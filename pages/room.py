from fasthtml.common import *


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

        # ── Debate topic preview ───────────────────────────────────────────────
        (Div(
            Div("TODAY'S TOPIC", style=(
                "font-size:.7rem; letter-spacing:.1em; color:var(--brand-muted);"
                "font-weight:700; margin-bottom:.4rem;"
            )),
            Div(prompt, style="font-size:.95rem; color:var(--fg); line-height:1.4;"),
            style=(
                "background:rgba(5,217,232,.06); border:1px solid rgba(5,217,232,.2);"
                "border-radius:8px; padding:.85rem 1rem; margin-bottom:1.25rem;"
                "text-align:center;"
            ),
        ) if prompt else ()),

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
    """Hub page: create a private room OR join one with a code."""
    return Div(

        # ── Header ────────────────────────────────────────────────────────────
        Div(
            Div("// PRIVATE_ROOM.EXE", cls="wt-sys-label"),
            H1("Private Room", cls="wt-title"),
            cls="wt-info",
        ),

        # ── Two columns: Create | Join ─────────────────────────────────────────
        Div(

            # ── CREATE side ───────────────────────────────────────────────────
            Div(
                Div(
                    Span("🔗", style="font-size:1.4rem;"),
                    Div(
                        Div("CREATE A ROOM", style="font-weight:800; font-size:.95rem; letter-spacing:.06em;"),
                        Div("Pick a topic — get a shareable code", style="font-size:.78rem; color:var(--brand-muted); margin-top:.1rem;"),
                    ),
                    style="display:flex; align-items:center; gap:.75rem; margin-bottom:.85rem;",
                ),

                # ── Team size selector ────────────────────────────────────────
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
                                data_size=str(n),
                                onclick=f"setTeamSize({n})",
                                id=f"ts-btn-{n}",
                                style=(
                                    "padding:.4rem .9rem; border-radius:6px; cursor:pointer;"
                                    "font-size:.75rem; font-weight:800; letter-spacing:.07em;"
                                    "border:1px solid rgba(255,255,255,.15);"
                                    "background:rgba(255,255,255,.04); color:var(--brand-muted);"
                                    "transition:all .15s;"
                                ),
                            )
                            for n, label in [(1, "1v1"), (2, "2v2"), (3, "3v3")]
                        ],
                        style="display:flex; gap:.5rem; margin-bottom:1rem;",
                    ),
                    Div(id="team-size-hint", style="font-size:.75rem; color:var(--brand-muted); margin-bottom:.85rem;"),
                ),

                # ── Category grid ─────────────────────────────────────────────
                Div(
                    *[
                        A(
                            Span(icon, style="font-size:1.1rem;"),
                            Span(name, style="font-size:.75rem; font-weight:700; letter-spacing:.04em;"),
                            href=f"/room/create?category={slug}&team_size=1",
                            data_slug=slug,
                            cls="priv-cat-link",
                            style=(
                                "display:flex; align-items:center; gap:.5rem;"
                                "padding:.55rem .8rem; border-radius:6px;"
                                "border:1px solid rgba(255,255,255,.1);"
                                "background:rgba(255,255,255,.04);"
                                "color:var(--fg); text-decoration:none;"
                                "transition:background .15s, border-color .15s;"
                                "white-space:nowrap;"
                            ),
                        )
                        for slug, icon, name in _PRIVATE_CATEGORIES
                    ],
                    style=(
                        "display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr));"
                        "gap:.5rem;"
                    ),
                ),

                cls="card",
                style="padding:1.25rem; flex:1;",
            ),

            # ── JOIN side ─────────────────────────────────────────────────────
            Div(
                Div(
                    Span("🔑", style="font-size:1.4rem;"),
                    Div(
                        Div("JOIN A ROOM", style="font-weight:800; font-size:.95rem; letter-spacing:.06em;"),
                        Div("Enter the code your friend shared", style="font-size:.78rem; color:var(--brand-muted); margin-top:.1rem;"),
                    ),
                    style="display:flex; align-items:center; gap:.75rem; margin-bottom:1rem;",
                ),
                P(
                    f"❌ {error}",
                    style="color:var(--brand-red); margin:0 0 .75rem; font-size:.85rem;",
                ) if error else "",
                Form(
                    Input(
                        type="text",
                        name="code",
                        placeholder="e.g. WOLF42",
                        maxlength=6,
                        autocomplete="off",
                        autocapitalize="characters",
                        cls="room-code-input",
                        style="width:100%; box-sizing:border-box; margin-bottom:.75rem;",
                    ),
                    Button("Enter Room →", type="submit", cls="btn-fight", style="width:100%;"),
                    action="/room/enter",
                    method="post",
                ),
                cls="card",
                style="padding:1.25rem; flex:1; min-width:220px;",
            ),

            style="display:flex; flex-wrap:wrap; gap:1.25rem; align-items:flex-start;",
        ),

        A("← Back to Play", href="/play", cls="cat-back", style="margin-top:1rem; display:inline-block;"),

        Script("""
(function(){
  var currentSize = 1;
  var HINTS = {
    1: 'Classic 1v1 — you vs one friend.',
    2: '2v2 — two players per side, 4 total.',
    3: '3v3 — three players per side, 6 total.',
  };
  var ACTIVE_STYLE = (
    'padding:.4rem .9rem; border-radius:6px; cursor:pointer;' +
    'font-size:.75rem; font-weight:800; letter-spacing:.07em;' +
    'border:1px solid var(--brand-cyan);' +
    'background:rgba(5,217,232,.12); color:var(--brand-cyan);' +
    'transition:all .15s;'
  );
  var IDLE_STYLE = (
    'padding:.4rem .9rem; border-radius:6px; cursor:pointer;' +
    'font-size:.75rem; font-weight:800; letter-spacing:.07em;' +
    'border:1px solid rgba(255,255,255,.15);' +
    'background:rgba(255,255,255,.04); color:var(--brand-muted);' +
    'transition:all .15s;'
  );

  window.setTeamSize = function(n) {
    currentSize = n;
    [1,2,3].forEach(function(i){
      var btn = document.getElementById('ts-btn-'+i);
      if(btn) btn.style.cssText = (i === n) ? ACTIVE_STYLE : IDLE_STYLE;
    });
    var hint = document.getElementById('team-size-hint');
    if(hint) hint.textContent = HINTS[n] || '';
    document.querySelectorAll('.priv-cat-link').forEach(function(a){
      var slug = a.dataset.slug;
      if(slug) a.href = '/room/create?category=' + slug + '&team_size=' + n;
    });
  };

  setTeamSize(1);
})();
"""),

        cls="cat-page",
    )
