from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
import os
import uuid

from models.schemas import MatchState
from services.news_fetcher import fetch_debate_prompt
from services.ai_judge import judge_debate
from components.layout import layout
from components.verdicts import verdict_component
from pages.landing import landing_page
from pages.category import category_page
from pages.arena import waiting_page, arena_page, submitted_view

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SW_JS    = os.path.join(_BASE_DIR, "static", "js", "sw.js")


def setup_game_routes(rt, game_state):

    # ── Service Worker (must be at root scope) ────────────────────────────────

    @rt("/sw.js")
    def get():
        return Response(
            open(_SW_JS).read(),
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
        )

    # ── Landing (public) ──────────────────────────────────────────────────────

    @rt("/")
    def get(req: Request):
        if req.session.get("username"):
            return RedirectResponse("/dashboard", status_code=303)
        return layout(
            landing_page(),
            title="Akobato — Real-Time 1v1 Debate Game",
            full_width=True,
            extra_css="/static/css/landing.css",
        )

    # ── Category picker ───────────────────────────────────────────────────────

    @rt("/play")
    def get(req: Request):
        username = req.session.get("username")
        if not username:
            return RedirectResponse("/login", status_code=303)
        tokens = _fetch_tokens(username, game_state)
        return layout(
            category_page(username, tokens),
            title="Pick a Category | Akobato",
            user=username,
            alias=req.session.get("alias"),
            tokens=tokens,
        )


    # ── Join / Matchmaking ────────────────────────────────────────────────────

    @rt("/join")
    async def get(req: Request, category: str = "random"):
        username = req.session.get("username")
        if not username:
            return RedirectResponse("/login", status_code=303)

        # Already in an active match → send back there
        if username in game_state.player_matches:
            mid = game_state.player_matches[username]
            return RedirectResponse(f"/game/{mid}?player={username}", status_code=303)

        # Check tokens before allowing entry
        tokens = _fetch_tokens(username, game_state)
        if tokens <= 0:
            return RedirectResponse("/play?no_tokens=1", status_code=303)

        # Deduct 1 token before entering any match
        _deduct_token(username, game_state)

        # Pair with a waiting player in the same category
        if game_state.waiting and game_state.waiting[0] != username:
            waiting_name, match_id = game_state.waiting
            match = game_state.matches.get(match_id)
            if match and match.status == "waiting":
                match.start(username)
                game_state.player_matches[username]     = match_id
                game_state.player_matches[waiting_name] = match_id
                game_state.waiting = None
                return RedirectResponse(
                    f"/game/{match_id}?player={username}", status_code=303
                )

        # Create a new match and wait
        match_id = str(uuid.uuid4())[:8]
        prompt   = await fetch_debate_prompt(category)
        match    = MatchState(match_id=match_id, prompt=prompt, player1=username)
        game_state.matches[match_id]        = match
        game_state.player_matches[username] = match_id
        game_state.waiting                  = (username, match_id)

        return RedirectResponse(f"/waiting/{username}", status_code=303)

    # ── Waiting room ──────────────────────────────────────────────────────────

    @rt("/waiting/{username}")
    def get(req: Request, username: str):
        return layout(
            waiting_page(username),
            title="Finding Opponent... | Akobato",
            user=username,
            alias=req.session.get("alias"),
        )

    @rt("/lobby/cancel/{username}", methods=["POST"])
    def post(username: str):
        mid = game_state.player_matches.get(username)
        if mid:
            # Clear waiting slot if this player is the one waiting
            if game_state.waiting and game_state.waiting[0] == username:
                game_state.waiting = None
            game_state.player_matches.pop(username, None)
            game_state.matches.pop(mid, None)
        return RedirectResponse("/play", status_code=303)

    @rt("/lobby/check/{username}")
    def get(username: str):
        mid   = game_state.player_matches.get(username)
        match = game_state.matches.get(mid) if mid else None

        if match and match.status != "waiting":
            return Script(f"window.location.href = '/game/{mid}?player={username}';")

        return Div(
            P("⏳ Still searching...", cls="status-waiting"),
            id="poll-area",
            hx_get=f"/lobby/check/{username}",
            hx_trigger="every 2s",
            hx_target="#poll-area",
            hx_swap="outerHTML",
        )

    # ── Game arena ────────────────────────────────────────────────────────────

    @rt("/game/{match_id}")
    def get(req: Request, match_id: str, player: str = ""):
        match = game_state.matches.get(match_id)
        _alias = req.session.get("alias")
        if not match:
            return layout(
                Div(H2("Match not found."), A("← Home", href="/dashboard")),
                user=player or None,
                alias=_alias,
            )
        if match.status == "waiting":
            return layout(
                Div(H2("Waiting for your opponent..."), cls="waiting-box"),
                user=player or None,
                alias=_alias,
            )
        return layout(
            arena_page(match, player),
            title="Arena | Akobato",
            user=player or None,
            alias=_alias,
        )

    # ── Submit argument ───────────────────────────────────────────────────────

    @rt("/game/{match_id}/submit", methods=["POST"])
    async def post(req: Request, match_id: str):
        form     = await req.form()
        player   = (form.get("player") or "").strip()
        argument = (form.get("argument") or "").strip()

        match = game_state.matches.get(match_id)
        if not match or match.status not in ("active", "judging"):
            return Div(P("Match not found or already over.", cls="status-waiting"), id="submit-area")

        match.submit(player, argument)
        _maybe_judge(match, game_state)

        if match.status == "complete" and match.verdict:
            return verdict_component(match, player)

        return submitted_view(player, match_id)

    # ── Status poll (HTMX) ────────────────────────────────────────────────────

    @rt("/game/{match_id}/status")
    def get(match_id: str, player: str = ""):
        match = game_state.matches.get(match_id)
        if not match:
            return Div(P("Match not found.", cls="status-waiting"), id="submit-area")

        if match.is_expired():
            match.submit(player, "")
            _maybe_judge(match, game_state)

        if match.status == "complete" and match.verdict:
            return verdict_component(match, player)

        return Div(
            Span("✅ Argument submitted!", cls="submitted-badge"),
            P("The AI Judge is deliberating...", cls="status-waiting", style="margin-top:.5rem"),
            id="submit-area",
            hx_get=f"/game/{match_id}/status?player={player}",
            hx_trigger="every 2s",
            hx_target="#submit-area",
            hx_swap="outerHTML",
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _maybe_judge(match: MatchState, game_state) -> None:
    if match.status != "judging":
        return
    verdict      = judge_debate(
        prompt=match.prompt,
        player1=match.player1,  arg1=match.argument1 or "",
        player2=match.player2 or "Player 2", arg2=match.argument2 or "",
    )
    match.verdict = verdict
    match.status  = "complete"
    _save_to_db(match, game_state)


def _save_to_db(match: MatchState, game_state) -> None:
    try:
        db = game_state.db
        if not db:
            return
        v = match.verdict

        for p in [match.player1, match.player2]:
            if not p:
                continue
            db.table("players").upsert({"username": p, "score": 0}, on_conflict="username").execute()

        def outcome(player):
            label = match.player_label(player)
            if v.winner == "Tie":
                return "tie"
            return "win" if v.winner == label else "loss"

        for p in [match.player1, match.player2]:
            if not p:
                continue
            result      = outcome(p)
            score_delta = 3 if result == "win" else 1 if result == "tie" else 0
            db.rpc("increment_player_stats", {
                "p_username": p,
                "p_wins":     1 if result == "win"  else 0,
                "p_losses":   1 if result == "loss" else 0,
                "p_ties":     1 if result == "tie"  else 0,
                "p_score":    score_delta,
            }).execute()

        db.table("verdicts").insert({
            "match_id":      match.match_id,
            "prompt":        match.prompt,
            "player1":       match.player1,
            "player2":       match.player2,
            "argument1":     match.argument1,
            "argument2":     match.argument2,
            "winner":        v.winner,
            "reasoning":     v.reasoning,
            "winning_quote": v.winning_quote,
            "hp1_score":     v.human_originality_score_p1,
            "hp2_score":     v.human_originality_score_p2,
        }).execute()

        # Restore 1 token per player after match completion (capped at 5)
        for p in [match.player1, match.player2]:
            if not p:
                continue
            try:
                db.rpc("restore_player_token", {"p_username": p}).execute()
            except Exception:
                pass
    except Exception:
        pass


def _fetch_tokens(username: str, game_state) -> int:
    try:
        db = game_state.db
        if not db:
            return 5
        result = (
            db.table("players")
            .select("tokens")
            .eq("username", username)
            .single()
            .execute()
        )
        val = (result.data or {}).get("tokens")
        return val if val is not None else 5
    except Exception:
        return 5


def _deduct_token(username: str, game_state) -> None:
    try:
        db = game_state.db
        if not db:
            return
        db.rpc("deduct_player_token", {"p_username": username}).execute()
    except Exception:
        pass
