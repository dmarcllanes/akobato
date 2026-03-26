from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
import os
import uuid

from models.schemas import MatchState, BOT_NAME, BOT_ALIAS
from services.news_fetcher import fetch_debate_prompt
from services.ai_judge import judge_debate, generate_bot_argument
from components.layout import layout
from components.verdicts import verdict_component
from pages.landing import landing_page
from pages.category import category_page
from pages.arena   import waiting_page, arena_page, submitted_view
from pages.room    import room_wait_page, join_room_page
from routes.profile import generate_alias

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
    async def get(req: Request, category: str = "random", mode: str = "versus"):
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

        match_id = str(uuid.uuid4())[:8]
        prompt   = await fetch_debate_prompt(category)

        # ── Solo mode: instant start vs AI bot ────────────────────────────────
        if mode == "solo":
            match = MatchState(match_id=match_id, prompt=prompt, player1=username, mode="solo")
            match.alias1 = _lookup_alias(username, game_state)
            match.alias2 = BOT_ALIAS
            match.start(BOT_NAME)
            game_state.matches[match_id]        = match
            game_state.player_matches[username] = match_id
            return RedirectResponse(f"/game/{match_id}?player={username}", status_code=303)

        # ── Versus mode: pair with a waiting player ────────────────────────────
        if game_state.waiting and game_state.waiting[0] != username:
            waiting_name, waiting_mid = game_state.waiting
            waiting_match = game_state.matches.get(waiting_mid)
            if waiting_match and waiting_match.status == "waiting":
                waiting_match.start(username)
                waiting_match.alias2 = _lookup_alias(username, game_state)
                game_state.player_matches[username]     = waiting_mid
                game_state.player_matches[waiting_name] = waiting_mid
                game_state.waiting = None
                return RedirectResponse(
                    f"/game/{waiting_mid}?player={username}", status_code=303
                )

        # No one waiting — create match and wait
        match = MatchState(match_id=match_id, prompt=prompt, player1=username, mode="versus")
        match.alias1 = _lookup_alias(username, game_state)
        game_state.matches[match_id]        = match
        game_state.player_matches[username] = match_id
        game_state.waiting                  = (username, match_id)

        return RedirectResponse(f"/waiting/{username}", status_code=303)

    # ── Waiting room ──────────────────────────────────────────────────────────

    @rt("/waiting/{username}")
    def get(req: Request, username: str):
        my_alias = req.session.get("alias") or _lookup_alias(username, game_state)
        return layout(
            waiting_page(my_alias, username),
            title="Finding Opponent... | Akobato",
            user=username,
            alias=my_alias,
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

        return Span(
            id="poll-area",
            hx_get=f"/lobby/check/{username}",
            hx_trigger="every 500ms",
            hx_target="#poll-area",
            hx_swap="outerHTML",
        )

    # ── Private room — create ─────────────────────────────────────────────────

    @rt("/room/create")
    async def get(req: Request, category: str = "random"):
        username = req.session.get("username")
        if not username:
            return RedirectResponse("/login", status_code=303)

        if username in game_state.player_matches:
            mid = game_state.player_matches[username]
            return RedirectResponse(f"/game/{mid}?player={username}", status_code=303)

        tokens = _fetch_tokens(username, game_state)
        if tokens <= 0:
            return RedirectResponse("/play?no_tokens=1", status_code=303)

        _deduct_token(username, game_state)

        room_code = _generate_room_code(game_state)
        match_id  = str(uuid.uuid4())[:8]
        prompt    = await fetch_debate_prompt(category)
        match     = MatchState(match_id=match_id, prompt=prompt, player1=username, mode="private")
        match.alias1    = _lookup_alias(username, game_state)
        match.room_code = room_code

        game_state.matches[match_id]        = match
        game_state.player_matches[username] = match_id
        game_state.rooms[room_code]         = match_id

        _alias = req.session.get("alias") or username
        return layout(
            room_wait_page(room_code, username),
            title="Private Room | Akobato",
            user=username,
            alias=_alias,
        )

    # ── Private room — poll (host waiting) ────────────────────────────────────

    @rt("/room/check/{room_code}")
    def get(room_code: str, player: str = ""):
        mid   = game_state.rooms.get(room_code)
        match = game_state.matches.get(mid) if mid else None
        if match and match.status != "waiting":
            return Script(f"window.location.href = '/game/{mid}?player={player}';")
        return Span(
            id="poll-area",
            hx_get=f"/room/check/{room_code}?player={player}",
            hx_trigger="every 500ms",
            hx_target="#poll-area",
            hx_swap="outerHTML",
        )

    # ── Private room — cancel (host leaves) ───────────────────────────────────

    @rt("/room/cancel/{room_code}", methods=["POST"])
    def post(room_code: str, player: str = ""):
        mid = game_state.rooms.pop(room_code, None)
        if mid:
            game_state.matches.pop(mid, None)
        game_state.player_matches.pop(player, None)
        return RedirectResponse("/play", status_code=303)

    # ── Private room — join page ───────────────────────────────────────────────

    @rt("/join-room")
    def get(req: Request, error: str = ""):
        username = req.session.get("username")
        if not username:
            return RedirectResponse("/login", status_code=303)
        _alias = req.session.get("alias")
        return layout(
            join_room_page(error=error),
            title="Join Room | Akobato",
            user=username,
            alias=_alias,
        )

    # ── Private room — enter by code ──────────────────────────────────────────

    @rt("/room/enter", methods=["POST"])
    async def post(req: Request):
        username = req.session.get("username")
        if not username:
            return RedirectResponse("/login", status_code=303)

        form      = await req.form()
        room_code = (form.get("code") or "").strip().upper()

        mid   = game_state.rooms.get(room_code)
        match = game_state.matches.get(mid) if mid else None

        if not match:
            return RedirectResponse(f"/join-room?error=Room+{room_code}+not+found", status_code=303)
        if match.status != "waiting":
            return RedirectResponse(f"/join-room?error=Room+{room_code}+already+started", status_code=303)
        if match.player1 == username:
            return RedirectResponse(f"/join-room?error=You+cannot+join+your+own+room", status_code=303)

        if username in game_state.player_matches:
            return RedirectResponse(f"/join-room?error=You+are+already+in+a+match", status_code=303)

        tokens = _fetch_tokens(username, game_state)
        if tokens <= 0:
            return RedirectResponse("/play?no_tokens=1", status_code=303)
        _deduct_token(username, game_state)

        match.start(username)
        match.alias2 = _lookup_alias(username, game_state)
        game_state.player_matches[username]      = mid
        game_state.player_matches[match.player1] = mid

        return RedirectResponse(f"/game/{mid}?player={username}", status_code=303)

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
            # Private room: show room-code waiting screen
            if match.room_code:
                return layout(
                    room_wait_page(match.room_code, player),
                    title="Private Room | Akobato",
                    user=player or None,
                    alias=_alias,
                )
            # Versus: show lobby animation
            my_alias = _alias or _lookup_alias(player, game_state)
            return layout(
                waiting_page(my_alias, player),
                title="Finding Opponent... | Akobato",
                user=player or None,
                alias=_alias,
            )
        # Show verdict directly if match is already complete
        if match.status == "complete" and match.verdict:
            return layout(
                verdict_component(match, player),
                title="Result | Akobato",
                user=player or None,
                alias=_alias,
            )
        my_alias = _alias or match.alias_of(player) or _lookup_alias(player, game_state)
        return layout(
            arena_page(match, player, my_alias),
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
        await _maybe_judge(match, game_state)

        if match.status == "complete" and match.verdict:
            return verdict_component(match, player)

        return submitted_view(player, match_id)

    # ── Status poll (HTMX) ────────────────────────────────────────────────────

    @rt("/game/{match_id}/status")
    async def get(match_id: str, player: str = ""):
        match = game_state.matches.get(match_id)
        if not match:
            return Div(P("Match not found.", cls="status-waiting"), id="submit-area")

        if match.is_expired():
            match.submit(player, "")
            await _maybe_judge(match, game_state)

        if match.status == "complete" and match.verdict:
            return verdict_component(match, player)

        return Div(
            Span("✅ Argument submitted!", cls="submitted-badge"),
            P(
                Span(cls="judge-spinner"),
                "The AI Judge is deliberating...",
                cls="status-waiting",
                style="margin-top:.5rem",
            ),
            id="submit-area",
            hx_get=f"/game/{match_id}/status?player={player}",
            hx_trigger="every 500ms",
            hx_target="#submit-area",
            hx_swap="outerHTML",
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

# Guard against concurrent judging calls for the same match
_judging_in_progress: set = set()


async def _maybe_judge(match: MatchState, game_state) -> None:
    # Solo mode: generate bot counter-argument first
    if match.mode == "solo" and match.argument1 and match.argument2 is None:
        match.argument2 = await generate_bot_argument(match.prompt, match.argument1)
        match.status = "judging"

    if match.status != "judging":
        return

    # Prevent duplicate judging calls for the same match
    if match.match_id in _judging_in_progress:
        return
    _judging_in_progress.add(match.match_id)

    try:
        verdict = await judge_debate(
            prompt=match.prompt,
            player1=match.player1,  arg1=match.argument1 or "",
            player2=match.player2 or "Player 2", arg2=match.argument2 or "",
        )
        match.verdict = verdict
        match.status  = "complete"
        _save_to_db(match, game_state)
        # Free both players so they can join a new match
        for p in [match.player1, match.player2]:
            if p:
                game_state.player_matches.pop(p, None)
    finally:
        _judging_in_progress.discard(match.match_id)


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


def _generate_room_code(game_state) -> str:
    import random
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no confusable 0/O/1/I/L
    for _ in range(20):
        code = "".join(random.choices(chars, k=6))
        if code not in game_state.rooms:
            return code
    return "".join(random.choices(chars, k=8))  # fallback longer code


def _lookup_alias(username: str, game_state) -> str:
    """Always returns a public alias — never the real username."""
    try:
        db = game_state.db
        if not db:
            return generate_alias(username)
        result = (
            db.table("players")
            .select("alias")
            .eq("username", username)
            .single()
            .execute()
        )
        alias = (result.data or {}).get("alias")
        if alias:
            return alias
        # No alias saved yet — generate, persist, and return it
        alias = generate_alias(username)
        try:
            db.table("players").update({"alias": alias}).eq("username", username).execute()
        except Exception:
            pass
        return alias
    except Exception:
        return generate_alias(username)


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
