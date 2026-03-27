from fasthtml.common import *

_CAT_ICONS = {
    "random": "🎲", "world": "🌍", "technology": "💻",
    "politics": "🏛️", "sports": "⚽", "entertainment": "🎬",
    "science": "🔬", "business": "💰", "gaming": "🎮",
}
_CAT_NAMES = {
    "random": "SURPRISE ME", "world": "WORLD NEWS", "technology": "TECHNOLOGY",
    "politics": "POLITICS", "sports": "SPORTS", "entertainment": "ENTERTAINMENT",
    "science": "SCIENCE", "business": "BUSINESS", "gaming": "GAMING",
}

ROOM_PAGE_SIZE = 6


def room_list_fragment(rooms_data: list, page: int, total_pages: int) -> FT:
    """HTMX-refreshable paginated list of open rooms for the JOIN panel."""

    def _room_card(r: dict) -> FT:
        ts       = r["team_size"]
        joined   = r["players_joined"]
        total    = r["players_total"]
        cat      = r.get("category", "random")
        icon     = _CAT_ICONS.get(cat, "🎲")
        cat_name = _CAT_NAMES.get(cat, cat.upper())
        size_lbl = f"{ts}v{ts}"
        spots    = total - joined
        full_cls = " rl-card--full" if spots == 0 else ""
        spots_lbl = "FULL" if spots == 0 else f"{spots} spot{'s' if spots != 1 else ''} open"
        spots_color = "var(--brand-muted)" if spots == 0 else "#3fb950"

        return Div(
            Span(icon, cls="rl-cat-icon"),
            Div(
                Div(cat_name, cls="rl-cat-name"),
                Div(
                    Span(size_lbl, cls="rl-badge rl-badge--size"),
                    Span(f"{joined}/{total} players", cls="rl-badge rl-badge--players"),
                    cls="rl-badges",
                ),
                cls="rl-card-meta",
            ),
            Span(
                spots_lbl,
                style=f"font-size:.68rem; font-weight:700; color:{spots_color}; white-space:nowrap; flex-shrink:0;",
            ),
            cls=f"rl-card{full_cls}",
        )

    # Empty state
    if not rooms_data:
        empty = Div(
            Span("🔍", style="font-size:1.6rem; display:block; margin-bottom:.5rem;"),
            Div("No open rooms right now.", style="font-size:.82rem; color:var(--brand-muted); font-weight:600;"),
            Div("Create one and invite friends!", style="font-size:.75rem; color:var(--brand-muted); margin-top:.2rem;"),
            cls="rl-empty",
        )
        return Div(
            empty,
            id="room-list-fragment",
            hx_get=f"/room/list?page=1",
            hx_trigger="every 6000ms",
            hx_target="#room-list-fragment",
            hx_swap="outerHTML",
        )

    cards = [_room_card(r) for r in rooms_data]

    # Pagination row
    prev_btn = (Button(
        "← Prev",
        type="button",
        cls="rl-page-btn",
        hx_get=f"/room/list?page={page - 1}",
        hx_target="#room-list-fragment",
        hx_swap="outerHTML",
    ) if page > 1 else Span(cls="rl-page-spacer"))

    next_btn = (Button(
        "Next →",
        type="button",
        cls="rl-page-btn",
        hx_get=f"/room/list?page={page + 1}",
        hx_target="#room-list-fragment",
        hx_swap="outerHTML",
    ) if page < total_pages else Span(cls="rl-page-spacer"))

    pagination = Div(
        prev_btn,
        Span(f"{page} / {total_pages}", cls="rl-page-label"),
        next_btn,
        cls="rl-pagination",
    )

    return Div(
        *cards,
        (pagination if total_pages > 1 else ()),
        id="room-list-fragment",
        hx_get=f"/room/list?page={page}",
        hx_trigger="every 6000ms",
        hx_target="#room-list-fragment",
        hx_swap="outerHTML",
    )


def team_pick_page(room_code: str, username: str, my_alias: str,
                   prompt: str, team_size: int,
                   team1_aliases: list, team2_aliases: list,
                   error: str = "") -> FT:
    """Shown to a joining player so they can choose Team A or Team B."""

    def _team_panel(team_num: int, aliases: list, color: str, label: str) -> FT:
        has_space = len(aliases) < team_size
        slots = []
        for a in aliases:
            slots.append(Div(
                Span("✓", style=f"color:{color}; font-weight:900; margin-right:.4rem;"),
                Span(a, style="font-weight:700;"),
                cls="tp-slot tp-slot--filled",
            ))
        for _ in range(team_size - len(aliases)):
            slots.append(Div(
                Span("···", style="color:var(--brand-muted); margin-right:.4rem;"),
                Span("Open slot", style="color:var(--brand-muted); font-style:italic;"),
                cls="tp-slot tp-slot--empty",
            ))

        return Div(
            Div(label, cls="tp-team-label", style=f"color:{color};"),
            Div(*slots, cls="tp-slots"),
            (Button(
                f"Join {label} →",
                type="submit",
                name="team",
                value=str(team_num),
                cls="tp-join-btn",
                style=f"border-color:{color}; color:{color}; --tp-btn-glow:{color};",
            ) if has_space else Div(
                "FULL",
                style=(
                    f"text-align:center; font-size:.72rem; font-weight:900;"
                    f"letter-spacing:.12em; color:var(--brand-muted);"
                    f"padding:.55rem; border:1px solid rgba(255,255,255,.1);"
                    f"border-radius:8px;"
                )),
            ),
            cls="tp-team",
            style=f"--tp-color:{color};",
        )

    return Div(

        Div(
            Div("// CUSTOM_ROOM.EXE", cls="wt-sys-label"),
            H1("Choose Your Team", cls="wt-title"),
            cls="wt-info",
            style="margin-bottom:1rem;",
        ),

        # Topic hidden until match starts
        Div(
            Span("🔒", style="font-size:1rem; margin-right:.4rem;"),
            Span("Topic revealed when all players have joined",
                 style="font-size:.78rem; color:var(--brand-muted);"),
            style=(
                "background:rgba(255,255,255,.03); border:1px dashed rgba(255,255,255,.1);"
                "border-radius:8px; padding:.65rem 1rem; margin-bottom:1.25rem;"
                "text-align:center;"
            ),
        ),

        # Error
        (P(f"❌ {error}",
           style="color:var(--brand-red); font-size:.85rem; margin-bottom:.85rem;")
         if error else ()),

        # Team grid
        Form(
            Input(type="hidden", name="player", value=username),
            Input(type="hidden", name="code",   value=room_code),
            Div(
                _team_panel(1, team1_aliases, "#05D9E8", "TEAM A"),
                Div("VS", cls="tp-vs"),
                _team_panel(2, team2_aliases, "#a371f7", "TEAM B"),
                cls="tp-grid",
            ),
            action="/room/pick-team",
            method="post",
        ),

        A("← Back", href="/join-room", cls="cat-back",
          style="margin-top:1rem;"),

        cls="wt-page",
    )


def room_wait_page(room_code: str, username: str, prompt: str = "",
                   team_size: int = 1, team1_aliases: list = None,
                   team2_aliases: list = None, is_host: bool = False,
                   room_name: str = "") -> FT:
    """Shown to any player in the room while waiting for it to fill up."""
    t1 = team1_aliases or []
    t2 = team2_aliases or []
    is_team = team_size > 1
    players_needed = team_size * 2
    players_joined = len(t1) + len(t2)

    leave_action = (
        f"/room/cancel/{room_code}?player={username}" if is_host
        else f"/room/leave/{room_code}?player={username}"
    )
    leave_label = "✕  CANCEL ROOM" if is_host else "← LEAVE ROOM"

    return Div(

        # ── Room indicator ────────────────────────────────────────────────────
        Div(
            Span("🔗", style="font-size:.85rem; margin-right:.4rem;"),
            *(
                [Span(room_name, cls="wt-room-name"), Span(" · ", style="color:rgba(224,224,224,.25); margin:0 .3rem;")]
                if room_name else
                [Span("ROOM ", style="color:rgba(224,224,224,.4); font-size:.7rem; letter-spacing:.1em;")]
            ),
            Span(room_code, cls="wt-room-code"),
            cls="wt-room-indicator",
        ),

        # ── Header ────────────────────────────────────────────────────────────
        Div(
            Div("// PRIVATE_ROOM.EXE", cls="wt-sys-label"),
            H1("Waiting for Players" if is_team else "Waiting for Friend", cls="wt-title"),
            cls="wt-info",
            style="margin-bottom:1.25rem;",
        ),

        # Topic is hidden until match starts — revealed in the arena
        Div(
            Span("🔒", style="font-size:1rem; margin-right:.4rem;"),
            Span("Topic revealed when all players join",
                 style="font-size:.78rem; color:var(--brand-muted);"),
            style=(
                "background:rgba(255,255,255,.03); border:1px dashed rgba(255,255,255,.1);"
                "border-radius:8px; padding:.65rem 1rem; margin-bottom:1.25rem;"
                "text-align:center;"
            ),
        ),

        # ── Team slots (team matches only) ─────────────────────────────────────
        (team_slots_fragment(room_code, team_size, t1, t2) if is_team else ()),

        # ── Player count indicator (team match) ────────────────────────────────
        (Div(
            Span(f"{players_joined} / {players_needed} players joined",
                 style="font-size:.82rem; color:var(--brand-muted); font-weight:600;"),
            style="text-align:center; margin-bottom:1rem;",
        ) if is_team else ()),

        # ── Share link (primary action) ────────────────────────────────────────
        Div(
            Div("SEND THIS LINK TO YOUR FRIEND" if not is_team else "SHARE THIS LINK WITH YOUR TEAM",
                style=(
                    "font-size:.7rem; letter-spacing:.1em; color:var(--brand-muted);"
                    "font-weight:700; margin-bottom:.6rem;"
                )),
            Div(
                Span(id="share-url", cls="wt-share-url"),
                Button(
                    "📋 Copy Link",
                    id="copy-link-btn",
                    type="button",
                    onclick="copyLink()",
                    cls="wt-copy-btn",
                ),
                cls="wt-share-row",
            ),
            style="margin-bottom:1rem;",
        ),

        # ── Fallback code ──────────────────────────────────────────────────────
        Div(
            Span("Or share the code: ", style="color:var(--brand-muted); font-size:.8rem;"),
            Span(room_code, style=(
                "font-size:1.1rem; font-weight:900; letter-spacing:.15em;"
                "color:var(--brand-cyan); font-family:inherit;"
            )),
            style="text-align:center; margin-bottom:1.25rem;",
        ),

        # ── Waiting / Starting indicator ──────────────────────────────────────
        (Div(
            Div(
                Span(cls="wt-dot"),
                Span(cls="wt-dot"),
                Span(cls="wt-dot"),
                cls="wt-dots",
            ),
            Div(
                Span("Waiting for players" if is_team else "Waiting for friend", cls="wt-search-label"),
                Span("0:00", id="wt-elapsed", cls="wt-elapsed"),
                cls="wt-search-row",
            ),
            cls="wt-searching",
        ) if players_joined < players_needed else Div(
            Div("⚔", style="font-size:2rem; margin-bottom:.5rem;"),
            Div("ALL PLAYERS READY", style=(
                "font-size:.8rem; font-weight:900; letter-spacing:.12em;"
                "color:#3fb950; margin-bottom:.3rem;"
            )),
            Div("Match starting...", style=(
                "font-size:.82rem; color:var(--brand-muted);"
            )),
            style=(
                "text-align:center; padding:1.25rem;"
                "background:rgba(63,185,80,.06); border:1px solid rgba(63,185,80,.25);"
                "border-radius:10px;"
            ),
        )),

        # ── Leave / Cancel — always visible ───────────────────────────────────
        Form(
            Button(leave_label, type="submit", cls="wt-cancel-btn"),
            action=leave_action,
            method="post",
            style="margin-top:1rem;",
        ),

        # ── Scripts ───────────────────────────────────────────────────────────
        Script(f"""
(function(){{
  var joinUrl = location.origin + '/r/{room_code}';
  var urlEl   = document.getElementById('share-url');
  if(urlEl) urlEl.textContent = joinUrl;

  window.copyLink = function(){{
    navigator.clipboard.writeText(joinUrl).then(function(){{
      var btn = document.getElementById('copy-link-btn');
      if(btn){{
        btn.textContent = '✅ Copied!';
        setTimeout(function(){{ btn.textContent = '📋 Copy Link'; }}, 2500);
      }}
    }});
  }};

  var el = document.getElementById('wt-elapsed');
  if(el){{
    var s = Date.now();
    setInterval(function(){{
      var d = Math.floor((Date.now()-s)/1000);
      el.textContent = Math.floor(d/60)+':'+String(d%60).padStart(2,'0');
    }}, 1000);
  }}

  // WebSocket — redirect the moment room is full and match starts
  var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  var ws = new WebSocket(proto + '//' + location.host + '/ws/room/{room_code}/{username}');
  ws.onmessage = function(e){{
    try {{
      var data = JSON.parse(e.data);
      if(data.action === 'redirect') window.location.href = data.url;
    }} catch(_) {{}}
  }};
  ws.onerror = function(){{
    setInterval(function(){{
      fetch('/room/check/{room_code}?player={username}')
        .then(function(r){{ return r.text(); }})
        .then(function(html){{
          if(html.indexOf('window.location') !== -1) {{
            var m = html.match(/href\s*=\s*'([^']+)'/);
            if(m) window.location.href = m[1];
          }}
        }});
    }}, 1000);
  }};
}})();
"""),

        cls="wt-page",
    )


def team_slots_fragment(room_code: str, team_size: int,
                        team1_aliases: list, team2_aliases: list) -> FT:
    """HTMX-refreshable team roster shown in the wait room."""

    def _slot(alias=None):
        if alias:
            return Div(
                Span("✓ ", style="color:#3fb950; font-weight:900;"),
                Span(alias, style="font-weight:700; color:var(--fg);"),
                style=(
                    "padding:.45rem .75rem; border-radius:6px;"
                    "background:rgba(63,185,80,.08); border:1px solid rgba(63,185,80,.25);"
                    "font-size:.82rem; margin-bottom:.35rem;"
                ),
            )
        return Div(
            Span("···  ", style="color:var(--brand-muted);"),
            Span("Waiting...", style="color:var(--brand-muted); font-style:italic;"),
            style=(
                "padding:.45rem .75rem; border-radius:6px;"
                "background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.08);"
                "font-size:.82rem; margin-bottom:.35rem;"
            ),
        )

    t1_slots = [_slot(a) for a in team1_aliases] + [_slot() for _ in range(team_size - len(team1_aliases))]
    t2_slots = [_slot(a) for a in team2_aliases] + [_slot() for _ in range(team_size - len(team2_aliases))]

    return Div(
        # Team A
        Div(
            Div("TEAM A", style=(
                "font-size:.68rem; font-weight:900; letter-spacing:.12em;"
                "color:var(--brand-cyan); margin-bottom:.5rem;"
            )),
            *t1_slots,
            style="flex:1;",
        ),
        # VS divider
        Div("VS", style=(
            "font-size:.75rem; font-weight:900; color:var(--brand-muted);"
            "align-self:center; padding:0 .6rem;"
        )),
        # Team B
        Div(
            Div("TEAM B", style=(
                "font-size:.68rem; font-weight:900; letter-spacing:.12em;"
                "color:#a371f7; margin-bottom:.5rem;"
            )),
            *t2_slots,
            style="flex:1;",
        ),
        style=(
            "display:flex; gap:.5rem; align-items:flex-start;"
            "background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.08);"
            "border-radius:8px; padding:.85rem 1rem; margin-bottom:1rem;"
        ),
        id="wt-team-slots",
        hx_get=f"/room/teams/{room_code}",
        hx_trigger="every 1500ms",
        hx_target="#wt-team-slots",
        hx_swap="outerHTML",
    )


def room_teams_live_fragment(
    room_code: str, username: str, team_size: int,
    team1_aliases: list, team2_aliases: list,
    joined_team=None,
) -> FT:
    """
    HTMX-refreshable two-team section.
    joined_team=None  → show JOIN buttons (player hasn't chosen a side yet).
    joined_team=1 or 2 → show 'YOU'RE HERE' badge on the player's team.
    """
    players_joined = len(team1_aliases) + len(team2_aliases)
    players_needed = team_size * 2

    def _slot(alias=None) -> FT:
        if alias:
            return Div(
                Span("✓", style="color:var(--brand-cyan); font-weight:900; margin-right:.4rem;"),
                Span(alias, style="font-weight:700;"),
                cls="tp-slot tp-slot--filled",
            )
        return Div(
            Span("···", style="color:var(--brand-muted); margin-right:.4rem;"),
            Span("Waiting...", style="color:var(--brand-muted); font-style:italic;"),
            cls="tp-slot tp-slot--empty",
        )

    def _panel(team_num: int, aliases: list, color: str, label: str) -> FT:
        is_mine = (joined_team == team_num)
        is_other = (joined_team is not None and not is_mine)
        is_full = len(aliases) >= team_size

        slots = [_slot(a) for a in aliases] + [_slot() for _ in range(team_size - len(aliases))]

        if joined_team is None:
            action = (
                Button(
                    f"JOIN {label} →",
                    type="submit", name="team", value=str(team_num),
                    cls="tp-join-btn",
                    style=f"border-color:{color}; color:{color}; --tp-btn-glow:{color};",
                ) if not is_full else Div(
                    "FULL",
                    style=(
                        "text-align:center; font-size:.7rem; font-weight:900;"
                        "letter-spacing:.12em; color:var(--brand-muted);"
                        "padding:.5rem; border:1px solid rgba(255,255,255,.1);"
                        "border-radius:8px;"
                    ),
                )
            )
        elif is_mine:
            action = Div(
                "◀ YOU'RE HERE",
                style=(
                    f"text-align:center; font-size:.68rem; font-weight:900;"
                    f"letter-spacing:.1em; color:{color}; padding:.45rem;"
                    f"border:1px solid {color}44; border-radius:8px;"
                    f"background:{color}11; margin-top:.25rem;"
                ),
            )
        else:
            action = ()

        panel_cls = "tp-team"
        if is_mine:
            panel_cls += " tp-team--joined"
        elif is_other:
            panel_cls += " tp-team--other"

        return Div(
            Div(label, cls="tp-team-label", style=f"color:{color};"),
            Div(*slots, cls="tp-slots"),
            action,
            cls=panel_cls,
            style=f"--tp-color:{color};",
        )

    grid = Div(
        _panel(1, team1_aliases, "#05D9E8", "TEAM A"),
        Div("VS", cls="tp-vs"),
        _panel(2, team2_aliases, "#a371f7", "TEAM B"),
        cls="tp-grid",
    )

    count_el = Div(
        Span(
            f"{players_joined} / {players_needed} players joined",
            style="font-size:.78rem; color:var(--brand-muted); font-weight:600;",
        ),
        style="text-align:center; margin-top:.75rem; margin-bottom:.5rem;",
    )

    if joined_team is None:
        inner = Form(
            Input(type="hidden", name="player", value=username),
            Input(type="hidden", name="code",   value=room_code),
            grid,
            count_el,
            action="/room/pick-team",
            method="post",
        )
    else:
        inner = Div(grid, count_el)

    return Div(
        inner,
        id="rl-teams-section",
        hx_get=f"/room/teams/{room_code}?username={username}",
        hx_trigger="every 2000ms",
        hx_target="#rl-teams-section",
        hx_swap="outerHTML",
    )


def room_lobby_page(
    room_code: str, username: str, team_size: int,
    team1_aliases: list, team2_aliases: list,
    joined_team=None,
    is_host: bool = False,
    room_name: str = "",
) -> FT:
    """
    Unified lobby for 2v2 / 3v3 custom rooms.
    Works for both the host (joined_team=1) and joining players (joined_team=None until they pick).
    """
    players_joined = len(team1_aliases) + len(team2_aliases)
    players_needed = team_size * 2
    is_joined = joined_team is not None
    is_full   = players_joined >= players_needed
    size_label = f"{team_size}v{team_size}"

    title_text = (
        "All Players Ready!" if is_full and is_joined else
        "Waiting for Players" if is_joined else
        "Choose Your Side"
    )
    sub_text = (
        f"You're on {'Team A' if joined_team == 1 else 'Team B'} · waiting for the room to fill"
        if is_joined and not is_full else
        f"Match starting soon!" if is_full and is_joined else
        f"{size_label} — pick a team to enter the room"
    )

    leave_action = (
        f"/room/cancel/{room_code}?player={username}" if is_host
        else f"/room/leave/{room_code}?player={username}"
    )
    leave_label = "✕  CANCEL ROOM" if is_host else "← LEAVE ROOM"

    return Div(

        # ── Room indicator ────────────────────────────────────────────────────
        Div(
            Span("🔗", style="font-size:.85rem; margin-right:.4rem;"),
            *(
                [Span(room_name, cls="wt-room-name"), Span(" · ", style="color:rgba(224,224,224,.25); margin:0 .3rem;")]
                if room_name else
                [Span("ROOM ", style="color:rgba(224,224,224,.4); font-size:.7rem; letter-spacing:.1em;")]
            ),
            Span(room_code, cls="wt-room-code"),
            cls="wt-room-indicator",
        ),

        # Header
        Div(
            Div("// CUSTOM_ROOM.EXE", cls="wt-sys-label"),
            H1(title_text, cls="wt-title"),
            P(sub_text, style="font-size:.78rem; color:var(--brand-muted); margin:.2rem 0 0;"),
            cls="wt-info",
            style="margin-bottom:1.25rem;",
        ),

        # Topic hidden banner
        Div(
            Span("🔒", style="font-size:1rem; margin-right:.4rem;"),
            Span("Topic revealed when all players join",
                 style="font-size:.78rem; color:var(--brand-muted);"),
            style=(
                "background:rgba(255,255,255,.03); border:1px dashed rgba(255,255,255,.1);"
                "border-radius:8px; padding:.65rem 1rem; margin-bottom:1.25rem; text-align:center;"
            ),
        ),

        # Live team panels (HTMX-refreshed)
        room_teams_live_fragment(
            room_code, username, team_size,
            team1_aliases, team2_aliases, joined_team,
        ),

        # Share link (host / joined players)
        (Div(
            Div(
                "SHARE THIS LINK WITH YOUR TEAM",
                style="font-size:.7rem; letter-spacing:.1em; color:var(--brand-muted); font-weight:700; margin-bottom:.6rem;",
            ),
            Div(
                Span(id="share-url", cls="wt-share-url"),
                Button("📋 Copy Link", id="copy-link-btn", type="button",
                       onclick="copyLink()", cls="wt-copy-btn"),
                cls="wt-share-row",
            ),
            style="margin-bottom:.85rem;",
        ) if is_joined else ()),

        # Room code (always visible — useful for sharing manually)
        Div(
            Span("Room code: ", style="color:var(--brand-muted); font-size:.8rem;"),
            Span(room_code, style=(
                "font-size:1.1rem; font-weight:900; letter-spacing:.15em;"
                "color:var(--brand-cyan); font-family:inherit;"
            )),
            style="text-align:center; margin-bottom:1.25rem;",
        ),

        # Waiting animation (joined, not full)
        (Div(
            Div(
                Span(cls="wt-dot"), Span(cls="wt-dot"), Span(cls="wt-dot"),
                cls="wt-dots",
            ),
            Div(
                Span("Waiting for players", cls="wt-search-label"),
                Span("0:00", id="wt-elapsed", cls="wt-elapsed"),
                cls="wt-search-row",
            ),
            cls="wt-searching",
        ) if is_joined and not is_full else ()),

        # All ready banner (full)
        (Div(
            Div("⚔", style="font-size:2rem; margin-bottom:.5rem;"),
            Div("ALL PLAYERS READY", style=(
                "font-size:.8rem; font-weight:900; letter-spacing:.12em;"
                "color:#3fb950; margin-bottom:.3rem;"
            )),
            Div("Match starting...", style="font-size:.82rem; color:var(--brand-muted);"),
            style=(
                "text-align:center; padding:1.25rem;"
                "background:rgba(63,185,80,.06); border:1px solid rgba(63,185,80,.25);"
                "border-radius:10px;"
            ),
        ) if is_full else ()),

        # Leave / Cancel — always visible for everyone
        Form(
            Button(leave_label, type="submit", cls="wt-cancel-btn"),
            action=leave_action,
            method="post",
            style="margin-top:1rem;",
        ),

        # Scripts
        Script(f"""
(function(){{
  var joinUrl = location.origin + '/r/{room_code}';
  var urlEl   = document.getElementById('share-url');
  if(urlEl) urlEl.textContent = joinUrl;
  window.copyLink = function(){{
    navigator.clipboard.writeText(joinUrl).then(function(){{
      var btn = document.getElementById('copy-link-btn');
      if(btn){{
        btn.textContent = '✅ Copied!';
        setTimeout(function(){{ btn.textContent = '📋 Copy Link'; }}, 2500);
      }}
    }});
  }};
}})();
"""),
        *([ Script(f"""
(function(){{
  var el = document.getElementById('wt-elapsed');
  if(el){{
    var s = Date.now();
    setInterval(function(){{
      var d = Math.floor((Date.now()-s)/1000);
      el.textContent = Math.floor(d/60)+':'+String(d%60).padStart(2,'0');
    }}, 1000);
  }}
  var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  var ws = new WebSocket(proto + '//' + location.host + '/ws/room/{room_code}/{username}');
  ws.onmessage = function(e){{
    try {{
      var data = JSON.parse(e.data);
      if(data.action === 'redirect') window.location.href = data.url;
    }} catch(_) {{}}
  }};
  ws.onerror = function(){{
    setInterval(function(){{
      fetch('/room/check/{room_code}?player={username}')
        .then(function(r){{ return r.text(); }})
        .then(function(html){{
          if(html.indexOf('window.location') !== -1) {{
            var m = html.match(/href='([^']+)'/);
            if(m) window.location.href = m[1];
          }}
        }});
    }}, 1000);
  }};
}})();
""") ] if is_joined else []),

        A("← Back", href="/join-room", cls="cat-back", style="margin-top:1rem;"),

        cls="wt-page",
    )


_PRIVATE_CATEGORIES = [
    ("random",        "🎲", "SURPRISE ME",   "No prep. No excuses.",        "#FFC200"),
    ("world",         "🌍", "WORLD NEWS",     "Live breaking headlines",     "#05D9E8"),
    ("technology",    "💻", "TECHNOLOGY",     "AI · gadgets · startups",     "#a371f7"),
    ("politics",      "🏛️", "POLITICS",       "Power · policy · debate",     "#FF2A6D"),
    ("sports",        "⚽", "SPORTS",         "Wins · trades · rivalry",     "#3fb950"),
    ("entertainment", "🎬", "ENTERTAINMENT",  "Movies · music · celebs",     "#FFC200"),
    ("science",       "🔬", "SCIENCE",        "Space · breakthroughs",       "#05D9E8"),
    ("business",      "💰", "BUSINESS",       "Markets · money · hustle",    "#3fb950"),
    ("gaming",        "🎮", "GAMING",         "Esports · games · culture",   "#a371f7"),
]


def _room_cat_card(slug: str, icon: str, name: str, tagline: str, color: str) -> FT:
    """Compact carousel card for category selection in the custom room creator."""
    return Div(
        Div(
            Span(icon, cls="rc-icon"),
            Div(
                Div(name, cls="rc-name", style=f"color:{color}"),
                Div(tagline, cls="rc-tagline"),
            ),
            Span("✓", cls="rc-check"),
            cls="rc-inner",
            style=f"--rc-color:{color};",
        ),
        cls="rc-card",
        data_slug=slug,
        onclick=f"rcSelect('{slug}')",
        id=f"rc-{slug}",
    )


def join_room_page(error: str = "") -> FT:
    """Custom Room hub — choose Create or Join, then configure."""
    return Div(

        # ── Header ────────────────────────────────────────────────────────────
        Div(
            Div("// CUSTOM_ROOM.EXE", cls="wt-sys-label"),
            H1("Custom Room", cls="wt-title"),
            cls="wt-info",
            style="margin-bottom:1.5rem;",
        ),

        # ── Option toggle cards ────────────────────────────────────────────────
        Div(
            # Create card
            Div(
                Div(
                    Span("🔗", style="font-size:1.6rem; margin-bottom:.35rem; display:block;"),
                    Div("CREATE A ROOM", style=(
                        "font-size:.78rem; font-weight:900; letter-spacing:.1em;"
                        "color:var(--brand-cyan);"
                    )),
                    Div("Set team size · pick topic · invite friends",
                        style="font-size:.72rem; color:var(--brand-muted); margin-top:.2rem;"),
                    cls="pf-option-inner",
                ),
                id="opt-create",
                onclick="selectOption('create')",
                cls="pf-option pf-option--active",
            ),
            # Join card
            Div(
                Div(
                    Span("🔑", style="font-size:1.6rem; margin-bottom:.35rem; display:block;"),
                    Div("JOIN A ROOM", style=(
                        "font-size:.78rem; font-weight:900; letter-spacing:.1em;"
                        "color:#a371f7;"
                    )),
                    Div("Enter the code a friend shared with you",
                        style="font-size:.72rem; color:var(--brand-muted); margin-top:.2rem;"),
                    cls="pf-option-inner",
                ),
                id="opt-join",
                onclick="selectOption('join')",
                cls="pf-option",
            ),
            cls="pf-options",
        ),

        # ── CREATE panel ──────────────────────────────────────────────────────
        Div(
            # Team size selector
            Div(
                Div("TEAM SIZE", style=(
                    "font-size:.65rem; font-weight:900; letter-spacing:.12em;"
                    "color:var(--brand-muted); margin-bottom:.5rem;"
                )),
                Div(
                    *[
                        Button(
                            label,
                            type="button",
                            onclick=f"setTeamSize({n})",
                            id=f"ts-btn-{n}",
                            cls="pf-size-btn",
                        )
                        for n, label in [(1, "1v1"), (2, "2v2"), (3, "3v3")]
                    ],
                    style="display:flex; gap:.5rem; margin-bottom:.5rem;",
                ),
                Div(id="team-size-hint", style=(
                    "font-size:.75rem; color:var(--brand-cyan);"
                    "min-height:1.1em; margin-bottom:1rem;"
                )),
            ),
            # Topic carousel
            Div(
                Div("PICK A TOPIC", style=(
                    "font-size:.65rem; font-weight:900; letter-spacing:.12em;"
                    "color:var(--brand-muted);"
                )),
                Div(
                    Span("👆", style="font-size:.85rem;"),
                    Span("Swipe or tap a card to select"),
                    id="rc-hint",
                    cls="rc-hint",
                ),
                style="margin-bottom:.65rem;",
            ),
            Div(
                # Sliding track
                Div(
                    Div(
                        *[_room_cat_card(slug, icon, name, tagline, color)
                          for slug, icon, name, tagline, color in _PRIVATE_CATEGORIES],
                        cls="rc-track",
                        id="rc-track",
                    ),
                    cls="rc-track-wrap",
                    id="rc-track-wrap",
                ),
                # Nav row: prev · dots · next
                Div(
                    Button("‹", type="button", cls="cs-nav-btn cs-prev", id="rc-prev",
                           onclick="rcStep(-1)", aria_label="Previous topic"),
                    Div(
                        *[Div(cls=f"cs-dot{'  cs-dot--active' if i == 0 else ''}",
                              data_idx=str(i), onclick=f"rcGoTo({i})")
                          for i in range(len(_PRIVATE_CATEGORIES))],
                        cls="cs-dots",
                        id="rc-dots",
                    ),
                    Button("›", type="button", cls="cs-nav-btn cs-next", id="rc-next",
                           onclick="rcStep(1)", aria_label="Next topic"),
                    cls="cs-nav",
                ),
                cls="rc-wrap",
            ),
            # Selected topic summary
            Div(id="cat-summary", style=(
                "font-size:.78rem; color:var(--brand-cyan); min-height:1.2em;"
                "margin-top:.35rem; margin-bottom:.5rem; text-align:center;"
            )),
            # Room name input
            Div(
                Div("ROOM NAME", style=(
                    "font-size:.65rem; font-weight:900; letter-spacing:.12em;"
                    "color:var(--brand-muted); margin-bottom:.4rem;"
                )),
                Input(
                    type="text",
                    id="room-name-input",
                    placeholder="e.g. Friday Night Fights",
                    maxlength="32",
                    autocomplete="off",
                    style=(
                        "width:100%; box-sizing:border-box; background:rgba(255,255,255,.05);"
                        "border:1px solid rgba(255,255,255,.12); border-radius:8px;"
                        "color:var(--fg); font-size:.85rem; padding:.55rem .75rem;"
                        "outline:none; font-family:inherit;"
                    ),
                ),
                style="margin-bottom:.5rem;",
            ),
            # Create Room button
            Button(
                "🔗  Create Room →",
                type="button",
                id="create-room-btn",
                onclick="submitCreate()",
                cls="btn-fight",
                style="width:100%; margin-top:1rem; opacity:.4; cursor:not-allowed;",
                disabled=True,
            ),
            id="panel-create",
            cls="pf-panel",
        ),

        # ── JOIN panel ────────────────────────────────────────────────────────
        Div(
            P(f"❌ {error}",
              style="color:var(--brand-red); margin:0 0 .85rem; font-size:.85rem;",
            ) if error else "",

            # Open rooms list
            Div("OPEN ROOMS", cls="rl-section-label"),
            Div(
                Div(
                    Span(cls="wt-dot"),
                    Span(cls="wt-dot"),
                    Span(cls="wt-dot"),
                    cls="wt-dots",
                    style="justify-content:center; margin:.75rem 0;",
                ),
                id="room-list-fragment",
                hx_get="/room/list?page=1",
                hx_trigger="load",
                hx_target="#room-list-fragment",
                hx_swap="outerHTML",
            ),

            # Separator
            Div(
                Div(cls="rl-sep-line"),
                Span("or enter code manually", cls="rl-sep-label"),
                Div(cls="rl-sep-line"),
                cls="rl-separator",
            ),

            Form(
                Input(
                    type="text",
                    name="code",
                    id="join-code-input",
                    placeholder="Enter code  e.g.  WOLF42",
                    maxlength=6,
                    autocomplete="off",
                    autocapitalize="characters",
                    cls="room-code-input",
                    style="width:100%; box-sizing:border-box; margin-bottom:.75rem;",
                ),
                Button("Join Room →", type="submit", cls="btn-fight", style="width:100%;"),
                action="/room/enter",
                method="post",
            ),
            id="panel-join",
            cls="pf-panel",
            style="display:none;",
        ),

        A("← Back", href="/dashboard", cls="cat-back",
          style="margin-top:1.25rem;"),

        Script("""
(function(){
  /* ── Option toggle ───────────────────────────────────── */
  window.selectOption = function(which) {
    var isCreate = (which === 'create');
    document.getElementById('opt-create').className =
      'pf-option' + (isCreate ? ' pf-option--active' : '');
    document.getElementById('opt-join').className =
      'pf-option' + (!isCreate ? ' pf-option--active pf-option--join' : '');
    document.getElementById('panel-create').style.display = isCreate ? '' : 'none';
    document.getElementById('panel-join').style.display   = isCreate ? 'none' : '';
  };

  /* ── Team size ───────────────────────────────────────── */
  var currentSize = 1;
  var HINTS = {
    1: '1v1 — you vs one friend  (2 players)',
    2: '2v2 — two players per side  (4 total)',
    3: '3v3 — three players per side  (6 total)',
  };

  window.setTeamSize = function(n) {
    currentSize = n;
    [1,2,3].forEach(function(i){
      var b = document.getElementById('ts-btn-'+i);
      if(!b) return;
      b.className = 'pf-size-btn' + (i===n ? ' pf-size-btn--active' : '');
    });
    var hint = document.getElementById('team-size-hint');
    if(hint) hint.textContent = HINTS[n] || '';
  };

  /* ── Category carousel ───────────────────────────────── */
  var selectedSlug = null;
  var rcTotal   = """ + str(len(_PRIVATE_CATEGORIES)) + """;
  var rcCurrent = 0;
  var rcTrack   = document.getElementById('rc-track');
  var rcDots    = document.getElementById('rc-dots');
  var CAT_NAMES = {
    random:'SURPRISE ME', world:'WORLD NEWS', technology:'TECHNOLOGY',
    politics:'POLITICS', sports:'SPORTS', entertainment:'ENTERTAINMENT',
    science:'SCIENCE', business:'BUSINESS', gaming:'GAMING',
  };

  function rcGoTo(idx) {
    rcCurrent = Math.max(0, Math.min(idx, rcTotal - 1));
    rcTrack.style.transform = 'translateX(-' + (rcCurrent * 100) + '%)';
    if(rcDots) rcDots.querySelectorAll('.cs-dot').forEach(function(d, i) {
      d.classList.toggle('cs-dot--active', i === rcCurrent);
    });
    var prev = document.getElementById('rc-prev');
    var next = document.getElementById('rc-next');
    if(prev) prev.style.opacity = rcCurrent === 0 ? '0.3' : '1';
    if(next) next.style.opacity = rcCurrent === rcTotal - 1 ? '0.3' : '1';
    // Pulse the currently visible card (only while nothing is selected)
    if(!selectedSlug) {
      document.querySelectorAll('.rc-card').forEach(function(c, i) {
        c.classList.toggle('rc-card--attention', i === rcCurrent);
      });
    }
  }
  window.rcGoTo = rcGoTo;
  window.rcStep = function(dir) { rcGoTo(rcCurrent + dir); };

  window.rcSelect = function(slug) {
    selectedSlug = slug;
    document.querySelectorAll('.rc-card').forEach(function(el) {
      el.classList.toggle('rc-card--selected', el.dataset.slug === slug);
      el.classList.remove('rc-card--attention');
    });
    var hint = document.getElementById('rc-hint');
    if(hint){ hint.style.opacity='0'; hint.style.pointerEvents='none'; }
    var summary = document.getElementById('cat-summary');
    if(summary) summary.textContent = '✓  ' + (CAT_NAMES[slug] || slug) + ' selected';
    var btn = document.getElementById('create-room-btn');
    if(btn){ btn.disabled = false; btn.style.opacity='1'; btn.style.cursor='pointer'; }
  };

  /* Touch swipe on carousel */
  (function(){
    var wrap = document.getElementById('rc-track-wrap');
    if(!wrap) return;
    var tx = 0, ty = 0, drag = false;
    wrap.addEventListener('touchstart', function(e){
      tx = e.touches[0].clientX; ty = e.touches[0].clientY; drag = true;
    }, { passive: true });
    wrap.addEventListener('touchmove', function(e){
      if(!drag) return;
      if(Math.abs(e.touches[0].clientX-tx) > Math.abs(e.touches[0].clientY-ty))
        e.preventDefault();
    }, { passive: false });
    wrap.addEventListener('touchend', function(e){
      if(!drag) return; drag = false;
      var dx = e.changedTouches[0].clientX - tx;
      var dy = Math.abs(e.changedTouches[0].clientY - ty);
      if(dy > 60) return;
      if(dx < -44) rcGoTo(rcCurrent + 1);
      else if(dx > 44) rcGoTo(rcCurrent - 1);
    });
  })();

  window.submitCreate = function() {
    if(!selectedSlug) return;
    var nameEl = document.getElementById('room-name-input');
    var roomName = nameEl ? nameEl.value.trim() : '';
    window.location.href = '/room/create?category='+selectedSlug+'&team_size='+currentSize+(roomName?'&room_name='+encodeURIComponent(roomName):'');
  };

  rcGoTo(0);
  setTeamSize(1);
})();
"""),

        cls="cat-page",
    )
