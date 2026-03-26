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

    return Div(

        # ── Page title + energy ───────────────────────────────────────────────
        Div(
            Div(
                H1("Choose Your Arena", cls="wz-title"),
                P("Two steps to your next battle.", cls="wz-subtitle"),
            ),
            # Energy pill
            Div(
                Span("⚡", style="font-size:.9rem;"),
                Span(f"{tokens}/5", style="font-weight:900; font-size:.85rem;"),
                Span("ENERGY", style=(
                    "font-size:.6rem; font-weight:700; letter-spacing:.1em;"
                    "color:var(--brand-muted); margin-left:.1rem;"
                )),
                *[Span(
                    cls=f"wz-energy-pip {'wz-energy-pip--on' if i < tokens else ''}",
                ) for i in range(5)],
                cls=f"wz-energy {'wz-energy--empty' if no_tokens else ''}",
            ),
            cls="wz-header",
        ),

        # ── No energy banner ──────────────────────────────────────────────────
        (Div(
            Span("⚡", style="font-size:1.2rem;"),
            Div(
                Div("NO ENERGY", style=(
                    "font-size:.72rem; font-weight:900; letter-spacing:.12em;"
                    "color:var(--brand-red);"
                )),
                Div("Finish a match to restore energy.",
                    style="font-size:.78rem; color:var(--brand-muted); margin-top:.1rem;"),
            ),
            cls="wz-no-energy",
        ) if no_tokens else ()),

        # ── Wizard stepper ────────────────────────────────────────────────────
        Div(
            # Step 1
            Div(
                Div("1", cls="wz-step-num wz-step-num--active", id="step-num-1"),
                Div(
                    Div("GAME TYPE", cls="wz-step-label"),
                    Div("Quick Match or Custom Room", cls="wz-step-sub"),
                ),
                cls="wz-step wz-step--active",
                id="wz-step-1",
            ),
            # Connector
            Div(cls="wz-connector", id="wz-connector"),
            # Step 2
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

        # ══ STEP 1 — Game Type ════════════════════════════════════════════════
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
                Div("Random human opponent · matchmaking queue",
                    cls="wz-mode-desc"),
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
            # Custom Room card — direct link, no Step 2 needed
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
                Div("Set teams · pick topic · invite friends",
                    cls="wz-mode-desc"),
                href="/join-room",
                id="mode-private",
                cls="wz-mode-card",
                data_mode="private",
            ),
            cls="wz-modes",
            id="wz-panel-1",
        ),

        # ══ STEP 2 — Topic ════════════════════════════════════════════════════
        Div(
            # Selected mode reminder banner
            Div(id="wz-mode-banner", cls="wz-mode-banner"),

            # Topic grid
            Div(
                *[_cat_card(slug, icon, name, desc, color, disabled=no_tokens)
                  for slug, icon, name, desc, color in CATEGORIES],
                cls="wz-cat-grid",
                id="wz-cat-grid",
            ),

            id="wz-panel-2",
            cls="wz-panel-2",
        ),

        A("← Dashboard", href="/dashboard", cls="cat-back", style="margin-top:1rem;"),

        Script("""
(function(){

  var MODE_META = {
    versus: {
      icon:'👥', label:'QUICK MATCH', dur:'2 MIN',
      desc:'Random human opponent',
      color:'#a371f7',
      base:'/join', qs:'&mode=versus'
    },
  };

  function updateBanner(mode) {
    var m  = MODE_META[mode];
    var el = document.getElementById('wz-mode-banner');
    if(!el || !m) return;
    el.innerHTML =
      '<span style="font-size:1rem">'+m.icon+'</span> ' +
      '<strong style="color:'+m.color+';letter-spacing:.05em">'+m.label+'</strong>' +
      '<span class="wz-dur-badge" style="background:'+m.color+'22;color:'+m.color+'">'+m.dur+'</span>' +
      '<span style="color:var(--brand-muted);font-size:.8rem">'+m.desc+'</span>' +
      '<span style="margin-left:auto;color:var(--brand-muted);font-size:.75rem">→ click a topic</span>';
    el.style.borderLeftColor = m.color;
  }

  function updateCards(mode) {
    var m = MODE_META[mode];
    if(!m) return;
    document.querySelectorAll('.wz-cat-card[data-slug]').forEach(function(a){
      if(a.classList.contains('wz-cat-card--disabled')) return;
      a.href = m.base + '?category=' + a.dataset.slug + m.qs;
      var badge = a.querySelector('.wz-cat-badge');
      if(badge){
        badge.textContent = m.icon + ' ' + m.label;
        badge.style.color       = m.color;
        badge.style.borderColor = m.color + '55';
        badge.style.background  = m.color + '11';
      }
    });
  }

  function revealStep2() {
    var p2 = document.getElementById('wz-panel-2');
    if(!p2) return;
    p2.classList.add('wz-panel-2--visible');

    // Advance stepper visuals
    var s2 = document.getElementById('wz-step-2');
    var n2 = document.getElementById('step-num-2');
    var conn = document.getElementById('wz-connector');
    if(s2)   s2.classList.add('wz-step--active');
    if(n2)   n2.classList.add('wz-step-num--active');
    if(conn) conn.classList.add('wz-connector--done');

    // Scroll to step 2
    setTimeout(function(){
      p2.scrollIntoView({ behavior:'smooth', block:'start' });
    }, 120);
  }

  window.pickMode = function(mode) {
    // Update mode card highlight
    document.querySelectorAll('.wz-mode-card').forEach(function(c){
      c.classList.toggle('wz-mode-card--active', c.dataset.mode === mode);
    });

    if(MODE_META[mode]) {
      updateBanner(mode);
      updateCards(mode);
      revealStep2();
    }
  };

  // Initialise: pre-select versus so Step 2 cards have correct hrefs
  updateCards('versus');
  // Step 2 starts hidden — only revealed after mode pick
})();
"""),

        cls="wz-page",
    )


def _cat_card(slug: str, icon: str, name: str, desc: str,
              color: str, disabled: bool = False) -> FT:
    extra = " wz-cat-card--disabled" if disabled else ""
    extra += " wz-cat-card--random"  if slug == "random" else ""
    return A(
        Span(icon, cls="wz-cat-icon"),
        Div(
            Div(name, cls="wz-cat-name", style=f"color:{color}"),
            Div(desc, cls="wz-cat-desc"),
        ),
        Div(
            Span(
                f"👥 QUICK MATCH",
                cls="wz-cat-badge",
                style=f"color:#a371f7; border:1px solid #a371f755; background:#a371f711;",
            ) if not disabled else Span(
                "NO ENERGY",
                style="color:var(--brand-red); font-size:.7rem; font-weight:700;",
            ),
            Span("▶" if not disabled else "🔒", cls="wz-cat-arrow"),
            cls="wz-cat-footer",
        ),
        href="#" if disabled else f"/join?category={slug}&mode=versus",
        data_slug=slug,
        cls=f"wz-cat-card{extra}",
        style=f"--wz-color:{color}",
    )
