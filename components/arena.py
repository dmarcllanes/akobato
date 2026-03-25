from fasthtml.common import *
from models.schemas import MatchState


def home_page(username: str | None = None) -> FT:
    if username:
        # Logged-in state
        return Div(
            Div(
                H1("⚔️ Akobato"),
                P("A polarizing prompt. 60 seconds. One winner.", cls="tagline"),
                P(
                    f"Welcome, ", Strong(username), "! Ready to clash?",
                    style="color: var(--brand-muted); margin-bottom: 2rem;",
                ),
                A("⚡ Enter the Arena", href="/join", cls="btn-fight", style="display:block; text-align:center; text-decoration:none;"),
                Form(
                    Button("Sign out", type="submit", cls="btn-signout"),
                    action="/auth/logout",
                    method="post",
                    style="margin-top: 1rem;",
                ),
                cls="home-hero",
            )
        )

    # Guest state — show Google sign-in
    return Div(
        Div(
            H1("⚔️ Akobato"),
            P("A polarizing prompt. 60 seconds. One winner.", cls="tagline"),
            P(
                Em("Breaking news turns into debate fuel. An AI Judge decides your fate."),
                style="color: var(--brand-muted); margin-bottom: 2.5rem;",
            ),
            A(
                Img(src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg", height="20", style="vertical-align:middle; margin-right:8px;"),
                "Sign in with Google",
                href="/auth/login",
                cls="btn-google",
            ),
            cls="home-hero",
        )
    )


def waiting_page(username: str) -> FT:
    return Div(
        Div(
            Div(cls="pulse-circle"),
            H2("Searching for an opponent..."),
            P(
                "Fighting as ", Strong(username), ". A worthy opponent is being summoned.",
                style="color: var(--brand-muted);",
            ),
            Div(
                P("⏳ Waiting...", cls="status-waiting"),
                id="poll-area",
                hx_get=f"/lobby/check/{username}",
                hx_trigger="every 2s",
                hx_target="#poll-area",
                hx_swap="outerHTML",
            ),
            cls="waiting-box",
        )
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
  var duration = {MatchState.DURATION * 1000};
  var timerEl = document.getElementById('timer-val');
  var displayEl = document.getElementById('timer-display');
  var submitted = false;

  function tick() {{
    var remaining = Math.max(0, Math.ceil((startedAt + duration - Date.now()) / 1000));
    if (timerEl) timerEl.textContent = remaining;
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
