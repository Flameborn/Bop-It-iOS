"""Local high scores, kept like the original's per mode top 10 (GameSettings::saveGameModeScore)."""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from bopit.config import PROJECT_ROOT

log = logging.getLogger(__name__)

SCORES_PATH = PROJECT_ROOT / "scores.json"
LIST_LENGTH = 10


@dataclass(frozen=True)
class Entry:
    # Points, or for Blitz a time in seconds.
    score: float
    moves: int


class Scores:
    def __init__(self, path: Path = SCORES_PATH) -> None:
        self._path = path
        self._modes: dict[str, list[Entry]] = {}
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                self._modes = {mode: [Entry(**e) for e in entries] for mode, entries in raw.items()}
            except (OSError, ValueError, TypeError) as exc:
                log.error("Could not read scores from %s: %s", path, exc)

    def entries(self, mode: str) -> list[Entry]:
        # A mode never played has one placeholder entry of 0 and 0, as in the original.
        return list(self._modes.get(mode, [Entry(0, 0)]))

    def best(self, mode: str) -> Entry:
        return self.entries(mode)[0]

    def add(self, mode: str, score: int, moves: int) -> int:
        """Record a result and return the previous top score."""
        entries = self.entries(mode)
        previous_best = entries[0].score
        for index, entry in enumerate(entries):
            if entry.score <= score:
                entries.insert(index, Entry(score, moves))
                del entries[LIST_LENGTH:]
                self._modes[mode] = entries
                self._save()
                break
        return previous_best

    def add_time(self, mode: str, seconds: float) -> float:
        """Record a Blitz time, fastest first (GameSettings::saveGameModeTime). A 0 entry is
        an empty slot. Returns the value the original compared against last, which is 0 or
        the previous best whenever the new time is a new best."""
        entries = self.entries(mode)
        count = len(entries)
        compared = entries[count - 1].score
        index = count - 2
        while True:
            if compared <= seconds and compared != 0:
                position = index + 1
                break
            if index + 1 > 0:
                compared = entries[index].score
            more = index > 0
            position = index
            index -= 1
            if not more:
                break
        position += 1 if compared < seconds else 0
        if position < count:
            entries.insert(position, Entry(seconds, 0))
            del entries[LIST_LENGTH:]
            self._modes[mode] = entries
            self._save()
        return compared

    def reset(self, modes: tuple[str, ...]) -> None:
        """Scores::alertView:clickedButtonAtIndex: clears the four solo lists."""
        for mode in modes:
            self._modes.pop(mode, None)
        self._save()

    def _save(self) -> None:
        raw = {mode: [asdict(e) for e in entries] for mode, entries in self._modes.items()}
        try:
            self._path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        except OSError as exc:
            log.error("Could not save scores to %s: %s", self._path, exc)
