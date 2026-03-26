from fasthtml.common import *


def room_wait_page(room_code: str, username: str) -> FT:
    """Shown to the host while waiting for friend to join."""
    return Div(

        # ── Icon ──────────────────────────────────────────────────────────────
        Div(
            Span("🔗", style="font-size:2rem; line-height:1;"),
            cls="room-icon-wrap",
        ),

        # ── Header ────────────────────────────────────────────────────────────
        Div(
            Div("// PRIVATE_ROOM.EXE", cls="wt-sys-label"),
            H1("Private Room", cls="wt-title"),
            P("Share this code with your friend.", cls="room-sub"),
            cls="wt-info",
        ),

        # ── Room code ─────────────────────────────────────────────────────────
        Div(
            Span(room_code, cls="room-code-text", id="room-code-val"),
            Button(
                "Copy",
                cls="room-copy-btn",
                id="room-copy-btn",
                type="button",
                onclick=f"copyCode('{room_code}')",
            ),
            cls="room-code-box",
        ),

        # ── Waiting indicator ─────────────────────────────────────────────────
        Div(
            Div(
                Span(cls="wt-dot"),
                Span(cls="wt-dot"),
                Span(cls="wt-dot"),
                cls="wt-dots",
            ),
            Div(
                Span("Waiting for friend", cls="wt-search-label"),
                Span("0:00", id="wt-elapsed", cls="wt-elapsed"),
                cls="wt-search-row",
            ),
            cls="wt-searching",
            style="margin-top:.5rem;",
        ),

        # ── Cancel ────────────────────────────────────────────────────────────
        Form(
            Button("✕  CANCEL ROOM", type="submit", cls="wt-cancel-btn"),
            action=f"/room/cancel/{room_code}?player={username}",
            method="post",
        ),

        # ── Scripts ───────────────────────────────────────────────────────────
        Script(f"""
(function(){{
  // Elapsed timer
  var el = document.getElementById('wt-elapsed');
  if(el){{
    var s = Date.now();
    setInterval(function(){{
      var d = Math.floor((Date.now()-s)/1000);
      el.textContent = Math.floor(d/60)+':'+String(d%60).padStart(2,'0');
    }}, 1000);
  }}

  // Copy code helper
  window.copyCode = function(code){{
    navigator.clipboard.writeText(code).then(function(){{
      var btn = document.getElementById('room-copy-btn');
      if(btn){{ btn.textContent='Copied!'; setTimeout(function(){{ btn.textContent='Copy'; }}, 2000); }}
    }});
  }};

  // WebSocket for instant redirect when friend joins
  var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  var ws = new WebSocket(proto + '//' + location.host + '/ws/room/{room_code}/{username}');
  ws.onmessage = function(e){{
    try {{
      var data = JSON.parse(e.data);
      if(data.action === 'redirect') window.location.href = data.url;
      if(data.action === 'error') console.warn('WS room error:', data.msg);
    }} catch(_) {{}}
  }};
  ws.onerror = function(){{
    // Fallback: HTTP poll
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
                    style="display:flex; align-items:center; gap:.75rem; margin-bottom:1rem;",
                ),
                Div(
                    *[
                        A(
                            Span(icon, style="font-size:1.1rem;"),
                            Span(name, style="font-size:.75rem; font-weight:700; letter-spacing:.04em;"),
                            href=f"/room/create?category={slug}",
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

        cls="cat-page",
    )
