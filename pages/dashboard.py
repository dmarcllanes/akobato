from fasthtml.common import *
from components.verdicts import leaderboard_row

# Rank tiers based on score
RANKS = [
    (0,    "ROOKIE",     "#8b949e", "I"),
    (10,   "DEBATER",    "#3fb950", "II"),
    (30,   "AGITATOR",   "#05D9E8", "III"),
    (75,   "POLEMICIST", "#a371f7", "IV"),
    (150,  "RHETORICIAN","#FFC200", "V"),
    (300,  "SOPHIST",    "#FF2A6D", "VI"),
    (600,  "LEGEND",     "#ff9900", "VII"),
]

_MODES = [
    ("⚡", "QUICK MATCH",  "Random 1v1 · Instant matchmaking",   "#FF2A6D", "FASTEST",
     ["Paired with a random human opponent", "Random topic from breaking news", "AI judge declares the winner"],
     "FIND OPPONENT", "/join?category=random&mode=versus"),
    ("🎯", "PICK TOPIC",   "Choose your battlefield category",    "#a371f7", None,
     ["9 topic categories available", "Preview sample debate questions", "Works with Quick Match or Custom Room"],
     "BROWSE TOPICS",  "/play"),
    ("🔗", "CUSTOM ROOM",  "Private match · Invite your squad",   "#05D9E8", None,
     ["1v1, 2v2, or 3v3 team formats", "Shareable invite link or room code", "You pick the topic category"],
     "CREATE ROOM",    "/join-room"),
    ("🏆", "HALL OF FAME", "Global rankings · Top fighters",      "#FFC200", None,
     ["Top 50 players ranked by score", "See win rate, rank tier, and record", "Climb through 7 rank tiers to LEGEND"],
     "VIEW RANKINGS",  "/leaderboard"),
]


def _mode_slide(icon, name, tagline, color, badge, features, cta, href) -> FT:
    feat_els = [
        Div(
            Span("▸", style=f"color:{color}; margin-right:.42rem; flex-shrink:0;"),
            Span(f, cls="dm-feat-text"),
            cls="dm-feat",
        )
        for f in features
    ]
    badge_el = (
        Span(badge, cls="dm-badge",
             style=f"color:{color}; background:{color}1a; border:1px solid {color}44;")
        if badge else ()
    )
    return Div(
        A(
            Span(icon, cls="dm-ghost"),
            Div(
                badge_el,
                Div(name, cls="dm-name", style=f"color:{color};"),
                Div(tagline, cls="dm-tagline"),
                Div(*feat_els, cls="dm-feats"),
                Div(
                    Span(cta, cls="dm-cta-text"),
                    Span("→", cls="dm-cta-arr"),
                    cls="dm-cta",
                    style=f"color:{color}; border-color:{color}40;",
                ),
                cls="dm-body",
            ),
            href=href,
            cls="dm-card",
            style=f"border-left:3px solid {color};",
        ),
        cls="dm-slide",
    )


def _get_rank(score):
    rank = RANKS[0]
    for threshold, title, color, tier in RANKS:
        if score >= threshold:
            rank = (threshold, title, color, tier)
    return rank

def _xp_progress(score):
    """Returns (current_xp, next_threshold, pct) for the progress bar."""
    tier_idx = 0
    for i, (threshold, *_) in enumerate(RANKS):
        if score >= threshold:
            tier_idx = i
    current_threshold = RANKS[tier_idx][0]
    next_threshold    = RANKS[tier_idx + 1][0] if tier_idx + 1 < len(RANKS) else None
    if next_threshold is None:
        return score - current_threshold, 0, 100
    xp_in_tier  = score - current_threshold
    xp_needed   = next_threshold - current_threshold
    pct         = min(100, int(xp_in_tier / xp_needed * 100))
    return xp_in_tier, xp_needed, pct


def dashboard_page(username: str, stats: dict, top_players: list, alias: str = "") -> FT:
    display_name = alias or username
    wins     = stats.get("wins",   0)
    losses   = stats.get("losses", 0)
    ties     = stats.get("ties",   0)
    score    = stats.get("score",  0)
    tokens   = stats.get("tokens", 5)
    total    = wins + losses + ties
    win_rate = f"{int(wins / total * 100)}%" if total else "—"

    _, rank_title, rank_color, rank_tier = _get_rank(score)
    xp_in, xp_needed, xp_pct = _xp_progress(score)
    rank_idx  = next((i for i, (t,*_) in enumerate(RANKS) if score >= t), 0)
    next_rank = RANKS[rank_idx + 1][1] if rank_idx + 1 < len(RANKS) else "MAX"

    return Div(

        # ── Player card (top) ────────────────────────────────────────────────
        Div(
            # Left — avatar + identity
            Div(
                Div(
                    Img(src=f"/avatar/{username}", alt=display_name, cls="dash-avatar-img"),
                    Div(cls="dash-avatar-ring"),
                    cls="dash-avatar",
                ),
                Div(
                    Div("PLAYER", cls="dash-greeting"),
                    H1(display_name, cls="dash-username"),
                    Div(
                        Span(f"TIER {rank_tier}", cls="dash-tier-badge"),
                        Span(rank_title, cls="dash-rank-title", style=f"color:{rank_color}"),
                        cls="dash-rank-row",
                    ),
                    cls="dash-user-info",
                ),
                cls="dash-identity",
            ),

            # Right — XP bar + fight button
            Div(
                Div(
                    Div(
                        Span(f"XP  {xp_in}", cls="dash-xp-label"),
                        Span(f"NEXT RANK: {next_rank}", cls="dash-xp-next") if xp_needed else Span("MAX RANK", cls="dash-xp-next"),
                        cls="dash-xp-labels",
                    ),
                    Div(
                        Div(cls="dash-xp-fill", style=f"width:{xp_pct}%"),
                        cls="dash-xp-bar",
                    ),
                    cls="dash-xp-wrap",
                ),
                A(
                    Span("⚔"),
                    Span("FIGHT"),
                    href="/play",
                    cls="dash-fight-btn",
                ),
                cls="dash-hero-right",
            ),

            cls="dash-player-card",
        ),

        # ── Stats ────────────────────────────────────────────────────────────
        Div(
            _stat("🏅", "SCORE",    score,    ""),
            _stat("🏆", "WINS",     wins,     "stat-win"),
            _stat("💀", "LOSSES",   losses,   "stat-loss"),
            _stat("🤝", "TIES",     ties,     ""),
            _stat("🪙", "TOKENS",   f"{tokens}/5", f"stat-tokens{'--empty' if tokens == 0 else ''}"),
            cls="dash-stats",
        ),

        # ── Mode select carousel ─────────────────────────────────────────────
        Div(
            Div(Span("// SELECT MODE", cls="dash-section-tag"), cls="dm-header"),
            Div(
                Div(
                    *[_mode_slide(*m) for m in _MODES],
                    cls="dm-track",
                    id="dm-track",
                ),
                cls="dm-wrap",
            ),
            Div(
                Button("‹", type="button", cls="dm-nav-btn", id="dm-prev", onclick="dmStep(-1)"),
                Div(
                    *[Div(
                        cls=f"dm-dot{'  dm-dot--active' if i == 0 else ''}",
                        id=f"dm-dot-{i}",
                        onclick=f"dmGoTo({i})",
                    ) for i in range(len(_MODES))],
                    cls="dm-dots",
                ),
                Button("›", type="button", cls="dm-nav-btn", id="dm-next", onclick="dmStep(1)"),
                cls="dm-nav",
            ),
            Script(f"""
(function(){{
  var track = document.getElementById('dm-track');
  var total = {len(_MODES)};
  var cur   = 0;
  var COLS  = {[m[3] for m in _MODES]};

  function upDots() {{
    for(var i=0;i<total;i++){{
      var d=document.getElementById('dm-dot-'+i);
      if(!d) continue;
      d.classList.toggle('dm-dot--active', i===cur);
      d.style.background = i===cur ? COLS[cur] : '';
    }}
    document.getElementById('dm-prev').style.opacity = cur===0?'0.3':'1';
    document.getElementById('dm-next').style.opacity = cur===total-1?'0.3':'1';
  }}

  window.dmGoTo = function(idx){{
    cur = Math.max(0, Math.min(idx, total-1));
    track.style.transform = 'translateX(-'+(cur*100)+'%)';
    upDots();
  }};
  window.dmStep = function(d){{ window.dmGoTo(cur+d); }};

  // Touch/swipe
  var wrap=document.querySelector('.dm-wrap');
  var tx=0,ty=0,drag=false;
  wrap.addEventListener('touchstart',function(e){{tx=e.touches[0].clientX;ty=e.touches[0].clientY;drag=true;}},{{passive:true}});
  wrap.addEventListener('touchmove',function(e){{
    if(!drag)return;
    if(Math.abs(e.touches[0].clientX-tx)>Math.abs(e.touches[0].clientY-ty))e.preventDefault();
  }},{{passive:false}});
  wrap.addEventListener('touchend',function(e){{
    if(!drag)return;drag=false;
    var dx=e.changedTouches[0].clientX-tx,dy=Math.abs(e.changedTouches[0].clientY-ty);
    if(dy>50)return;
    if(dx<-40)window.dmGoTo(cur+1);else if(dx>40)window.dmGoTo(cur-1);
  }});

  upDots();
}})();
"""),
            cls="dm-section",
        ),

        # ── Top Fighters ─────────────────────────────────────────────────────
        Div(
            Div(
                Span("// TOP FIGHTERS", cls="dash-section-tag"),
                A("SEE ALL →", href="/leaderboard", cls="dash-table-link"),
                cls="dash-table-header",
            ),
            (
                Div(
                    Table(
                        Thead(Tr(Th("#"), Th("FIGHTER"), Th("W"), Th("L"), Th("T"), Th("SCORE"))),
                        Tbody(*[leaderboard_row(i + 1, r) for i, r in enumerate(top_players)]),
                        cls="dash-table",
                    ),
                    cls="dash-table-wrap",
                )
                if top_players else
                Div(
                    P("⚔", cls="dash-empty-icon"),
                    P("No fighters ranked yet.", cls="dash-empty-text"),
                    P("Be the first to claim the top spot.", cls="dash-empty-sub"),
                    cls="dash-empty",
                )
            ),
            cls="dash-leaderboard",
        ),

        cls="dashboard",
    )


def _stat(icon: str, label: str, value, cls_extra: str) -> FT:
    return Div(
        Span(icon, cls="dash-stat-icon"),
        Div(str(value), cls=f"dash-stat-value {cls_extra}".strip()),
        Div(label, cls="dash-stat-label"),
        cls="dash-stat-card",
    )
