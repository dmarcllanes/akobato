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
        code     = r["code"]
        ts       = r["team_size"]
        joined   = r["players_joined"]
        total    = r["players_total"]
        cat      = r.get("category", "random")
        icon     = _CAT_ICONS.get(cat, "🎲")
        cat_name = _CAT_NAMES.get(cat, cat.upper())
        size_lbl = f"{ts}v{ts}"
        spots    = total - joined
        full_cls = " rl-card--full" if spots == 0 else ""

        return Div(
            # Left: category icon + info
            Div(
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
                cls="rl-card-left",
            ),
            # Right: code + select button
            Div(
                Span(code, cls="rl-code"),
                (Button(
                    "Select →",
                    type="button",
                    cls="rl-select-btn",
                    onclick=f"selectRoom('{code}')",
                ) if spots > 0 else Span("FULL", cls="rl-full-badge")),
                cls="rl-card-right",
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
          style="margin-top:1rem; display:inline-block;"),

        cls="wt-page",
    )


def room_wait_page(room_code: str, username: str, prompt: str = "",
                   team_size: int = 1, team1_aliases: list = None,
                   team2_aliases: list = None) -> FT:
    """Shown to any player in the room while waiting for it to fill up."""
    t1 = team1_aliases or []
    t2 = team2_aliases or []
    is_team = team_size > 1
    players_needed = team_size * 2
    players_joined = len(t1) + len(t2)

    return Div(

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
                Span(id="share-url", style=(
                    "flex:1; font-size:.85rem; font-family:inherit;"
                    "color:var(--brand-cyan); word-break:break-all;"
                )),
                Button(
                    "📋 Copy Link",
                    id="copy-link-btn",
                    type="button",
                    onclick="copyLink()",
                    style=(
                        "white-space:nowrap; padding:.5rem 1rem;"
                        "background:var(--brand-cyan); color:#000; border:none;"
                        "border-radius:6px; font-weight:700; cursor:pointer;"
                        "font-size:.8rem; letter-spacing:.05em;"
                    ),
                ),
                style=(
                    "display:flex; align-items:center; gap:.75rem;"
                    "background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1);"
                    "border-radius:8px; padding:.75rem 1rem;"
                ),
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

        # ── Waiting indicator ─────────────────────────────────────────────────
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
        ) if players_joined < players_needed else ()),

        # ── Cancel ────────────────────────────────────────────────────────────
        Form(
            Button("✕  CANCEL", type="submit", cls="wt-cancel-btn"),
            action=f"/room/cancel/{room_code}?player={username}",
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


_PRIVATE_CATEGORIES = [
    ("random",        "🎲", "SURPRISE ME"),
    ("world",         "🌍", "WORLD NEWS"),
    ("technology",    "💻", "TECHNOLOGY"),
    ("politics",      "🏛️", "POLITICS"),
    ("sports",        "⚽", "SPORTS"),
    ("entertainment", "🎬", "ENTERTAINMENT"),
    ("science",       "🔬", "SCIENCE"),
    ("business",      "💰", "BUSINESS"),
    ("gaming",        "🎮", "GAMING"),
]


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
            # Topic label
            Div("PICK A TOPIC", style=(
                "font-size:.65rem; font-weight:900; letter-spacing:.12em;"
                "color:var(--brand-muted); margin-bottom:.65rem;"
            )),
            # Selectable category grid
            Div(
                *[
                    Div(
                        Span(icon, style="font-size:1.15rem;"),
                        Div(name, style="font-size:.78rem; font-weight:700; letter-spacing:.04em;"),
                        Span("✓", cls="pf-cat-check"),
                        data_slug=slug,
                        onclick=f"selectCategory('{slug}')",
                        id=f"cat-{slug}",
                        cls="pf-cat-card",
                    )
                    for slug, icon, name in _PRIVATE_CATEGORIES
                ],
                cls="pf-cat-grid",
            ),
            # Selected topic summary
            Div(id="cat-summary", style=(
                "font-size:.78rem; color:var(--brand-cyan); min-height:1.2em;"
                "margin-top:.65rem; text-align:center;"
            )),
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
          style="margin-top:1.25rem; display:inline-block;"),

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

  /* ── Category selection ──────────────────────────────── */
  var selectedSlug = null;
  var CAT_NAMES = {
    random:'SURPRISE ME', world:'WORLD NEWS', technology:'TECHNOLOGY',
    politics:'POLITICS', sports:'SPORTS', entertainment:'ENTERTAINMENT',
    science:'SCIENCE', business:'BUSINESS', gaming:'GAMING',
  };

  window.selectCategory = function(slug) {
    selectedSlug = slug;
    document.querySelectorAll('.pf-cat-card').forEach(function(el){
      el.classList.toggle('pf-cat-card--selected', el.dataset.slug === slug);
    });
    var summary = document.getElementById('cat-summary');
    if(summary) summary.textContent = '✓  ' + (CAT_NAMES[slug] || slug) + ' selected';
    var btn = document.getElementById('create-room-btn');
    if(btn){ btn.disabled = false; btn.style.opacity='1'; btn.style.cursor='pointer'; }
  };

  window.submitCreate = function() {
    if(!selectedSlug) return;
    window.location.href = '/room/create?category='+selectedSlug+'&team_size='+currentSize;
  };

  /* ── Room list — select fills code input ─────────────────── */
  window.selectRoom = function(code) {
    selectOption('join');
    var inp = document.getElementById('join-code-input');
    if(inp){ inp.value = code; inp.focus(); }
  };

  setTeamSize(1);
})();
"""),

        cls="cat-page",
    )
