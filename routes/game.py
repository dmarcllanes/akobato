from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
import os
import uuid

from models.schemas import MatchState, BOT_NAME, BOT_ALIAS
from services.news_fetcher import fetch_debate_prompt
from services.ai_judge import judge_debate
from components.layout import layout
from components.verdicts import verdict_component
from pages.landing import landing_page
from pages.category import category_page
from pages.arena   import waiting_page, arena_page, submitted_view
from pages.room    import room_wait_page, join_room_page, team_slots_fragment
from routes.profile import generate_alias
from services.cache import TTLCache

_alias_cache  = TTLCache(ttl=300)   # 5 min — alias rarely changes
_token_cache  = TTLCache(ttl=20)    # 20 s  — tokens change per match

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

    # ── Quick room (one-click from dashboard) ────────────────────────────────

    @rt("/quick-room")
    async def get(req: Request):
        """Create a private room instantly with a random topic."""
        return RedirectResponse("/room/create?category=random", status_code=303)

    # ── Private room — create ─────────────────────────────────────────────────

    @rt("/room/create")
    async def get(req: Request, category: str = "random", team_size: int = 1):
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
        match     = MatchState(match_id=match_id, prompt=prompt, player1=username,
                               mode="private", team_size=team_size)
        match.alias1    = _lookup_alias(username, game_state)
        match.room_code = room_code

        game_state.matches[match_id]        = match
        game_state.player_matches[username] = match_id
        game_state.rooms[room_code]         = match_id

        _alias = req.session.get("alias") or username
        return layout(
            room_wait_page(room_code, username, prompt=prompt,
                           team_size=match.team_size,
                           team1_aliases=match.team_aliases(1),
                           team2_aliases=match.team_aliases(2)),
            title="Private Room | Akobato",
            user=username,
            alias=_alias,
        )

    # ── Friend join via shareable link ────────────────────────────────────────

    @rt("/r/{code}")
    async def get(req: Request, code: str):
        """Direct join link — friend clicks this, gets taken straight into the room."""
        username = req.session.get("username")
        if not username:
            req.session["after_login"] = f"/r/{code.upper()}"
            return RedirectResponse("/login", status_code=303)

        room_code = code.upper()
        mid   = game_state.rooms.get(room_code)
        match = game_state.matches.get(mid) if mid else None

        if not match:
            return RedirectResponse(f"/join-room?error=Room+{room_code}+not+found", status_code=303)

        # Already in this room — show wait page (team match may need more players)
        if username in match.all_players():
            _alias = req.session.get("alias") or username
            return layout(
                room_wait_page(room_code, username, prompt=match.prompt,
                               team_size=match.team_size,
                               team1_aliases=match.team_aliases(1),
                               team2_aliases=match.team_aliases(2)),
                title="Private Room | Akobato",
                user=username,
                alias=_alias,
            )

        if match.is_full():
            return RedirectResponse(f"/join-room?error=Room+{room_code}+is+full", status_code=303)
        if match.status != "waiting":
            return RedirectResponse(f"/join-room?error=Room+{room_code}+already+started", status_code=303)
        if username in game_state.player_matches:
            return RedirectResponse(f"/join-room?error=You+are+already+in+a+match", status_code=303)

        tokens = _fetch_tokens(username, game_state)
        if tokens <= 0:
            return RedirectResponse("/play?no_tokens=1", status_code=303)
        _deduct_token(username, game_state)

        user_alias = _lookup_alias(username, game_state)
        team_num   = match.add_player(username, user_alias)
        if team_num is None:
            return RedirectResponse(f"/join-room?error=Room+{room_code}+is+full", status_code=303)

        # Track all current room members
        for p in match.all_players():
            game_state.player_matches[p] = mid

        # If room is now full, redirect this last joiner straight to the game
        if match.is_full():
            return RedirectResponse(f"/game/{mid}?player={username}", status_code=303)

        # Room still needs more players — show wait page
        _alias = req.session.get("alias") or username
        return layout(
            room_wait_page(room_code, username, prompt=match.prompt,
                           team_size=match.team_size,
                           team1_aliases=match.team_aliases(1),
                           team2_aliases=match.team_aliases(2)),
            title="Private Room | Akobato",
            user=username,
            alias=_alias,
        )

    # ── Private room — live team slots (HTMX fragment) ────────────────────────

    @rt("/room/teams/{room_code}")
    def get(room_code: str):
        mid   = game_state.rooms.get(room_code)
        match = game_state.matches.get(mid) if mid else None
        if not match:
            return Div("Room expired", id="wt-team-slots")
        return team_slots_fragment(
            room_code,
            match.team_size,
            match.team_aliases(1),
            match.team_aliases(2),
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

        # Already in this room — redirect to game/wait page
        if username in match.all_players():
            return RedirectResponse(f"/game/{mid}?player={username}", status_code=303)

        if match.is_full():
            return RedirectResponse(f"/join-room?error=Room+{room_code}+is+full", status_code=303)
        if match.status != "waiting":
            return RedirectResponse(f"/join-room?error=Room+{room_code}+already+started", status_code=303)
        if username in game_state.player_matches:
            return RedirectResponse(f"/join-room?error=You+are+already+in+a+match", status_code=303)

        tokens = _fetch_tokens(username, game_state)
        if tokens <= 0:
            return RedirectResponse("/play?no_tokens=1", status_code=303)
        _deduct_token(username, game_state)

        user_alias = _lookup_alias(username, game_state)
        team_num   = match.add_player(username, user_alias)
        if team_num is None:
            return RedirectResponse(f"/join-room?error=Room+{room_code}+is+full", status_code=303)

        for p in match.all_players():
            game_state.player_matches[p] = mid

        if match.is_full():
            return RedirectResponse(f"/game/{mid}?player={username}", status_code=303)

        # Room still needs more players
        _alias = req.session.get("alias") or username
        return layout(
            room_wait_page(room_code, username, prompt=match.prompt,
                           team_size=match.team_size,
                           team1_aliases=match.team_aliases(1),
                           team2_aliases=match.team_aliases(2)),
            title="Private Room | Akobato",
            user=username,
            alias=_alias,
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
            # Private room: show room-code waiting screen
            if match.room_code:
                return layout(
                    room_wait_page(match.room_code, player, prompt=match.prompt,
                                   team_size=match.team_size,
                                   team1_aliases=match.team_aliases(1),
                                   team2_aliases=match.team_aliases(2)),
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

        submitted, total = match.submitted_count()
        return submitted_view(player, match_id,
                              submitted=submitted, total=total,
                              judging=(match.status == "judging"))

    # ── Submission progress poll (HTMX — replaces only the status inner div) ──

    @rt("/game/{match_id}/submit-count")
    async def get(match_id: str, player: str = ""):
        match = game_state.matches.get(match_id)
        if not match:
            return Div(P("Match ended.", cls="status-waiting"), id="submit-status")

        if match.is_expired():
            match.auto_submit_expired()
            await _maybe_judge(match, game_state)

        if match.status == "complete" and match.verdict:
            # Verdict is in — redirect via JS (WS should have already done this)
            return Div(
                Script(f"window.location.href='/game/{match_id}?player={player}';"),
                id="submit-status",
            )

        submitted, total = match.submitted_count()
        judging = match.status == "judging"

        if judging or submitted >= total:
            inner = P(Span(cls="judge-spinner"), " The AI Judge is deliberating...",
                      cls="status-waiting")
        else:
            remaining = total - submitted
            inner = P(
                Span(cls="judge-spinner"),
                f" Waiting for {remaining} more player{'s' if remaining != 1 else ''} to submit…"
                f"  ({submitted}/{total} done)",
                cls="status-waiting",
            )

        return Div(
            inner,
            id="submit-status",
            hx_get=f"/game/{match_id}/submit-count?player={player}",
            hx_trigger="every 1500ms",
            hx_target="#submit-status",
            hx_swap="outerHTML",
        )

    # ── Status poll (HTMX fallback) ───────────────────────────────────────────

    @rt("/game/{match_id}/status")
    async def get(match_id: str, player: str = ""):
        match = game_state.matches.get(match_id)
        if not match:
            return Div(P("Match not found.", cls="status-waiting"), id="submit-area")

        if match.is_expired():
            match.auto_submit_expired()
            await _maybe_judge(match, game_state)

        if match.status == "complete" and match.verdict:
            return verdict_component(match, player)

        submitted, total = match.submitted_count()
        return Div(
            Span("✅ Argument submitted!", cls="submitted-badge"),
            P(
                Span(cls="judge-spinner"),
                " The AI Judge is deliberating..." if match.status == "judging"
                else f" Waiting for {total - submitted} more player(s)…  ({submitted}/{total} done)",
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
    if match.status != "judging":
        return

    if match.match_id in _judging_in_progress:
        return
    _judging_in_progress.add(match.match_id)

    try:
        verdict = await judge_debate(
            prompt=match.prompt,
            player1=match.team_label(1), arg1=match.combined_arg(1),
            player2=match.team_label(2), arg2=match.combined_arg(2),
        )
        match.verdict = verdict
        match.status  = "complete"
        _save_to_db(match, game_state)
        for p in match.all_players():
            game_state.player_matches.pop(p, None)
    finally:
        _judging_in_progress.discard(match.match_id)


def _save_to_db(match: MatchState, game_state) -> None:
    try:
        db = game_state.db
        if not db:
            return
        v = match.verdict
        all_players = match.all_players()

        for p in all_players:
            db.table("players").upsert({"username": p, "score": 0}, on_conflict="username").execute()

        def outcome(player):
            if v.winner == "Tie":
                return "tie"
            player_team = match.player_team(player)  # 1 or 2
            return "win" if v.winner == match.team_label(player_team) else "loss"

        for p in all_players:
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
            "argument1":     match.combined_arg(1),
            "argument2":     match.combined_arg(2),
            "winner":        v.winner,
            "reasoning":     v.reasoning,
            "winning_quote": v.winning_quote,
            "hp1_score":     v.human_originality_score_p1,
            "hp2_score":     v.human_originality_score_p2,
        }).execute()

        # Restore 1 token per player after match completion
        for p in all_players:
            try:
                db.rpc("restore_player_token", {"p_username": p}).execute()
                _token_cache.delete(p)
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
    """Always returns a public alias — never the real username. Cached for 5 min."""
    cached = _alias_cache.get(username)
    if cached is not None:
        return cached
    try:
        db = game_state.db
        if not db:
            alias = generate_alias(username)
            _alias_cache.set(username, alias)
            return alias
        result = (
            db.table("players")
            .select("alias")
            .eq("username", username)
            .single()
            .execute()
        )
        alias = (result.data or {}).get("alias")
        if not alias:
            alias = generate_alias(username)
            try:
                db.table("players").update({"alias": alias}).eq("username", username).execute()
            except Exception:
                pass
        _alias_cache.set(username, alias)
        return alias
    except Exception:
        alias = generate_alias(username)
        _alias_cache.set(username, alias)
        return alias


def _fetch_tokens(username: str, game_state) -> int:
    cached = _token_cache.get(username)
    if cached is not None:
        return cached
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
        tokens = val if val is not None else 5
        _token_cache.set(username, tokens)
        return tokens
    except Exception:
        return 5


def _deduct_token(username: str, game_state) -> None:
    _token_cache.delete(username)   # invalidate so next read hits DB
    try:
        db = game_state.db
        if not db:
            return
        db.rpc("deduct_player_token", {"p_username": username}).execute()
    except Exception:
        pass
