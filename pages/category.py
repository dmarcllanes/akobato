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

_MODES = [
    (
        "versus",
        "👥",
        "QUICK MATCH",
        "2 MIN",
        "Random human opponent · matchmaking queue",
        "#a371f7",
        "/join",
        "&mode=versus",
    ),
    (
        "private",
        "🔗",
        "PLAY WITH FRIEND",
        "2 MIN",
        "Invite a specific person · shareable link",
        "#05D9E8",
        "/room/create",
        "",
    ),
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
            *[Span(cls=f"cat-token-pip {'cat-token-pip--on' if i < tokens else ''}", key=i)
              for i in range(5)],
            cls="cat-token-pips",
        ),
        cls=f"cat-token-bar {'cat-token-bar--empty' if no_tokens else ''}",
    )

    no_tokens_banner = Div(
        Span("⚡", cls="cat-no-tokens-icon"),
        Div(
            Div("NO ENERGY", cls="cat-no-tokens-title"),
            Div("Complete a match to restore energy.", cls="cat-no-tokens-sub"),
            cls="cat-no-tokens-text",
        ),
        cls="cat-no-tokens-banner",
    ) if no_tokens else ()

    return Div(

        # ── Header ────────────────────────────────────────────────────────────
        Div(
            H1("Choose Your Arena", cls="cat-title", style="margin-bottom:.25rem;"),
            token_bar,
            cls="cat-header",
        ),

        no_tokens_banner,

        # ══ STEP 1 — Game Type ════════════════════════════════════════════════
        Div(
            Div(
                Span("STEP 1", style=(
                    "font-size:.65rem; font-weight:900; letter-spacing:.15em;"
                    "color:var(--brand-cyan); background:rgba(5,217,232,.12);"
                    "padding:.2rem .6rem; border-radius:4px;"
                )),
                Span("Choose Game Type", style=(
                    "font-size:.9rem; font-weight:700; color:var(--fg); margin-left:.6rem;"
                )),
                style="display:flex; align-items:center; margin-bottom:.85rem;",
            ),

            Div(
                *[_mode_card(slug, icon, label, dur, desc, color)
                  for slug, icon, label, dur, desc, color, _, __ in _MODES],
                cls="arena-modes",
                id="mode-selector",
            ),

            style="margin-bottom:1.5rem;",
        ),

        # ══ STEP 2 — Topic ════════════════════════════════════════════════════
        Div(
            Div(
                Span("STEP 2", style=(
                    "font-size:.65rem; font-weight:900; letter-spacing:.15em;"
                    "color:var(--brand-cyan); background:rgba(5,217,232,.12);"
                    "padding:.2rem .6rem; border-radius:4px;"
                )),
                Span("Pick a Topic", style=(
                    "font-size:.9rem; font-weight:700; color:var(--fg); margin-left:.6rem;"
                )),
                style="display:flex; align-items:center; margin-bottom:.75rem;",
            ),

            # Live mode summary banner
            Div(id="mode-banner", style="margin-bottom:.85rem;"),

            Div(
                *[_cat_card(slug, icon, name, desc, color, disabled=no_tokens)
                  for slug, icon, name, desc, color in CATEGORIES],
                cls="cat-grid",
                id="cat-grid",
            ),

            style="margin-bottom:1.5rem;",
        ),

        A("← Dashboard", href="/dashboard", cls="cat-back"),

        Script("""
(function(){
  var MODE_META = {
    versus:  {
      icon:'👥', label:'QUICK MATCH',       dur:'2 MIN',
      desc:'Random human opponent',         color:'#a371f7',
      base:'/join',        qs:'&mode=versus'
    },
    private: {
      icon:'🔗', label:'PLAY WITH FRIEND',  dur:'2 MIN',
      desc:'Invite a specific person',      color:'#05D9E8',
      base:'/room/create', qs:''
    },
  };

  var current = 'versus';

  function updateBanner(mode) {
    var m  = MODE_META[mode];
    var el = document.getElementById('mode-banner');
    if (!el) return;
    el.innerHTML = [
      '<div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;',
      'background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);',
      'border-left:3px solid '+m.color+';',
      'border-radius:8px;padding:.65rem 1rem;font-size:.82rem;">',
        '<span style="font-size:1.1rem">'+m.icon+'</span>',
        '<strong style="color:'+m.color+';letter-spacing:.05em">'+m.label+'</strong>',
        '<span style="background:'+m.color+'22;color:'+m.color+';font-size:.68rem;font-weight:700;',
        'padding:.15rem .5rem;border-radius:4px;letter-spacing:.08em">'+m.dur+'</span>',
        '<span style="color:var(--brand-muted)">'+m.desc+'</span>',
        '<span style="margin-left:auto;color:var(--brand-muted);font-size:.75rem">',
        '→ click a topic to start</span>',
      '</div>',
    ].join('');
  }

  function updateCards(mode) {
    var m = MODE_META[mode];
    document.querySelectorAll('.cat-card[data-slug]').forEach(function(a) {
      if (a.classList.contains('cat-card--disabled')) return;
      a.href = m.base + '?category=' + a.dataset.slug + m.qs;
      var badge = a.querySelector('.cat-mode-badge');
      if (badge) {
        badge.textContent = m.icon + ' ' + m.label + ' · ' + m.dur;
        badge.style.color        = m.color;
        badge.style.borderColor  = m.color + '55';
        badge.style.background   = m.color + '11';
      }
    });
  }

  window.setMode = function(mode) {
    current = mode;
    document.querySelectorAll('.arena-mode-card').forEach(function(c) {
      c.classList.toggle('arena-mode-card--active', c.dataset.mode === mode);
    });
    updateBanner(mode);
    updateCards(mode);
  };

  setMode('versus');
})();
"""),

        cls="cat-page",
    )


def _mode_card(slug: str, icon: str, label: str, dur: str, desc: str, color: str) -> FT:
    return Div(
        Div(
            Span(icon, style="font-size:1.5rem; line-height:1;"),
            Div(
                Div(label, style="font-weight:900; font-size:.85rem; letter-spacing:.06em;"),
                Div(dur, style=(
                    f"font-size:.68rem; font-weight:700; letter-spacing:.1em;"
                    f"color:{color}; margin-top:.1rem;"
                )),
                style="display:flex; flex-direction:column;",
            ),
            style="display:flex; align-items:center; gap:.65rem; margin-bottom:.35rem;",
        ),
        Div(desc, style="font-size:.75rem; color:var(--brand-muted); line-height:1.3;"),
        Div(
            Div(style=(
                f"width:8px; height:8px; border-radius:50%;"
                f"background:{color}; box-shadow:0 0 6px {color};"
            )),
            Span("SELECTED", style=(
                f"font-size:.6rem; font-weight:900; letter-spacing:.1em; color:{color};"
            )),
            cls="arena-mode-check",
        ),
        cls="arena-mode-card",
        data_mode=slug,
        onclick=f"setMode('{slug}')",
    )


def _cat_card(slug: str, icon: str, name: str, desc: str, color: str, disabled: bool = False) -> FT:
    is_random = slug == "random"
    extra_cls = " cat-card--random" if is_random else ""
    extra_cls += " cat-card--disabled" if disabled else ""
    return A(
        Div(cls="cat-corner cat-tl"),
        Div(cls="cat-corner cat-br"),
        Span(icon, cls="cat-card-icon"),
        Div(name, cls="cat-card-name", style=f"color:{color}"),
        Div(desc, cls="cat-card-desc"),
        Div(
            Span(
                "👥 QUICK MATCH · 2 MIN",
                cls="cat-mode-badge",
                style="color:#a371f7; border:1px solid #a371f755; background:#a371f711;",
            ) if not disabled else Span(
                "NO ENERGY",
                style="color:var(--brand-red); font-size:.72rem; font-weight:700;",
            ),
            Span("▶ START" if not disabled else "LOCKED", cls="cat-card-enter"),
            cls="cat-card-footer",
        ),
        href="#" if disabled else f"/join?category={slug}&mode=versus",
        data_slug=slug,
        cls=f"cat-card{extra_cls}",
        style=f"--cat-color:{color}",
    )
