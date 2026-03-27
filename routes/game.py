from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
import asyncio
import logging
import os
import uuid

log = logging.getLogger(__name__)

from models.schemas import MatchState, BOT_NAME, BOT_ALIAS
from services.news_fetcher import fetch_debate_prompt
from services.ai_judge import judge_debate
from components.layout import layout
from components.verdicts import verdict_component
from pages.landing import landing_page
from pages.category import category_page
from pages.arena   import waiting_page, arena_page, submitted_view, submit_status_fragment
from pages.room    import room_wait_page, join_room_page, team_slots_fragment, team_pick_page, room_list_fragment, ROOM_PAGE_SIZE
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
        """Legacy shortcut — now sends to preference lobby first."""
        return RedirectResponse("/join-room", status_code=303)

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
        match.category  = category

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

        # Already in this room — back to wait page
        if username in match.all_players():
            _alias = req.session.get("alias") or username
            return layout(
                room_wait_page(room_code, username, prompt=match.prompt,
                               team_size=match.team_size,
                               team1_aliases=match.team_aliases(1),
                               team2_aliases=match.team_aliases(2)),
                title="Custom Room | Akobato",
                user=username,
                alias=_alias,
            )

        if match.is_full():
            return RedirectResponse(f"/join-room?error=Room+{room_code}+is+full", status_code=303)
        if match.status != "waiting":
            return RedirectResponse(f"/join-room?error=Room+{room_code}+already+started", status_code=303)
        if username in game_state.player_matches:
            return RedirectResponse(f"/join-room?error=You+are+already+in+a+match", status_code=303)

        # For 1v1, skip the picker — only one spot available
        if match.team_size == 1:
            tokens = _fetch_tokens(username, game_state)
            if tokens <= 0:
                return RedirectResponse("/play?no_tokens=1", status_code=303)
            _deduct_token(username, game_state)
            user_alias = _lookup_alias(username, game_state)
            match.add_player_to_team(username, user_alias, 2)
            for p in match.all_players():
                game_state.player_matches[p] = mid
            # Go to wait page — WebSocket will redirect everyone into the game together
            _alias = req.session.get("alias") or username
            return layout(
                room_wait_page(room_code, username, prompt=match.prompt,
                               team_size=match.team_size,
                               team1_aliases=match.team_aliases(1),
                               team2_aliases=match.team_aliases(2)),
                title="Custom Room | Akobato",
                user=username,
                alias=_alias,
            )

        # Team match — show team picker
        my_alias = req.session.get("alias") or _lookup_alias(username, game_state)
        return layout(
            team_pick_page(
                room_code=room_code, username=username, my_alias=my_alias,
                prompt=match.prompt, team_size=match.team_size,
                team1_aliases=match.team_aliases(1),
                team2_aliases=match.team_aliases(2),
            ),
            title="Choose Team | Akobato",
            user=username,
            alias=my_alias,
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

    # ── Open room listing (HTMX fragment for JOIN panel) ─────────────────────

    @rt("/room/list")
    def get(page: int = 1):
        # Collect all rooms still in "waiting" status
        open_rooms = []
        for code, mid in list(game_state.rooms.items()):
            match = game_state.matches.get(mid)
            if not match or match.status != "waiting":
                continue
            open_rooms.append({
                "code":           code,
                "team_size":      match.team_size,
                "players_joined": len(match.all_players()),
                "players_total":  match.team_size * 2,
                "category":       getattr(match, "category", "random"),
            })

        total      = len(open_rooms)
        total_pages = max(1, (total + ROOM_PAGE_SIZE - 1) // ROOM_PAGE_SIZE)
        page        = max(1, min(page, total_pages))
        start       = (page - 1) * ROOM_PAGE_SIZE
        page_rooms  = open_rooms[start : start + ROOM_PAGE_SIZE]

        return room_list_fragment(page_rooms, page, total_pages)

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

        # Already in this room — back to wait page
        if username in match.all_players():
            return RedirectResponse(f"/game/{mid}?player={username}", status_code=303)

        if match.is_full():
            return RedirectResponse(f"/join-room?error=Room+{room_code}+is+full", status_code=303)
        if match.status != "waiting":
            return RedirectResponse(f"/join-room?error=Room+{room_code}+already+started", status_code=303)
        if username in game_state.player_matches:
            return RedirectResponse(f"/join-room?error=You+are+already+in+a+match", status_code=303)

        # For 1v1, auto-join — no team choice needed
        if match.team_size == 1:
            tokens = _fetch_tokens(username, game_state)
            if tokens <= 0:
                return RedirectResponse("/play?no_tokens=1", status_code=303)
            _deduct_token(username, game_state)
            user_alias = _lookup_alias(username, game_state)
            match.add_player_to_team(username, user_alias, 2)
            for p in match.all_players():
                game_state.player_matches[p] = mid
            # Go to wait page — WebSocket syncs everyone into the game together
            _alias = req.session.get("alias") or username
            return layout(
                room_wait_page(room_code, username, prompt=match.prompt,
                               team_size=match.team_size,
                               team1_aliases=match.team_aliases(1),
                               team2_aliases=match.team_aliases(2)),
                title="Custom Room | Akobato",
                user=username,
                alias=_alias,
            )

        # Team match — show team picker
        my_alias = req.session.get("alias") or _lookup_alias(username, game_state)
        return layout(
            team_pick_page(
                room_code=room_code, username=username, my_alias=my_alias,
                prompt=match.prompt, team_size=match.team_size,
                team1_aliases=match.team_aliases(1),
                team2_aliases=match.team_aliases(2),
            ),
            title="Choose Team | Akobato",
            user=username,
            alias=my_alias,
        )

    # ── Team picker — confirm and join ───────────────────────────────────────

    @rt("/room/pick-team", methods=["POST"])
    async def post(req: Request):
        username = req.session.get("username")
        if not username:
            return RedirectResponse("/login", status_code=303)

        form      = await req.form()
        room_code = (form.get("code")   or "").strip().upper()
        team_str  = (form.get("team")   or "").strip()

        try:
            chosen_team = int(team_str)
        except ValueError:
            return RedirectResponse(f"/join-room?error=Invalid+team+selection", status_code=303)

        mid   = game_state.rooms.get(room_code)
        match = game_state.matches.get(mid) if mid else None

        if not match:
            return RedirectResponse(f"/join-room?error=Room+{room_code}+not+found", status_code=303)
        if username in match.all_players():
            return RedirectResponse(f"/game/{mid}?player={username}", status_code=303)
        if not match.team_has_space(chosen_team):
            my_alias = req.session.get("alias") or _lookup_alias(username, game_state)
            return layout(
                team_pick_page(
                    room_code=room_code, username=username, my_alias=my_alias,
                    prompt=match.prompt, team_size=match.team_size,
                    team1_aliases=match.team_aliases(1),
                    team2_aliases=match.team_aliases(2),
                    error="That team is full — pick the other side.",
                ),
                title="Choose Team | Akobato",
                user=username,
                alias=my_alias,
            )
        if match.status != "waiting":
            return RedirectResponse(f"/join-room?error=Room+already+started", status_code=303)
        if username in game_state.player_matches:
            return RedirectResponse(f"/join-room?error=You+are+already+in+a+match", status_code=303)

        tokens = _fetch_tokens(username, game_state)
        if tokens <= 0:
            return RedirectResponse("/play?no_tokens=1", status_code=303)
        _deduct_token(username, game_state)

        user_alias = _lookup_alias(username, game_state)
        ok = match.add_player_to_team(username, user_alias, chosen_team)
        if not ok:
            my_alias = req.session.get("alias") or user_alias
            return layout(
                team_pick_page(
                    room_code=room_code, username=username, my_alias=my_alias,
                    prompt=match.prompt, team_size=match.team_size,
                    team1_aliases=match.team_aliases(1),
                    team2_aliases=match.team_aliases(2),
                    error="Could not join that team — please try again.",
                ),
                title="Choose Team | Akobato",
                user=username,
                alias=my_alias,
            )

        for p in match.all_players():
            game_state.player_matches[p] = mid

        # Always go to wait page — WebSocket redirects everyone into the game together
        _alias = req.session.get("alias") or username
        return layout(
            room_wait_page(room_code, username, prompt=match.prompt,
                           team_size=match.team_size,
                           team1_aliases=match.team_aliases(1),
                           team2_aliases=match.team_aliases(2)),
            title="Custom Room | Akobato",
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
        # If judging is in progress, show submitted view so they wait for verdict
        if match.status == "judging":
            submitted, total = match.submitted_count()
            return layout(
                submitted_view(player, match.match_id,
                               submitted=submitted, total=total, judging=True),
                title="Judging... | Akobato",
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
        return submit_status_fragment(match_id, player, submitted, total, judging)

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
        await asyncio.to_thread(_save_to_db, match, game_state)
        for p in match.all_players():
            game_state.player_matches.pop(p, None)
    except Exception as e:
        log.error("Judge failed for match %s: %s — resetting to active for retry", match.match_id, e)
        # Reset so the match can be re-judged on the next trigger
        match.status = "active"
    finally:
        _judging_in_progress.discard(match.match_id)


def _save_to_db(match: MatchState, game_state) -> None:
    """Synchronous DB save — always run via asyncio.to_thread so it doesn't block the loop."""
    db = game_state.db
    if not db:
        return

    v           = match.verdict
    all_players = match.all_players()

    # ── Normalise winner field ─────────────────────────────────────────────────
    # LLM occasionally returns legacy "Player 1"/"Player 2" — map back to team labels
    winner = v.winner
    if winner == "Player 1":
        winner = "Team A"
    elif winner == "Player 2":
        winner = "Team B"

    def outcome(player: str) -> str:
        if winner == "Tie":
            return "tie"
        team = match.player_team(player)   # 1 or 2
        return "win" if winner == match.team_label(team) else "loss"

    # ── Ensure every player row exists (insert defaults, ignore if already there) ──
    for p in all_players:
        try:
            db.table("players").insert({
                "username": p,
                "wins": 0, "losses": 0, "ties": 0, "score": 0, "tokens": 5,
            }).execute()
        except Exception:
            # Row already exists — that's fine, ignore the unique-constraint error
            pass

    # ── Increment stats per player ─────────────────────────────────────────────
    for p in all_players:
        result      = outcome(p)
        score_delta = 3 if result == "win" else 1 if result == "tie" else 0
        try:
            db.rpc("increment_player_stats", {
                "p_username": p,
                "p_wins":     1 if result == "win"  else 0,
                "p_losses":   1 if result == "loss" else 0,
                "p_ties":     1 if result == "tie"  else 0,
                "p_score":    score_delta,
            }).execute()
        except Exception as e:
            log.warning("increment_player_stats RPC failed for %s, falling back: %s", p, e)
            # Fallback: direct column increment
            try:
                existing = (
                    db.table("players")
                    .select("wins,losses,ties,score")
                    .eq("username", p)
                    .single()
                    .execute()
                )
                row = existing.data or {}
                db.table("players").update({
                    "wins":   (row.get("wins",   0) or 0) + (1 if result == "win"  else 0),
                    "losses": (row.get("losses", 0) or 0) + (1 if result == "loss" else 0),
                    "ties":   (row.get("ties",   0) or 0) + (1 if result == "tie"  else 0),
                    "score":  (row.get("score",  0) or 0) + score_delta,
                }).eq("username", p).execute()
            except Exception as e2:
                log.error("Direct stat update also failed for %s: %s", p, e2)

    # ── Save verdict record ────────────────────────────────────────────────────
    try:
        db.table("verdicts").insert({
            "match_id":      match.match_id,
            "prompt":        match.prompt,
            "player1":       match.player1,
            "player2":       match.player2,
            "argument1":     match.combined_arg(1),
            "argument2":     match.combined_arg(2),
            "winner":        winner,
            "reasoning":     v.reasoning,
            "winning_quote": v.winning_quote,
            "hp1_score":     v.human_originality_score_p1,
            "hp2_score":     v.human_originality_score_p2,
        }).execute()
    except Exception as e:
        log.error("Failed to insert verdict for match %s: %s", match.match_id, e)

    # ── Restore 1 token per player ─────────────────────────────────────────────
    for p in all_players:
        try:
            db.rpc("restore_player_token", {"p_username": p}).execute()
            _token_cache.delete(p)
        except Exception:
            # Fallback: increment tokens directly (cap at 5)
            try:
                existing = (
                    db.table("players")
                    .select("tokens")
                    .eq("username", p)
                    .single()
                    .execute()
                )
                cur = (existing.data or {}).get("tokens", 0) or 0
                db.table("players").update({
                    "tokens": min(5, cur + 1)
                }).eq("username", p).execute()
                _token_cache.delete(p)
            except Exception as e:
                log.warning("Token restore failed for %s: %s", p, e)


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
