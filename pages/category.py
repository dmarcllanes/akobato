from fasthtml.common import *

CATEGORIES = [
    ("world",         "🌍", "WORLD NEWS",    "Live breaking headlines",   "#05D9E8"),
    ("technology",    "💻", "TECHNOLOGY",    "AI · gadgets · startups",   "#a371f7"),
    ("politics",      "🏛️", "POLITICS",      "Power · policy · debate",   "#FF2A6D"),
    ("sports",        "⚽", "SPORTS",        "Wins · trades · rivalry",   "#3fb950"),
    ("entertainment", "🎬", "ENTERTAINMENT", "Movies · music · celebs",   "#FFC200"),
    ("science",       "🔬", "SCIENCE",       "Space · breakthroughs",     "#05D9E8"),
    ("business",      "💰", "BUSINESS",      "Markets · money · hustle",  "#3fb950"),
    ("gaming",        "🎮", "GAMING",        "Esports · games · culture", "#a371f7"),
    ("random",        "🎲", "SURPRISE ME",   "No prep. No excuses.",      "#FFC200"),
]


def category_page(username: str, tokens: int = 5) -> FT:
    no_tokens = tokens <= 0

    token_bar = Div(
        Div(
            Span("⚡", cls="cat-token-icon"),
            Span(f"{tokens} / 5", cls="cat-token-count"),
            Span("ENERGY", cls="cat-token-label"),
            cls="cat-token-left",
        ),
        Div(
            *[Span(cls=f"cat-token-pip {'cat-token-pip--on' if i < tokens else ''}",
                   key=i) for i in range(5)],
            cls="cat-token-pips",
        ),
        cls=f"cat-token-bar {'cat-token-bar--empty' if no_tokens else ''}",
    )

    no_tokens_banner = Div(
        Span("⚡", cls="cat-no-tokens-icon"),
        Div(
            Div("NO ENERGY", cls="cat-no-tokens-title"),
            Div("You're out of tokens. Tokens restore after each completed match.", cls="cat-no-tokens-sub"),
            cls="cat-no-tokens-text",
        ),
        cls="cat-no-tokens-banner",
    ) if no_tokens else ()

    return Div(

        # ── Header ────────────────────────────────────────────────────────────
        Div(
            Div("// SELECT_BATTLEFIELD.EXE", cls="cat-sys-label"),
            H1("Choose Your Arena", cls="cat-title"),
            P(
                Span(username, style="color:#05D9E8"),
                " — pick a topic. Your opponent gets the same prompt.",
                cls="cat-sub",
            ),
            token_bar,
            cls="cat-header",
        ),

        no_tokens_banner,

        # ── Mode selector ─────────────────────────────────────────────────────
        Div(
            Button(
                Span("⚡", cls="mode-icon"),
                Div(Span("SOLO", cls="mode-label"), Span("1 min · vs AI · instant", cls="mode-desc"), cls="mode-text"),
                id="btn-solo", cls="mode-btn mode-btn--active", type="button", onclick="setMode('solo')",
            ),
            Button(
                Span("👥", cls="mode-icon"),
                Div(Span("VERSUS", cls="mode-label"), Span("2 min · vs human · matchmaking", cls="mode-desc"), cls="mode-text"),
                id="btn-versus", cls="mode-btn", type="button", onclick="setMode('versus')",
            ),
            Button(
                Span("🔗", cls="mode-icon"),
                Div(Span("PRIVATE", cls="mode-label"), Span("2 min · invite friend · room code", cls="mode-desc"), cls="mode-text"),
                id="btn-private", cls="mode-btn", type="button", onclick="setMode('private')",
            ),
            cls="mode-selector",
        ),

        # ── Join existing room (shown only in private mode) ────────────────────
        Div(
            Span("Already have a code?", cls="room-inline-label"),
            Form(
                Input(
                    type="text", name="code", placeholder="WOLF42",
                    maxlength=6, autocomplete="off", autocapitalize="characters",
                    cls="room-code-input room-code-input--sm",
                ),
                Button("Join →", type="submit", cls="room-join-inline-btn"),
                action="/room/enter", method="post", cls="room-inline-form",
            ),
            id="join-room-bar", cls="room-inline-bar", style="display:none;",
        ),

        # ── Grid ──────────────────────────────────────────────────────────────
        Div(
            *[_cat_card(slug, icon, name, desc, color, i, disabled=no_tokens)
              for i, (slug, icon, name, desc, color) in enumerate(CATEGORIES)],
            cls="cat-grid",
            id="cat-grid",
        ),

        A("← Back to dashboard", href="/dashboard", cls="cat-back"),

        # ── Mode JS ───────────────────────────────────────────────────────────
        Script("""
(function(){
  window.setMode = function(mode) {
    ['solo','versus','private'].forEach(function(m){
      document.getElementById('btn-'+m).classList.toggle('mode-btn--active', m === mode);
    });
    var bar = document.getElementById('join-room-bar');
    if(bar) bar.style.display = mode === 'private' ? 'flex' : 'none';
    document.querySelectorAll('.cat-card[data-slug]').forEach(function(a) {
      if (!a.classList.contains('cat-card--disabled')) {
        var base = mode === 'private' ? '/room/create' : '/join';
        a.href = base + '?category=' + a.dataset.slug + (mode !== 'private' ? '&mode=' + mode : '');
      }
    });
  };
  setMode('solo');
})();
"""),

        cls="cat-page",
    )


def _cat_card(slug: str, icon: str, name: str, desc: str, color: str, idx: int, disabled: bool = False) -> FT:
    is_random = slug == "random"
    extra_cls = " cat-card--random" if is_random else ""
    extra_cls += " cat-card--disabled" if disabled else ""
    return A(
        Div(cls="cat-corner cat-tl"),
        Div(cls="cat-corner cat-br"),
        Span(f"{idx + 1:02d}", cls="cat-card-num"),
        Span(icon, cls="cat-card-icon"),
        Div(name, cls="cat-card-name", style=f"color:{color}"),
        Div(desc, cls="cat-card-desc"),
        Div(
            Span("⚡ -1" if not disabled else "NO ENERGY", cls="cat-card-cost"),
            Span("▶ ENTER" if not disabled else "LOCKED", cls="cat-card-enter"),
            cls="cat-card-footer",
        ),
        href="#" if disabled else f"/join?category={slug}&mode=solo",
        data_slug=slug,
        cls=f"cat-card{extra_cls}",
        style=f"--cat-color:{color}",
    )
