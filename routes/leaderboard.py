from fasthtml.common import *
from starlette.requests import Request

from components.layout import layout
from components.verdicts import leaderboard_row


def setup_leaderboard_routes(rt, game_state):

    @rt("/leaderboard")
    def get(req: Request):
        username = req.session.get("username")
        rows     = _fetch_leaderboard(game_state)

        _alias = req.session.get("alias")

        if not rows:
            content = Div(
                H2("🏆 Hall of Fame"),
                P("No debates recorded yet. Be the first to fight!", style="color:var(--brand-muted); text-align:center;"),
                A("⚔️ Enter the Arena", href="/dashboard" if username else "/login", cls="play-again-btn"),
                cls="card text-center",
                style="padding: 3rem;",
            )
            return layout(content, title="Hall of Fame | Akobato", user=username, alias=_alias)

        table = Div(
            Table(
                Thead(Tr(Th("Rank"), Th("Fighter"), Th("Wins"), Th("Losses"), Th("Ties"), Th("Score"))),
                Tbody(*[leaderboard_row(i + 1, r) for i, r in enumerate(rows)]),
                cls="leaderboard-table",
            ),
            cls="card",
        )

        return layout(
            H2("🏆 Hall of Fame", style="text-align:center; margin-bottom:1.5rem;"),
            table,
            A("⚔️ Enter the Arena", href="/dashboard" if username else "/login", cls="play-again-btn"),
            title="Hall of Fame | Akobato",
            user=username,
            alias=_alias,
        )


def _fetch_leaderboard(game_state) -> list[dict]:
    try:
        db = game_state.db
        if not db:
            return []
        result = (
            db.table("players")
            .select("username, alias, score, wins, losses, ties")
            .order("score", desc=True)
            .limit(20)
            .execute()
        )
        rows = result.data or []
        # Show alias in leaderboard instead of real username
        for r in rows:
            r["username"] = r.get("alias") or r["username"]
        return rows
    except Exception:
        return []
