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
            # ── Page header ──────────────────────────────────────────────
            Div(
                H2("🏆 Hall of Fame", cls="lb-title"),
                P("Top fighters ranked by score. Aliases only — identities stay hidden.",
                  cls="lb-subtitle"),
                cls="lb-header",
            ),
            # ── Table ────────────────────────────────────────────────────
            Div(
                Table(
                    Thead(
                        Tr(
                            Th("#",       cls="lb-th lb-th--rank"),
                            Th("Fighter", cls="lb-th lb-th--name"),
                            Th("W",       cls="lb-th lb-th--stat"),
                            Th("L",       cls="lb-th lb-th--stat"),
                            Th("T",       cls="lb-th lb-th--stat"),
                            Th("Score",   cls="lb-th lb-th--score"),
                        )
                    ),
                    Tbody(*[leaderboard_row(i + 1, r) for i, r in enumerate(rows)]),
                    cls="leaderboard-table",
                ),
                cls="lb-table-wrap",
            ),
            cls="card lb-card",
        )

        return layout(
            table,
            A("⚔️ Enter the Arena", href="/dashboard" if username else "/login",
              cls="play-again-btn", style="display:block; text-align:center; margin-top:1.5rem;"),
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
        # Show alias in leaderboard instead of real username — never expose real username
        for r in rows:
            r["username"] = r.get("alias") or "Fighter"
        return rows
    except Exception:
        return []
