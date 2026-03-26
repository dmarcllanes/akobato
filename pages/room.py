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


def join_room_page(error: str = "") -> FT:
    """Standalone page where a friend enters a room code to join."""
    return Div(
        Div(
            Div("// JOIN_PRIVATE_ROOM.EXE", cls="wt-sys-label"),
            H1("Join a Room", cls="wt-title"),
            P("Enter the 6-character code your friend shared with you.", cls="room-sub"),
            cls="wt-info",
        ),

        Div(
            P(f"❌ {error}", style="color:var(--brand-red); margin:0 0 .75rem; font-size:.85rem;") if error else "",
            Form(
                Div(
                    Input(
                        type="text",
                        name="code",
                        placeholder="e.g. WOLF42",
                        maxlength=6,
                        autocomplete="off",
                        autocapitalize="characters",
                        cls="room-code-input",
                        autofocus=True,
                    ),
                    Button("Enter Room →", type="submit", cls="btn-fight"),
                    cls="room-join-row",
                ),
                action="/room/enter",
                method="post",
            ),
            cls="card room-join-card",
        ),

        A("← Back", href="/play", cls="cat-back", style="margin-top:1.5rem; display:inline-block;"),

        cls="wt-page",
        style="gap:1.5rem;",
    )
