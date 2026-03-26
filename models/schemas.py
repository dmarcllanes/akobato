from pydantic import BaseModel, Field
from typing import Optional
import time


class JudgeVerdict(BaseModel):
    winner: str  # "Player 1", "Player 2", or "Tie"
    human_originality_score_p1: int = Field(ge=1, le=10)
    human_originality_score_p2: int = Field(ge=1, le=10)
    reasoning: str  # Sassy, witty explanation
    winning_quote: str  # Best sentence from winner (empty string if Tie)


class MatchState:
    DURATION = 60  # seconds

    def __init__(self, match_id: str, prompt: str, player1: str):
        self.match_id = match_id
        self.prompt = prompt
        self.player1 = player1
        self.player2: Optional[str] = None
        self.alias1: Optional[str] = None   # public display name for player1
        self.alias2: Optional[str] = None   # public display name for player2
        self.argument1: Optional[str] = None
        self.argument2: Optional[str] = None
        self.status: str = "waiting"  # waiting | active | judging | complete
        self.verdict: Optional[JudgeVerdict] = None
        self.started_at: Optional[float] = None

    def start(self, player2: str) -> None:
        self.player2 = player2
        self.status = "active"
        self.started_at = time.time()

    def submit(self, player: str, argument: str) -> None:
        if player == self.player1 and self.argument1 is None:
            self.argument1 = argument or "(no argument submitted)"
        elif player == self.player2 and self.argument2 is None:
            self.argument2 = argument or "(no argument submitted)"
        if self.argument1 is not None and self.argument2 is not None:
            self.status = "judging"

    def time_remaining(self) -> int:
        if self.started_at is None:
            return self.DURATION
        elapsed = time.time() - self.started_at
        return max(0, int(self.DURATION - elapsed))

    def is_expired(self) -> bool:
        return self.status == "active" and self.time_remaining() == 0

    def player_label(self, username: str) -> str:
        return "Player 1" if username == self.player1 else "Player 2"

    def opponent_of(self, username: str) -> Optional[str]:
        return self.player2 if username == self.player1 else self.player1

    def alias_of(self, username: str) -> str:
        """Returns the public alias for a player (falls back to username)."""
        if username == self.player1:
            return self.alias1 or username
        return self.alias2 or username or "Player 2"

    def opponent_alias_of(self, username: str) -> str:
        """Returns the public alias of the opponent (falls back to username)."""
        if username == self.player1:
            return self.alias2 or self.player2 or "Opponent"
        return self.alias1 or self.player1 or "Opponent"
