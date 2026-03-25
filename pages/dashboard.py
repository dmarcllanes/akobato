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
            _stat("⚡", "ENERGY",   f"{tokens}/5", f"stat-tokens{'--empty' if tokens == 0 else ''}"),
            cls="dash-stats",
        ),

        # ── Mode select ──────────────────────────────────────────────────────
        Div(
            Span("// SELECT MODE", cls="dash-section-tag"),
            Div(
                # Quick fight
                A(
                    Div(
                        Div(
                            Span("⚡", cls="dash-mode-icon"),
                            Div(
                                Div("QUICK FIGHT", cls="dash-mode-name"),
                                Div("Random topic · instant match", cls="dash-mode-sub"),
                                cls="dash-mode-text",
                            ),
                            cls="dash-mode-top",
                        ),
                        Div(
                            Span("PRESS START", cls="dash-mode-press"),
                            cls="dash-mode-footer",
                        ),
                        cls="dash-mode-inner",
                    ),
                    href="/join?category=random",
                    cls="dash-mode-card dash-mode-card--hot",
                ),
                # Choose category
                A(
                    Div(
                        Div(
                            Span("🎯", cls="dash-mode-icon"),
                            Div(
                                Div("PICK TOPIC", cls="dash-mode-name"),
                                Div("Choose your battlefield", cls="dash-mode-sub"),
                                cls="dash-mode-text",
                            ),
                            cls="dash-mode-top",
                        ),
                        Div(
                            Span("SELECT →", cls="dash-mode-press"),
                            cls="dash-mode-footer",
                        ),
                        cls="dash-mode-inner",
                    ),
                    href="/play",
                    cls="dash-mode-card",
                ),
                # Leaderboard
                A(
                    Div(
                        Div(
                            Span("🏆", cls="dash-mode-icon"),
                            Div(
                                Div("HALL OF FAME", cls="dash-mode-name"),
                                Div("Global rankings", cls="dash-mode-sub"),
                                cls="dash-mode-text",
                            ),
                            cls="dash-mode-top",
                        ),
                        Div(
                            Span("VIEW →", cls="dash-mode-press"),
                            cls="dash-mode-footer",
                        ),
                        cls="dash-mode-inner",
                    ),
                    href="/leaderboard",
                    cls="dash-mode-card",
                ),
                cls="dash-modes",
            ),
            cls="dash-modes-section",
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
