from fasthtml.common import *
from models.schemas import JudgeVerdict, MatchState


def verdict_component(match: MatchState, username: str) -> FT:
    """Full verdict display — replaces the submit-area div."""
    v = match.verdict
    if v is None:
        return Div(P("Verdict loading...", cls="status-waiting"), id="submit-area")

    # Resolve winner display name
    if v.winner == "Player 1":
        winner_name = match.player1
    elif v.winner == "Player 2":
        winner_name = match.player2 or "Player 2"
    else:
        winner_name = "Nobody — it's a Tie!"

    you_won = (v.winner == match.player_label(username))
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

    your_score = (
        v.human_originality_score_p1
        if match.player_label(username) == "Player 1"
        else v.human_originality_score_p2
    )
    opp_score = (
        v.human_originality_score_p2
        if match.player_label(username) == "Player 1"
        else v.human_originality_score_p1
    )
    opponent = match.opponent_of(username) or "Opponent"

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
        A("⚔️ Fight Again", href="/", cls="play-again-btn"),
        id="submit-area",
    )


def leaderboard_row(rank: int, record: dict) -> FT:
    medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, str(rank))
    return Tr(
        Td(Span(medal, cls="rank-badge")),
        Td(Strong(record.get("username", "??"))),
        Td(Span(str(record.get("wins", 0)), cls="tag-win")),
        Td(Span(str(record.get("losses", 0)), cls="tag-lose")),
        Td(Span(str(record.get("ties", 0)), cls="tag-tie")),
        Td(Strong(str(record.get("score", 0)))),
    )
