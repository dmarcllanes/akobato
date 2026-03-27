from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse

from components.layout import layout
from pages.login import login_page
from pages.dashboard import dashboard_page


def setup_dashboard_routes(rt, game_state):

    # ── Login page ────────────────────────────────────────────────────────────

    @rt("/login")
    def get(req: Request, error: str = ""):
        if req.session.get("username"):
            return RedirectResponse("/dashboard", status_code=303)
        return (
            Title("Sign In | Akobato"),
            Link(rel="icon", href="/static/img/favicon.svg", type="image/svg+xml"),
            Link(rel="manifest", href="/static/manifest.json"),
            Meta(name="theme-color", content="#05D9E8"),
            Style("body{background:#050514!important;margin:0;font-family:'Share Tech Mono',monospace;}"),
            Link(rel="stylesheet", href="/static/css/custom.css"),
            Link(rel="stylesheet",
                 href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap"),
            login_page(error=error),
        )

    # ── Dashboard ─────────────────────────────────────────────────────────────

    @rt("/dashboard")
    def get(req: Request):
        username = req.session.get("username")
        if not username:
            return RedirectResponse("/login", status_code=303)

        stats       = _fetch_stats(username, game_state)
        top_players = _fetch_top_players(game_state)
        tokens      = stats.get("tokens", 5)
        alias = stats.get("alias") or req.session.get("alias") or username
        # Cache alias in session for nav display across all pages
        if alias and alias != username:
            req.session["alias"] = alias

        return layout(
            dashboard_page(username, stats, top_players, alias=alias),
            title="Dashboard | Akobato",
            user=username,
            alias=alias,
            tokens=tokens,
        )


def _fetch_stats(username: str, game_state) -> dict:
    default = {"score": 0, "wins": 0, "losses": 0, "ties": 0, "tokens": 5, "alias": None}
    try:
        db = game_state.db
        if not db:
            return default
        result = (
            db.table("players")
            .select("score, wins, losses, ties, tokens")
            .eq("username", username)
            .single()
            .execute()
        )
        data = result.data or {}
        if not data:
            return default
        if "tokens" not in data or data["tokens"] is None:
            data["tokens"] = 5
        data["alias"] = _fetch_alias(username, db)
        return data
    except Exception:
        return default


def _fetch_alias(username: str, db) -> str | None:
    try:
        result = (
            db.table("players")
            .select("alias")
            .eq("username", username)
            .single()
            .execute()
        )
        return (result.data or {}).get("alias")
    except Exception:
        return None


def _fetch_top_players(game_state) -> list:
    try:
        db = game_state.db
        if not db:
            return []
        result = (
            db.table("players")
            .select("username, alias, score, wins, losses, ties")
            .order("score", desc=True)
            .limit(5)
            .execute()
        )
        rows = result.data or []
        for r in rows:
            r["username"] = r.get("alias") or r.get("username") or "Fighter"
        return rows
    except Exception:
        return []
