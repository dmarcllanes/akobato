from fasthtml.common import *

# ── Category metadata ─────────────────────────────────────────────────────────
# Each entry: (slug, icon, name, tagline, color, [3 sample debate questions])
CATEGORIES = [
    (
        "world", "🌍", "WORLD NEWS", "Live breaking headlines", "#05D9E8",
        [
            "Should wealthy nations be legally required to accept climate refugees?",
            "Is the United Nations still relevant in today's world?",
            "Do open borders do more good than harm to society?",
        ],
    ),
    (
        "technology", "💻", "TECHNOLOGY", "AI · gadgets · startups", "#a371f7",
        [
            "Should there be a global pause on developing superintelligent AI?",
            "Does big tech have too much power over democracy?",
            "Should children under 16 be banned from all social media?",
        ],
    ),
    (
        "politics", "🏛️", "POLITICS", "Power · policy · debate", "#FF2A6D",
        [
            "Should voting be mandatory in all democracies?",
            "Should billionaires be required to give away most of their wealth?",
            "Is civil disobedience ever justified in a democracy?",
        ],
    ),
    (
        "sports", "⚽", "SPORTS", "Wins · trades · rivalry", "#3fb950",
        [
            "Should performance-enhancing drugs be legalised in pro sports?",
            "Is esports a real sport deserving Olympic inclusion?",
            "Has money ruined the spirit of football?",
        ],
    ),
    (
        "entertainment", "🎬", "ENTERTAINMENT", "Movies · music · celebs", "#FFC200",
        [
            "Are reboots and sequels killing Hollywood creativity?",
            "Is celebrity culture more harmful than inspiring?",
            "Has streaming killed the communal experience of cinema?",
        ],
    ),
    (
        "science", "🔬", "SCIENCE", "Space · breakthroughs", "#05D9E8",
        [
            "Should human genetic engineering be legal for non-medical use?",
            "Is nuclear energy the only realistic answer to climate change?",
            "Is the pursuit of immortality ethical?",
        ],
    ),
    (
        "business", "💰", "BUSINESS", "Markets · money · hustle", "#3fb950",
        [
            "Should a four-day work week be legally mandated?",
            "Is hustle culture destroying mental health?",
            "Should CEOs earn no more than 20× their lowest-paid employee?",
        ],
    ),
    (
        "gaming", "🎮", "GAMING", "Esports · games · culture", "#a371f7",
        [
            "Should loot boxes be classified and regulated as gambling?",
            "Has online multiplayer made gaming more toxic than enjoyable?",
            "Are video games genuinely art or just entertainment?",
        ],
    ),
    (
        "random", "🎲", "SURPRISE ME", "No prep. No excuses.", "#FFC200",
        [
            "You won't know the topic until the match starts.",
            "Any category, any question — pure instinct.",
            "Wildcards only. Bring your best argument.",
        ],
    ),
]


def category_page(username: str, tokens: int = 5) -> FT:
    no_tokens = tokens <= 0

    return Div(

        # ── Page title + energy ─────────────────────────────────────────────
        Div(
            Div(
                H1("Choose Your Arena", cls="wz-title"),
                P("Two steps to your next battle.", cls="wz-subtitle"),
            ),
            Div(
                Span("🪙", style="font-size:.9rem; filter:sepia(1) saturate(5) hue-rotate(-15deg) brightness(1.1) drop-shadow(0 0 5px rgba(255,194,0,.75));"),
                Span(f"{tokens}/5", style="font-weight:900; font-size:.85rem; color:#FFC200;"),
                Span("TOKENS", style=(
                    "font-size:.6rem; font-weight:700; letter-spacing:.1em;"
                    "color:rgba(255,194,0,.6); margin-left:.1rem;"
                )),
                *[Span(
                    cls=f"wz-energy-pip {'wz-energy-pip--on' if i < tokens else ''}",
                ) for i in range(5)],
                cls=f"wz-tokens {'wz-tokens--empty' if no_tokens else ''}",
            ),
            cls="wz-header",
        ),

        # ── No energy banner ────────────────────────────────────────────────
        (Div(
            Span("🪙", style="font-size:1.2rem; filter:sepia(1) saturate(5) hue-rotate(-15deg) brightness(1.1);"),
            Div(
                Div("NO TOKENS", style=(
                    "font-size:.72rem; font-weight:900; letter-spacing:.12em;"
                    "color:var(--brand-red);"
                )),
                Div("Finish a match to restore tokens.",
                    style="font-size:.78rem; color:var(--brand-muted); margin-top:.1rem;"),
            ),
            cls="wz-no-tokens",
        ) if no_tokens else ()),

        # ── Wizard stepper ──────────────────────────────────────────────────
        Div(
            Div(
                Div("1", cls="wz-step-num wz-step-num--active", id="step-num-1"),
                Div(
                    Div("GAME TYPE", cls="wz-step-label"),
                    Div("Quick Match or Custom Room", cls="wz-step-sub"),
                ),
                cls="wz-step wz-step--active",
                id="wz-step-1",
            ),
            Div(cls="wz-connector", id="wz-connector"),
            Div(
                Div("2", cls="wz-step-num", id="step-num-2"),
                Div(
                    Div("PICK TOPIC", cls="wz-step-label"),
                    Div("Choose your battlefield", cls="wz-step-sub"),
                ),
                cls="wz-step",
                id="wz-step-2",
            ),
            cls="wz-stepper",
        ),

        # ══ STEP 1 — Game Type ══════════════════════════════════════════════
        Div(
            # Quick Match card
            Div(
                Div(
                    Span("👥", cls="wz-mode-icon"),
                    Div(
                        Div("QUICK MATCH", cls="wz-mode-name"),
                        Div("2 MIN", cls="wz-mode-dur", style="color:#a371f7;"),
                        cls="wz-mode-meta",
                    ),
                    cls="wz-mode-top",
                ),
                Div("Random human opponent · matchmaking queue", cls="wz-mode-desc"),
                Div(
                    Div(cls="wz-mode-check-dot", style="background:#a371f7; box-shadow:0 0 6px #a371f7;"),
                    Span("SELECTED", cls="wz-mode-check-label", style="color:#a371f7;"),
                    cls="wz-mode-check",
                ),
                id="mode-versus",
                cls="wz-mode-card wz-mode-card--active",
                data_mode="versus",
                onclick="pickMode('versus')",
            ),
            # Custom Room card — direct link, no Step 2
            A(
                Div(
                    Span("🔗", cls="wz-mode-icon"),
                    Div(
                        Div("CUSTOM ROOM", cls="wz-mode-name"),
                        Div("2 MIN", cls="wz-mode-dur", style="color:#05D9E8;"),
                        cls="wz-mode-meta",
                    ),
                    cls="wz-mode-top",
                ),
                Div("Set teams · pick topic · invite friends", cls="wz-mode-desc"),
                href="/join-room",
                id="mode-private",
                cls="wz-mode-card",
                data_mode="private",
            ),
            cls="wz-modes",
            id="wz-panel-1",
        ),

        # ══ STEP 2 — Topic Carousel ══════════════════════════════════════════
        Div(
            # Mode reminder banner
            Div(id="wz-mode-banner", cls="wz-mode-banner"),

            # Carousel
            Div(
                # Slides track
                Div(
                    *[_carousel_card(slug, icon, name, tagline, color, samples, disabled=no_tokens)
                      for slug, icon, name, tagline, color, samples in CATEGORIES],
                    cls="cs-track",
                    id="cs-track",
                ),
                cls="cs-track-wrap",
                id="cs-track-wrap",
            ),

            # Navigation row: prev · dots · next
            Div(
                # Prev button
                Button(
                    "‹",
                    type="button",
                    cls="cs-nav-btn cs-prev",
                    id="cs-prev",
                    onclick="csStep(-1)",
                    aria_label="Previous topic",
                ),
                # Dots
                Div(
                    *[Div(
                        cls=f"cs-dot{'  cs-dot--active' if i == 0 else ''}",
                        data_idx=str(i),
                        onclick=f"csGoTo({i})",
                    ) for i in range(len(CATEGORIES))],
                    cls="cs-dots",
                    id="cs-dots",
                ),
                # Next button
                Button(
                    "›",
                    type="button",
                    cls="cs-nav-btn cs-next",
                    id="cs-next",
                    onclick="csStep(1)",
                    aria_label="Next topic",
                ),
                cls="cs-nav",
            ),

            id="wz-panel-2",
            cls="wz-panel-2",
        ),

        A("← Dashboard", href="/dashboard", cls="cat-back", style="margin-top:1rem;"),

        Script(f"""
(function(){{

  /* ── mode meta ─────────────────────────────────────────── */
  var MODE_META = {{
    versus: {{
      icon:'👥', label:'QUICK MATCH', dur:'2 MIN',
      desc:'Random human opponent',
      color:'#a371f7',
      base:'/join', qs:'&mode=versus'
    }},
  }};

  /* ── step-2 reveal ─────────────────────────────────────── */
  function revealStep2() {{
    var p2   = document.getElementById('wz-panel-2');
    var s2   = document.getElementById('wz-step-2');
    var n2   = document.getElementById('step-num-2');
    var conn = document.getElementById('wz-connector');
    if(p2)   p2.classList.add('wz-panel-2--visible');
    if(s2)   s2.classList.add('wz-step--active');
    if(n2)   n2.classList.add('wz-step-num--active');
    if(conn) conn.classList.add('wz-connector--done');
    setTimeout(function(){{
      if(p2) p2.scrollIntoView({{ behavior:'smooth', block:'start' }});
    }}, 120);
  }}

  /* ── mode banner ────────────────────────────────────────── */
  function updateBanner(mode) {{
    var m  = MODE_META[mode];
    var el = document.getElementById('wz-mode-banner');
    if(!el || !m) return;
    el.innerHTML =
      '<span style="font-size:1rem">' + m.icon + '</span> ' +
      '<strong style="color:' + m.color + ';letter-spacing:.05em">' + m.label + '</strong>' +
      '<span class="wz-dur-badge" style="background:' + m.color + '22;color:' + m.color + '">' + m.dur + '</span>' +
      '<span style="color:var(--brand-muted);font-size:.8rem">' + m.desc + '</span>' +
      '<span style="margin-left:auto;color:var(--brand-muted);font-size:.75rem">→ swipe or click a card</span>';
    el.style.borderLeftColor = m.color;
  }}

  /* ── card href update ───────────────────────────────────── */
  function updateCards(mode) {{
    var m = MODE_META[mode];
    if(!m) return;
    document.querySelectorAll('.cs-card[data-slug]').forEach(function(card){{
      if(card.dataset.disabled === 'true') return;
      var slug = card.dataset.slug;
      var btn  = card.querySelector('.cs-play-btn');
      if(btn) btn.href = m.base + '?category=' + slug + m.qs;
    }});
  }}

  window.pickMode = function(mode) {{
    document.querySelectorAll('.wz-mode-card').forEach(function(c){{
      c.classList.toggle('wz-mode-card--active', c.dataset.mode === mode);
    }});
    if(MODE_META[mode]) {{
      updateBanner(mode);
      updateCards(mode);
      revealStep2();
    }}
  }};

  /* ══ Carousel ═════════════════════════════════════════════ */
  var track    = document.getElementById('cs-track');
  var dotsWrap = document.getElementById('cs-dots');
  var total    = {len(CATEGORIES)};
  var current  = 0;

  function csGoTo(idx) {{
    current = Math.max(0, Math.min(idx, total - 1));
    track.style.transform = 'translateX(-' + (current * 100) + '%)';
    dotsWrap.querySelectorAll('.cs-dot').forEach(function(d, i) {{
      d.classList.toggle('cs-dot--active', i === current);
    }});
    // Update prev/next visibility
    document.getElementById('cs-prev').style.opacity = current === 0 ? '0.3' : '1';
    document.getElementById('cs-next').style.opacity = current === total - 1 ? '0.3' : '1';
  }}

  window.csGoTo = csGoTo;
  window.csStep = function(dir) {{ csGoTo(current + dir); }};

  /* ── touch / swipe ─────────────────────────────────────── */
  var touchStartX = 0;
  var touchStartY = 0;
  var isDragging  = false;
  var wrap = document.getElementById('cs-track-wrap');

  wrap.addEventListener('touchstart', function(e) {{
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
    isDragging  = true;
  }}, {{ passive: true }});

  wrap.addEventListener('touchmove', function(e) {{
    if(!isDragging) return;
    var dx = Math.abs(e.touches[0].clientX - touchStartX);
    var dy = Math.abs(e.touches[0].clientY - touchStartY);
    if(dx > dy) e.preventDefault();   // horizontal — block page scroll
  }}, {{ passive: false }});

  wrap.addEventListener('touchend', function(e) {{
    if(!isDragging) return;
    isDragging = false;
    var dx = e.changedTouches[0].clientX - touchStartX;
    var dy = Math.abs(e.changedTouches[0].clientY - touchStartY);
    if(dy > 60) return;               // mainly vertical — ignore
    if(dx < -44) csGoTo(current + 1);
    else if(dx >  44) csGoTo(current - 1);
  }});

  /* ── keyboard navigation ───────────────────────────────── */
  document.addEventListener('keydown', function(e) {{
    var p2 = document.getElementById('wz-panel-2');
    if(!p2 || !p2.classList.contains('wz-panel-2--visible')) return;
    if(e.key === 'ArrowLeft')  csGoTo(current - 1);
    if(e.key === 'ArrowRight') csGoTo(current + 1);
  }});

  /* ── init ──────────────────────────────────────────────── */
  updateCards('versus');
  csGoTo(0);

}})();
"""),

        cls="wz-page",
    )


def _carousel_card(slug: str, icon: str, name: str, tagline: str,
                   color: str, samples: list, disabled: bool = False) -> FT:
    """Full-width carousel card for one topic category."""
    is_random = slug == "random"

    # Sample question rows
    sample_rows = [
        Div(
            Span("›", style=f"color:{color}; font-weight:900; flex-shrink:0;"),
            Span(q, cls="cs-sample-text"),
            cls="cs-sample-row",
        )
        for q in samples
    ]

    play_btn = (
        A(
            Span("🔒", style="font-size:.9rem;"),
            Span("NO TOKENS"),
            cls="cs-play-btn cs-play-btn--locked",
            href="#",
        ) if disabled else A(
            Span("▶"),
            Span("PLAY THIS TOPIC"),
            cls="cs-play-btn",
            href=f"/join?category={slug}&mode=versus",  # updated by JS on mode pick
        )
    )

    return Div(
        Div(
            # ── Card header ─────────────────────────────────
            Div(
                Span(icon, cls="cs-card-icon"),
                Div(
                    Div(name, cls="cs-card-name", style=f"color:{color}"),
                    Div(tagline, cls="cs-card-tagline"),
                    cls="cs-card-header-text",
                ),
                cls="cs-card-header",
            ),

            # ── Divider ──────────────────────────────────────
            Div(cls="cs-divider", style=f"background: linear-gradient(90deg, {color}55, transparent);"),

            # ── Sample questions ─────────────────────────────
            Div(
                Div(
                    "🎯 WHAT YOU MIGHT DEBATE" if not is_random else "🎲 THE UNKNOWN",
                    cls="cs-samples-label",
                ),
                *sample_rows,
                cls="cs-samples",
            ),

            # ── Play button ──────────────────────────────────
            Div(
                play_btn,
                cls="cs-card-footer",
            ),

            cls="cs-card-inner",
            style=f"--cs-color:{color};",
        ),
        cls="cs-card",
        data_slug=slug,
        data_disabled="true" if disabled else "false",
    )
