from fasthtml.common import *
from models.schemas import JudgeVerdict, MatchState


def verdict_component(match: MatchState, username: str) -> FT:
    """Full verdict display — replaces the submit-area div."""
    v = match.verdict
    if v is None:
        return Div(P("Verdict loading...", cls="status-waiting"), id="submit-area")

    # Resolve winner display name using aliases (never real usernames)
    if v.winner == "Team A":
        aliases = match.team_aliases(1)
        winner_name = aliases[0] if len(aliases) == 1 else " & ".join(aliases)
    elif v.winner == "Team B":
        aliases = match.team_aliases(2)
        winner_name = aliases[0] if len(aliases) == 1 else " & ".join(aliases)
    else:
        winner_name = "Nobody — it's a Tie!"

    my_team = match.player_team(username)
    you_won  = my_team is not None and v.winner == match.team_label(my_team)
    you_tied = v.winner == "Tie"

    if you_won:
        outcome_msg = "🏆 You Won!"
        outcome_color = "var(--brand-gold)"
    elif you_tied:
        outcome_msg = "🤝 It's a Tie"
        outcome_color = "var(--brand-muted)"
    else:
        outcome_msg = "💀 You Lost"
        outcome_color = "var(--brand-red)"

    your_score = v.human_originality_score_p1 if my_team == 1 else v.human_originality_score_p2
    opp_score  = v.human_originality_score_p2 if my_team == 1 else v.human_originality_score_p1
    opponent   = match.opponent_alias_of(username)

    return Div(
        # Replace timer + form area with this full verdict card
        Div(
            Div(
                P(
                    outcome_msg,
                    style=f"font-size: 1.5rem; font-weight: 900; color: {outcome_color}; margin: 0;",
                ),
                P(
                    f"Winner: {winner_name}",
                    cls="verdict-winner",
                ),
                P(
                    f'"{v.winning_quote}"' if v.winning_quote else "",
                    cls="verdict-quote",
                ),
                cls="verdict-header",
            ),
            Div(
                P(Strong("🧑‍⚖️ The Judge says: "), v.reasoning),
                cls="verdict-reasoning",
            ),
            Div(
                Div(
                    P("Your Originality", cls="score-label"),
                    P(f"{your_score}/10", cls="score-value"),
                    cls="score-block",
                ),
                Div(
                    P(f"{opponent}'s Originality", cls="score-label"),
                    P(f"{opp_score}/10", cls="score-value"),
                    cls="score-block",
                ),
                cls="scores-row",
            ),
            cls="verdict-card card",
        ),
        Div(
            A("⚔️ Find New Match", href="/play", cls="play-again-btn"),
            A("🏠 Dashboard", href="/dashboard", cls="play-again-btn",
              style="background:rgba(255,255,255,.08); color:var(--fg); border:1px solid rgba(255,255,255,.15);"),
            style="display:flex; gap:.75rem; flex-wrap:wrap; justify-content:center;",
        ),
        Script(f"""
(function(){{
  if(!window.SFX) return;
  var outcome = '{("win" if you_won else ("tie" if you_tied else "lose"))}';
  setTimeout(function(){{
    if(outcome === 'win')       SFX.win();
    else if(outcome === 'tie') SFX.tie();
    else                       SFX.lose();
  }}, 200);
}})();
"""),
        id="submit-area",
    )


def leaderboard_row(rank: int, record: dict) -> FT:
    medal    = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "")
    top3     = rank <= 3
    row_cls  = f"lb-row {'lb-row--top' if top3 else ''} lb-row--{rank if top3 else 'rest'}"

    wins   = record.get("wins", 0) or 0
    losses = record.get("losses", 0) or 0
    ties   = record.get("ties", 0) or 0
    score  = record.get("score", 0) or 0
    name   = record.get("username", "??")

    rank_cell = Td(
        Span(medal or str(rank), cls="lb-rank"),
        cls="lb-td lb-td--rank",
    )
    name_cell = Td(
        Span(name, cls="lb-name"),
        cls="lb-td lb-td--name",
    )

    return Tr(
        rank_cell,
        name_cell,
        Td(Span(str(wins),   cls="lb-stat lb-stat--win"),  cls="lb-td lb-td--stat"),
        Td(Span(str(losses), cls="lb-stat lb-stat--lose"), cls="lb-td lb-td--stat"),
        Td(Span(str(ties),   cls="lb-stat lb-stat--tie"),  cls="lb-td lb-td--stat"),
        Td(Span(str(score),  cls="lb-score"),              cls="lb-td lb-td--score"),
        cls=row_cls,
    )
