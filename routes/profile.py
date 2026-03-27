import hashlib
import re
from datetime import datetime, timezone, timedelta

from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from components.layout import layout
from pages.profile import profile_page, match_history_fragment
from services.avatar import generate_avatar_svg

# ── Alias generator ───────────────────────────────────────────────────────────

_ADJECTIVES = [
    "Silent", "Shadow", "Cyber", "Neon", "Ghost", "Iron", "Dark",
    "Void", "Storm", "Rogue", "Stealth", "Crimson", "Phantom", "Binary",
    "Toxic", "Hyper", "Null", "Apex", "Crypt", "Drift",
]
_NOUNS = [
    "Fox", "Wolf", "Hawk", "Viper", "Lynx", "Raven", "Blade",
    "Cipher", "Specter", "Wraith", "Cobra", "Glitch", "Vector",
    "Reaper", "Forge", "Nexus", "Byte", "Flux", "Signal", "Node",
]

_ALIAS_RE = re.compile(r"^[\w#\-]{2,24}$")


def generate_alias(username: str) -> str:
    """Deterministic — same username always yields same alias."""
    h = int(hashlib.sha256(username.lower().encode()).hexdigest(), 16)
    adj  = _ADJECTIVES[h % len(_ADJECTIVES)]
    noun = _NOUNS[(h >> 8) % len(_NOUNS)]
    num  = 1000 + (h >> 16) % 9000
    return f"{adj}{noun}#{num}"


# ── Route setup ───────────────────────────────────────────────────────────────

def setup_profile_routes(rt, game_state):

    @rt("/avatar/{username}")
    def get(username: str):
        svg = generate_avatar_svg(username)
        return Response(
            svg,
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    @rt("/profile")
    def get(req: Request, saved: str = "", error: str = ""):
        username = req.session.get("username")
        if not username:
            return RedirectResponse("/login", status_code=303)

        stats  = _fetch_profile(username, game_state)
        # DB alias → session cache → deterministic fallback
        alias  = stats.get("alias") or req.session.get("alias") or _ensure_alias(username, game_state)
        req.session["alias"] = alias  # always keep session in sync
        tokens = stats.get("tokens", 5)

        return layout(
            profile_page(username, alias, stats, saved=bool(saved), error=error),
            title="Profile | Akobato",
            user=username,
            alias=alias,
            tokens=tokens,
        )

    @rt("/profile/matches")
    def get(req: Request, filter: str = "recent"):
        username = req.session.get("username")
        if not username:
            return Div("Not logged in", style="color:var(--brand-muted); font-size:.82rem; padding:1rem;")
        rows = _fetch_match_history(username, filter, game_state)
        return match_history_fragment(rows, username, filter)

    @rt("/profile/update-alias", methods=["POST"])
    async def post(req: Request):
        username = req.session.get("username")
        if not username:
            return RedirectResponse("/login", status_code=303)

        form  = await req.form()
        alias = (form.get("alias") or "").strip()

        if not alias or not _ALIAS_RE.match(alias):
            return RedirectResponse("/profile?error=invalid", status_code=303)

        ok = _save_alias(username, alias, game_state)
        if ok:
            # Cache alias in session so UI reflects the change immediately
            req.session["alias"] = alias
            return RedirectResponse("/profile?saved=1", status_code=303)
        else:
            return RedirectResponse("/profile?error=db", status_code=303)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_profile(username: str, game_state) -> dict:
    default = {"score": 0, "wins": 0, "losses": 0, "ties": 0, "tokens": 5, "alias": None}
    try:
        db = game_state.db
        if not db:
            return default
        result = (
            db.table("players")
            .select("score, wins, losses, ties, tokens, alias")
            .eq("username", username)
            .single()
            .execute()
        )
        data = result.data or default
        for k, v in default.items():
            if k not in data or data[k] is None and k != "alias":
                data[k] = v
        return data
    except Exception:
        return default


def _ensure_alias(username: str, game_state) -> str:
    """Generate and persist an alias if the player has none."""
    alias = generate_alias(username)
    try:
        db = game_state.db
        if db:
            db.table("players").update({"alias": alias}).eq("username", username).execute()
    except Exception:
        pass
    return alias


def _fetch_match_history(username: str, filter_name: str, game_state) -> list:
    try:
        db = game_state.db
        if not db:
            return []
        query = (
            db.table("verdicts")
            .select("match_id, prompt, player1, player2, winner, hp1_score, hp2_score, created_at")
            .or_(f"player1.eq.{username},player2.eq.{username}")
            .order("created_at", desc=True)
        )
        if filter_name == "weekly":
            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            query = query.gte("created_at", week_ago).limit(50)
        elif filter_name == "recent":
            query = query.limit(10)
        else:
            query = query.limit(50)

        rows = query.execute().data or []

        if rows:
            opp_names = {
                (r["player2"] if r["player1"] == username else r["player1"])
                for r in rows
            }
            alias_data = (
                db.table("players")
                .select("username, alias")
                .in_("username", list(opp_names))
                .execute()
                .data or []
            )
            alias_map = {a["username"]: a["alias"] for a in alias_data if a.get("alias")}
            for r in rows:
                opp = r["player2"] if r["player1"] == username else r["player1"]
                r["opp_alias"] = alias_map.get(opp, opp)

        return rows
    except Exception as e:
        print(f"[match history] {e}")
        return []


def _save_alias(username: str, alias: str, game_state) -> bool:
    try:
        db = game_state.db
        if not db:
            return False
        db.table("players").update({"alias": alias}).eq("username", username).execute()
        return True
    except Exception as e:
        print(f"[alias save error] {e}")
        return False
