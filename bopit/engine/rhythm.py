"""Rhythm grading for Basic and Extreme (GameController::checkInputTiming, postProcessInput)."""

from dataclasses import dataclass, field
from enum import Enum

# Positions in the music's "a" loop, in seconds of the file.
PERFECT_WINDOW = (0.78, 0.84)
GOOD_EARLY_FROM = 0.75
GOOD_LATE_TO = 0.87
OK_LATE_TO = 1.91
STREAK_LENGTH = 25


class Grade(Enum):
    PERFECT = "Perfect"
    GOOD = "Good"
    OK = "OK"
    # The original logged "should have lost" and reset the counts, without feedback.
    MISSED = "Missed"


class Streak(Enum):
    NONE = 0
    PERFECT = 1
    GOOD = 2


@dataclass
class RhythmState:
    perfect_count: int = 0
    good_count: int = 0
    ok_count: int = 0
    consecutive_perfects: int = 0
    streak: Streak = Streak.NONE
    # 0 for a perfect, 1 for a good, as in the original's lastMoveList.
    recent: list[int] = field(default_factory=list)
    end_bonus: int = 0

    def grade(self, position: float) -> Grade:
        """Grade a move made at this music position and update the end bonus."""
        low, high = PERFECT_WINDOW
        if low <= position <= high:
            self.perfect_count += 1
            self.recent.append(0)
            self.end_bonus += {Streak.PERFECT: 100, Streak.GOOD: 85}.get(self.streak, 75)
            return Grade.PERFECT
        if GOOD_EARLY_FROM <= position < low or high < position <= GOOD_LATE_TO:
            self.good_count += 1
            self.recent.append(1)
            self.end_bonus += {Streak.PERFECT: 75, Streak.GOOD: 60}.get(self.streak, 50)
            return Grade.GOOD
        if 0.0 <= position < GOOD_EARLY_FROM or GOOD_LATE_TO < position <= OK_LATE_TO:
            self.ok_count += 1
            self._reset_run()
            return Grade.OK
        self.ok_count = 0
        self._reset_run()
        return Grade.MISSED

    def _reset_run(self) -> None:
        self.perfect_count = 0
        self.good_count = 0
        self.consecutive_perfects = 0
        self.streak = Streak.NONE
        self.recent.clear()

    def post_process(self) -> Streak | None:
        """Award streak bonuses. Returns the streak to announce, if one was earned now."""
        if self.good_count + self.perfect_count < STREAK_LENGTH and self.consecutive_perfects == 0:
            return None
        perfects_in_list = 0
        goods_in_list = 0
        for value in self.recent:
            if value == 0:
                perfects_in_list += 1
                self.consecutive_perfects += 1
            elif value == 1:
                goods_in_list += 1
                self.consecutive_perfects = 0
        if perfects_in_list != STREAK_LENGTH and self.consecutive_perfects != STREAK_LENGTH:
            if self.good_count + self.perfect_count < STREAK_LENGTH:
                self.recent.clear()
                return None
            if self.streak == Streak.GOOD:
                perfects = self.perfect_count + perfects_in_list
                if self.good_count + perfects + goods_in_list < 2 * STREAK_LENGTH:
                    if perfects < 2 * STREAK_LENGTH or goods_in_list != 0:
                        self.recent.clear()
                        return None
                    self.streak = Streak.PERFECT
                    self.end_bonus += 100
                else:
                    self.end_bonus += 75
                self.perfect_count = 0
                self.good_count = 0
            elif self.streak == Streak.PERFECT:
                self.perfect_count = 0
                self.good_count = 0
                self.end_bonus += 75
                self.recent.clear()
                return None
            else:
                self.perfect_count = 0
                self.good_count = 0
                self.streak = Streak.GOOD
                self.end_bonus += 75
        else:
            self.perfect_count = 0
            self.good_count = 0
            self.consecutive_perfects = 0
            self.streak = Streak.PERFECT
            self.end_bonus += 100
        self.recent.clear()
        return self.streak
