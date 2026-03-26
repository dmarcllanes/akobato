from fasthtml.common import *
from models.schemas import MatchState


def waiting_page(display_name: str, real_username: str) -> FT:
    """
    display_name  — alias shown in the UI (never real username)
    real_username — used only in server-side route URLs (WS, cancel)
                    only visible in the player's own browser, never to opponents
    """
    return Div(

        # ── Animated radar (never swapped — always visible) ───────────────────
        Div(
            Div(cls="wt-radar-ring wt-ring-1"),
            Div(cls="wt-radar-ring wt-ring-2"),
            Div(cls="wt-radar-ring wt-ring-3"),
            Div(
                Span("⚔", cls="wt-radar-icon"),
                cls="wt-radar-core",
            ),
            cls="wt-radar",
        ),

        # ── Status text ───────────────────────────────────────────────────────
        Div(
            Div("// MATCHMAKING.EXE", cls="wt-sys-label"),
            H1("Scanning for Opponent", cls="wt-title"),
            Div(
                Span("FIGHTER", cls="wt-tag"),
                Span(display_name, cls="wt-username"),
                cls="wt-fighter-row",
            ),
            cls="wt-info",
        ),

        # ── Dots + label (animation never resets) ─────────────────────────────
        Div(
            Div(
                Span(cls="wt-dot"),
                Span(cls="wt-dot"),
                Span(cls="wt-dot"),
                cls="wt-dots",
            ),
            Div(
                Span("Searching", cls="wt-search-label"),
                Span("0:00", id="wt-elapsed", cls="wt-elapsed"),
                cls="wt-search-row",
            ),
            cls="wt-searching",
        ),

        # ── Cancel ────────────────────────────────────────────────────────────
        Form(
            Button("✕  CANCEL SEARCH", type="submit", cls="wt-cancel-btn"),
            action=f"/lobby/cancel/{real_username}",
            method="post",
        ),

        # ── WebSocket + elapsed timer ─────────────────────────────────────────
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

  // WebSocket for instant redirect when opponent found
  var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  var ws = new WebSocket(proto + '//' + location.host + '/ws/lobby/{real_username}');
  ws.onmessage = function(e){{
    try {{
      var data = JSON.parse(e.data);
      if(data.action === 'redirect') window.location.href = data.url;
    }} catch(_) {{}}
  }};
  ws.onerror = function(){{
    // Fallback to HTTP poll if WebSocket fails
    setInterval(function(){{
      fetch('/lobby/check/{real_username}').then(function(r){{ return r.text(); }}).then(function(html){{
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


def arena_page(match: MatchState, username: str, my_alias: str = "") -> FT:
    started_at_ms = int(match.started_at * 1000) if match.started_at else 0
    display_me  = my_alias or match.alias_of(username)
    display_opp = match.opponent_alias_of(username)

    return Div(
        Div(
            H2("⚔️ The Arena", style="margin:0"),
            P(
                f"{display_me}  vs  {display_opp}",
                style="color: var(--brand-muted); margin: 0.25rem 0 0;",
            ),
            cls="arena-header",
        ),

        Div(match.prompt, cls="prompt-box"),

        Div(
            Div(str(match.duration), id="timer-val"),
            id="timer-display",
        ),

        Form(
            Textarea(
                placeholder="Type your argument here. Be bold, be concise, be human...",
                name="argument",
                id="argument-input",
                cls="debate-textarea",
                maxlength=500,
            ),
            Input(type="hidden", name="player", value=username),
            Button("🔥 Submit Argument", type="submit", cls="btn-fight mt-2", id="submit-btn"),
            id="debate-form",
            hx_post=f"/game/{match.match_id}/submit",
            hx_target="#submit-area",
            hx_swap="outerHTML",
        ),

        Div(
            P("Waiting for your opponent to submit...", cls="status-waiting"),
            id="submit-area",
        ),

        Script(f"""
(function() {{
  var startedAt = {started_at_ms};
  var duration  = {match.duration * 1000};
  var timerEl   = document.getElementById('timer-val');
  var displayEl = document.getElementById('timer-display');
  var submitted = false;

  // Stop timer when the form is submitted
  var form = document.getElementById('debate-form');
  if(form) {{
    form.addEventListener('submit', function() {{ submitted = true; }});
  }}

  function tick() {{
    if(submitted) return;
    var remaining = Math.max(0, Math.ceil((startedAt + duration - Date.now()) / 1000));
    if(timerEl)   timerEl.textContent = remaining;
    if(remaining <= 10 && displayEl) displayEl.classList.add('timer-low');
    if(remaining === 0) {{
      submitted = true;
      if(form) htmx.trigger(form, 'submit');
    }}
  }}

  setInterval(tick, 500);
  tick();
}})();
"""),
    )


def submit_status_fragment(match_id: str, player: str,
                           submitted: int, total: int, judging: bool) -> FT:
    """
    HTMX-refreshable inner panel — returned by both submitted_view()
    and the /game/{match_id}/submit-count endpoint so they always look identical.
    """
    is_judging = judging or submitted >= total

    if is_judging:
        icon    = "⚖️"
        title   = "JUDGING IN PROGRESS"
        title_c = "#FFC200"
        msg     = "The AI Judge is deliberating…"
        dots_cls = "sw-dots sw-dots--fast"
    else:
        remaining = total - submitted
        icon    = "⏳"
        title   = f"WAITING FOR FIGHTERS  ·  {submitted}/{total}"
        title_c = "var(--brand-cyan)"
        msg     = (f"{remaining} more player{'s' if remaining != 1 else ''} "
                   f"still need{'s' if remaining == 1 else ''} to submit")
        dots_cls = "sw-dots"

    # Slot pips — filled = submitted, hollow = pending
    pips = Div(
        *[
            Span(
                cls="sw-pip sw-pip--done" if i < submitted else "sw-pip sw-pip--wait",
            )
            for i in range(total)
        ],
        cls="sw-pips",
    )

    # Progress bar
    pct = int(submitted / total * 100) if total else 100
    bar = Div(
        Div(cls="sw-bar-fill", style=f"width:{pct}%;"),
        cls="sw-bar",
    )

    return Div(
        # Icon + title
        Div(
            Span(icon, style="font-size:1.5rem; line-height:1;"),
            Span(title, style=(
                f"font-size:.65rem; font-weight:900; letter-spacing:.13em;"
                f"color:{title_c};"
            )),
            cls="sw-header",
        ),
        # Slot pips
        pips,
        # Progress bar
        bar,
        # Message
        Div(
            Div(cls=dots_cls),
            Span(msg, cls="sw-msg-text"),
            cls="sw-msg",
        ),
        # HTMX self-refresh
        id="submit-status",
        hx_get=f"/game/{match_id}/submit-count?player={player}",
        hx_trigger="every 1500ms",
        hx_target="#submit-status",
        hx_swap="outerHTML",
        cls="sw-panel",
    )


def submitted_view(username: str, match_id: str, submitted: int = 0, total: int = 2,
                   judging: bool = False) -> FT:
    """Shown after a player submits their argument."""
    return Div(
        # ── Lock-in confirmation ───────────────────────────────────────────────
        Div(
            Div(
                Span("🔒", style="font-size:2rem; display:block; margin-bottom:.3rem;"),
                Div("ARGUMENT LOCKED IN", style=(
                    "font-size:.68rem; font-weight:900; letter-spacing:.15em;"
                    "color:var(--brand-cyan);"
                )),
                cls="sw-locked-badge",
            ),
        ),

        # ── Live status panel ─────────────────────────────────────────────────
        submit_status_fragment(match_id, username, submitted, total, judging),

        # ── WebSocket — instant redirect when verdict is ready ─────────────────
        Script(f"""
(function(){{
  var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  var ws = new WebSocket(proto + '//' + location.host + '/ws/arena/{match_id}/{username}');
  ws.onmessage = function(e){{
    try {{
      var data = JSON.parse(e.data);
      if(data.action === 'redirect') window.location.href = data.url;
    }} catch(_) {{}}
  }};
  ws.onerror = function(){{
    setInterval(function(){{
      fetch('/game/{match_id}/status?player={username}')
        .then(function(r){{ return r.text(); }})
        .then(function(html){{
          if(html.indexOf('verdict') !== -1) window.location.href = '/game/{match_id}?player={username}';
        }});
    }}, 1000);
  }};
}})();
"""),

        id="submit-area",
        cls="sw-container",
    )
