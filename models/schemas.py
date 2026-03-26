from pydantic import BaseModel, Field
from typing import Optional
import time


class JudgeVerdict(BaseModel):
    winner: str  # "Team A", "Team B", or "Tie"
    human_originality_score_p1: int = Field(ge=1, le=10)
    human_originality_score_p2: int = Field(ge=1, le=10)
    reasoning: str
    winning_quote: str


DURATIONS = {"versus": 120, "private": 120}
BOT_NAME  = "AkobatoBot"
BOT_ALIAS = "🤖 Akobato AI"


class MatchState:
    """
    Supports both 1v1 and group (team) matches.

    team_size = 1  →  classic 1v1; player1/player2/alias1/alias2/argument1/argument2
                       work exactly as before (properties delegate to team dicts).
    team_size > 1  →  group match; teams fill up before match starts; each player
                       submits individually; combined team args are sent to the AI.
    """

    def __init__(self, match_id: str, prompt: str, player1: str,
                 mode: str = "versus", team_size: int = 1):
        self.match_id   = match_id
        self.prompt     = prompt
        self.mode       = mode
        self.duration   = DURATIONS.get(mode, 120)
        self.room_code: Optional[str] = None
        self.team_size  = max(1, min(team_size, 3))   # 1, 2, or 3

        # ── Team rosters ────────────────────────────────────────────────────
        self.team1: list[str] = [player1]  # usernames on Team A
        self.team2: list[str] = []         # usernames on Team B

        # ── Per-player aliases & arguments ──────────────────────────────────
        self._t1_aliases: dict[str, str] = {}
        self._t2_aliases: dict[str, str] = {}
        self._t1_args:    dict[str, str] = {}
        self._t2_args:    dict[str, str] = {}

        self.status:     str                     = "waiting"
        self.verdict:    Optional[JudgeVerdict]  = None
        self.started_at: Optional[float]         = None

    # ── Backward-compat properties (1v1 callers use these) ────────────────────

    @property
    def player1(self) -> Optional[str]:
        return self.team1[0] if self.team1 else None

    @property
    def player2(self) -> Optional[str]:
        return self.team2[0] if self.team2 else None

    @player2.setter
    def player2(self, v: str):
        """Allow legacy `match.player2 = x` from start()."""
        if v and (not self.team2 or self.team2[0] != v):
            self.team2 = [v]

    @property
    def alias1(self) -> Optional[str]:
        p = self.player1
        return self._t1_aliases.get(p) if p else None

    @alias1.setter
    def alias1(self, v: str):
        p = self.player1
        if p:
            self._t1_aliases[p] = v

    @property
    def alias2(self) -> Optional[str]:
        p = self.player2
        return self._t2_aliases.get(p) if p else None

    @alias2.setter
    def alias2(self, v: str):
        p = self.player2
        if p:
            self._t2_aliases[p] = v

    @property
    def argument1(self) -> Optional[str]:
        p = self.player1
        return self._t1_args.get(p) if p else None

    @argument1.setter
    def argument1(self, v: str):
        p = self.player1
        if p:
            self._t1_args[p] = v

    @property
    def argument2(self) -> Optional[str]:
        p = self.player2
        return self._t2_args.get(p) if p else None

    @argument2.setter
    def argument2(self, v: str):
        p = self.player2
        if p:
            self._t2_args[p] = v

    # ── Team management ───────────────────────────────────────────────────────

    def next_open_team(self) -> Optional[int]:
        """Returns 1 or 2 for the next player to join, None if room is full."""
        if len(self.team1) < self.team_size:
            return 1
        if len(self.team2) < self.team_size:
            return 2
        return None

    def add_player(self, username: str, alias: str) -> Optional[int]:
        """Assign player to a team. Starts match when both teams are full.
        Returns team number (1 or 2) or None if room is already full."""
        team = self.next_open_team()
        if team == 1:
            self.team1.append(username)
            self._t1_aliases[username] = alias
        elif team == 2:
            self.team2.append(username)
            self._t2_aliases[username] = alias
        else:
            return None
        if self.is_full():
            self.status     = "active"
            self.started_at = time.time()
        return team

    def is_full(self) -> bool:
        return len(self.team1) >= self.team_size and len(self.team2) >= self.team_size

    def all_players(self) -> list[str]:
        return self.team1 + self.team2

    # ── Legacy start (1v1) ───────────────────────────────────────────────────

    def start(self, player2: str) -> None:
        self.player2    = player2
        self.status     = "active"
        self.started_at = time.time()

    # ── Submission ────────────────────────────────────────────────────────────

    def submit(self, player: str, argument: str) -> None:
        arg = argument or "(no argument submitted)"
        if player in self.team1 and player not in self._t1_args:
            self._t1_args[player] = arg
        elif player in self.team2 and player not in self._t2_args:
            self._t2_args[player] = arg
        # Go to judging when all players on both sides have submitted
        if (len(self._t1_args) >= len(self.team1) and
                len(self._t2_args) >= len(self.team2)):
            self.status = "judging"

    def auto_submit_expired(self) -> None:
        """Fill in blanks for players who didn't submit before timer ran out."""
        for p in self.team1:
            self._t1_args.setdefault(p, "(no argument submitted)")
        for p in self.team2:
            self._t2_args.setdefault(p, "(no argument submitted)")
        self.status = "judging"

    # ── Combined arguments for AI judge ──────────────────────────────────────

    def combined_arg(self, team: int) -> str:
        """Returns a single string representing all arguments from a team."""
        if team == 1:
            members, aliases, args = self.team1, self._t1_aliases, self._t1_args
        else:
            members, aliases, args = self.team2, self._t2_aliases, self._t2_args
        if self.team_size == 1:
            p = members[0] if members else None
            return args.get(p, "") if p else ""
        parts = []
        for p in members:
            a = aliases.get(p, "?")
            parts.append(f"{a}: {args.get(p, '(silent)')}")
        return "\n".join(parts)

    # ── Player query helpers ──────────────────────────────────────────────────

    def player_team(self, username: str) -> Optional[int]:
        if username in self.team1: return 1
        if username in self.team2: return 2
        return None

    def player_label(self, username: str) -> str:
        """Returns 'Player 1' or 'Player 2' — used by verdict/scoring."""
        return "Player 1" if username in self.team1 else "Player 2"

    def alias_of(self, username: str) -> str:
        return (self._t1_aliases.get(username) or
                self._t2_aliases.get(username) or "Fighter")

    def opponent_alias_of(self, username: str) -> str:
        """Returns a readable label for the opposing side."""
        if username in self.team1:
            opp, opp_aliases = self.team2, self._t2_aliases
        else:
            opp, opp_aliases = self.team1, self._t1_aliases
        if not opp:
            return "Opponent"
        if len(opp) == 1:
            return opp_aliases.get(opp[0], "Opponent")
        return " & ".join(opp_aliases.get(p, "?") for p in opp)

    def team_label(self, team: int) -> str:
        return "Team A" if team == 1 else "Team B"

    def team_aliases(self, team: int) -> list[str]:
        """Sorted list of aliases for a team (for display)."""
        if team == 1:
            return [self._t1_aliases.get(p, "?") for p in self.team1]
        return [self._t2_aliases.get(p, "?") for p in self.team2]

    # ── Submission progress ───────────────────────────────────────────────────

    def submitted_count(self) -> tuple[int, int]:
        """Returns (submitted, total) across both teams."""
        submitted = len(self._t1_args) + len(self._t2_args)
        total     = len(self.team1) + len(self.team2)
        return submitted, total

    # ── Timer ─────────────────────────────────────────────────────────────────

    def time_remaining(self) -> int:
        if self.started_at is None:
            return self.duration
        return max(0, int(self.duration - (time.time() - self.started_at)))

    def is_expired(self) -> bool:
        return self.status == "active" and self.time_remaining() == 0
