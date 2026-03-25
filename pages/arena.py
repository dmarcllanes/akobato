from fasthtml.common import *
from models.schemas import MatchState


def waiting_page(username: str) -> FT:
    return Div(

        # ── Animated radar ────────────────────────────────────────────────────
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
                Span(username, cls="wt-username"),
                cls="wt-fighter-row",
            ),
            cls="wt-info",
        ),

        # ── HTMX poll area ────────────────────────────────────────────────────
        Div(
            Div(
                Span(cls="wt-dot"),
                Span(cls="wt-dot"),
                Span(cls="wt-dot"),
                cls="wt-dots",
            ),
            Span("Searching", cls="wt-search-label"),
            id="poll-area",
            hx_get=f"/lobby/check/{username}",
            hx_trigger="every 2s",
            hx_target="#poll-area",
            hx_swap="outerHTML",
            cls="wt-searching",
        ),

        # ── Cancel ────────────────────────────────────────────────────────────
        Form(
            Button("✕  CANCEL SEARCH", type="submit", cls="wt-cancel-btn"),
            action=f"/lobby/cancel/{username}",
            method="post",
        ),

        cls="wt-page",
    )


def arena_page(match: MatchState, username: str) -> FT:
    started_at_ms = int(match.started_at * 1000) if match.started_at else 0
    opponent = match.opponent_of(username) or "???"

    return Div(
        Div(
            H2("⚔️ The Arena", style="margin:0"),
            P(
                f"{username}  vs  {opponent}",
                style="color: var(--brand-muted); margin: 0.25rem 0 0;",
            ),
            cls="arena-header",
        ),

        Div(match.prompt, cls="prompt-box"),

        Div(
            Div("60", id="timer-val"),
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
            hx_get=f"/game/{match.match_id}/status?player={username}",
            hx_trigger="every 2s",
            hx_target="#submit-area",
            hx_swap="outerHTML",
        ),

        Script(f"""
(function() {{
  var startedAt = {started_at_ms};
  var duration  = {MatchState.DURATION * 1000};
  var timerEl   = document.getElementById('timer-val');
  var displayEl = document.getElementById('timer-display');
  var submitted = false;

  function tick() {{
    var remaining = Math.max(0, Math.ceil((startedAt + duration - Date.now()) / 1000));
    if (timerEl)   timerEl.textContent = remaining;
    if (remaining <= 10 && displayEl) displayEl.classList.add('timer-low');
    if (remaining === 0 && !submitted) {{
      submitted = true;
      var form = document.getElementById('debate-form');
      if (form) htmx.trigger(form, 'submit');
    }}
  }}

  setInterval(tick, 500);
  tick();
}})();
"""),
    )


def submitted_view(username: str, match_id: str) -> FT:
    return Div(
        Span("✅ Argument submitted!", cls="submitted-badge"),
        P("Waiting for the AI Judge...", cls="status-waiting", style="margin-top: 0.5rem;"),
        id="submit-area",
        hx_get=f"/game/{match_id}/status?player={username}",
        hx_trigger="every 2s",
        hx_target="#submit-area",
        hx_swap="outerHTML",
    )
