"""Banter after a failure (GameController::setUpBanterArray and playRandomBanter)."""

import random

# Lines 50 and up were only used when the device language was English; they were only
# recorded in English (GameController::setUpBanterArray).
GENERAL = tuple(f"VO_Banter_{n:02d}" for n in
                (1, 3, 4, 5, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 24, 28, 30, 32, 36, 40, 41, 50, 57, 58))
LOW_SCORE = tuple(f"VO_Banter_{n:02d}" for n in (8, 14, 25, 27, 33, 35, 51, 52, 53, 55, 56))
HIGH_SCORE = tuple(f"VO_Banter_{n:02d}" for n in
                   (2, 7, 20, 21, 26, 29, 31, 34, 37, 38, 39, 54, 59, 60))
ENGLISH_ONLY_FROM = 50


def _not_english(lines: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(line for line in lines if int(line[-2:]) < ENGLISH_ONLY_FROM)
HIGH_SCORE_THRESHOLD = 50


class _Bag:
    """Indices not yet used sit at the front; a used index is swapped to the back."""

    def __init__(self, lines: tuple[str, ...]) -> None:
        self.lines = lines
        self.order = list(range(len(lines)))
        self.unused = len(lines)

    def take(self, slot: int) -> str:
        line = self.lines[self.order[slot]]
        last = self.unused - 1
        self.order[slot], self.order[last] = self.order[last], self.order[slot]
        self.unused -= 1
        return line


class Banter:
    """Draws from the general pool plus the low or high score pool, without repeats until
    the general pool runs out. Lives as long as a game controller did in the original."""

    def __init__(self, rng: random.Random, english: bool = True) -> None:
        self._rng = rng
        pick = (lambda lines: lines) if english else _not_english
        self._general = _Bag(pick(GENERAL))
        self._low = _Bag(pick(LOW_SCORE))
        self._high = _Bag(pick(HIGH_SCORE))

    def pick(self, score: int) -> str:
        # The original always drew over general plus low counts, even above the threshold.
        slot = self._rng.randrange(self._low.unused + self._general.unused)
        if slot < self._general.unused:
            line = self._general.take(slot)
        elif score < HIGH_SCORE_THRESHOLD:
            line = self._low.take(slot - self._general.unused)
        else:
            line = self._high.take(slot - self._general.unused)
        if self._general.unused < 1:
            self._general.unused = len(self._general.lines)
            if self._high.unused < 1:
                self._high.unused = len(self._high.lines)
            if self._low.unused < 1:
                self._low.unused = len(self._low.lines)
        return line
