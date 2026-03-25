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

        # ── Grid ──────────────────────────────────────────────────────────────
        Div(
            *[_cat_card(slug, icon, name, desc, color, i, disabled=no_tokens)
              for i, (slug, icon, name, desc, color) in enumerate(CATEGORIES)],
            cls="cat-grid",
        ),

        A("← Back to dashboard", href="/dashboard", cls="cat-back"),

        cls="cat-page",
    )


def _cat_card(slug: str, icon: str, name: str, desc: str, color: str, idx: int, disabled: bool = False) -> FT:
    is_random = slug == "random"
    extra_cls = " cat-card--random" if is_random else ""
    extra_cls += " cat-card--disabled" if disabled else ""
    return A(
        # Corner brackets
        Div(cls="cat-corner cat-tl"),
        Div(cls="cat-corner cat-br"),

        # Index number
        Span(f"{idx + 1:02d}", cls="cat-card-num"),

        # Content
        Span(icon, cls="cat-card-icon"),
        Div(name, cls="cat-card-name", style=f"color:{color}"),
        Div(desc, cls="cat-card-desc"),

        # Footer
        Div(
            Span("⚡ -1" if not disabled else "NO ENERGY", cls="cat-card-cost"),
            Span("▶ ENTER" if not disabled else "LOCKED", cls="cat-card-enter"),
            cls="cat-card-footer",
        ),

        href="#" if disabled else f"/join?category={slug}",
        cls=f"cat-card{extra_cls}",
        style=f"--cat-color:{color}",
    )
