from fasthtml.common import *
from starlette.requests import Request

from components.layout import layout
from pages.roast import roast_page


def setup_roast_routes(rt, game_state):

    @rt("/roast")
    def get(req: Request):
        username = req.session.get("username")
        _alias   = req.session.get("alias")
        tokens   = None

        if username:
            try:
                db = game_state.db
                if db:
                    row = db.table("players").select("tokens").eq("username", username).single().execute()
                    tokens = (row.data or {}).get("tokens")
            except Exception:
                pass

        best, worst = _fetch_best_and_worst(game_state)

        return layout(
            roast_page(best, worst),
            title="The Burn Board | Akobato",
            user=username,
            alias=_alias,
            tokens=tokens,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_best_and_worst(game_state) -> tuple[list[dict], list[dict]]:
    try:
        db = game_state.db
        if not db:
            return [], []

        result = (
            db.table("verdicts")
            .select("prompt, player1, player2, argument1, argument2, winner, reasoning, winning_quote, hp1_score, hp2_score")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )
        rows = result.data or []

        submissions = []
        for r in rows:
            if r.get("argument1") and r.get("hp1_score") is not None:
                submissions.append({
                    "argument":      r["argument1"],
                    "score":         r["hp1_score"],
                    "player":        r.get("player1") or "",
                    "prompt":        r.get("prompt") or "",
                    "reasoning":     r.get("reasoning") or "",
                    "winning_quote": r.get("winning_quote") or "",
                    "is_winner":     r.get("winner") == "Player 1",
                })
            if r.get("argument2") and r.get("hp2_score") is not None:
                submissions.append({
                    "argument":      r["argument2"],
                    "score":         r["hp2_score"],
                    "player":        r.get("player2") or "",
                    "prompt":        r.get("prompt") or "",
                    "reasoning":     r.get("reasoning") or "",
                    "winning_quote": r.get("winning_quote") or "",
                    "is_winner":     r.get("winner") == "Player 2",
                })

        if not submissions:
            return [], []

        # Resolve aliases in one batch query
        usernames  = list({s["player"] for s in submissions if s["player"]})
        alias_map  = _fetch_aliases(usernames, db)
        for s in submissions:
            s["alias"] = alias_map.get(s["player"]) or s["player"] or "Anonymous"

        best  = sorted(submissions, key=lambda x: x["score"], reverse=True)[:5]
        worst = sorted(submissions, key=lambda x: x["score"])[:5]
        return best, worst

    except Exception:
        return [], []


def _fetch_aliases(usernames: list[str], db) -> dict[str, str]:
    if not usernames:
        return {}
    try:
        result = (
            db.table("players")
            .select("username, alias")
            .in_("username", usernames)
            .execute()
        )
        return {
            r["username"]: r.get("alias") or r["username"]
            for r in (result.data or [])
        }
    except Exception:
        return {u: u for u in usernames}
