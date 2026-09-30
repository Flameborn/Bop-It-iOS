"""Saved progress that is not scores: which BopJects have ever been unlocked.
The original kept this as trophies (TrophyManager::unlockBopject). Trophies will build on it."""

import json
import logging
from pathlib import Path

from bopit.config import PROJECT_ROOT

log = logging.getLogger(__name__)

PROGRESS_PATH = PROJECT_ROOT / "progress.json"

# Verbatim from English.lproj/Localizable.strings.
UNLOCK_MESSAGES = {
    "Shake": "Arriba!  Shake Unlocked",
    "Flick": "Boiiinng! Flick Unlocked",
    "Squeeze": "Ha-Honk! Squeeze Unlocked",
    "Nail": "Hamma Time! Nail Unlocked",
    "Crank": "Revved Up! Crank Unlocked",
    "Spin": "Spin to Win! Spin Unlocked",
    "Brush": "Whata Rush! Brush Unlocked",
    "Shout": "Yeah! Shout Unlocked",
    "Poke": "Yowch! Poke Unlocked",
}


class Progress:
    def __init__(self, path: Path = PROGRESS_PATH) -> None:
        self._path = path
        self.unlocked: set[str] = set()
        if path.exists():
            try:
                self.unlocked = set(json.loads(path.read_text(encoding="utf-8")).get("unlocked", []))
            except (OSError, ValueError, AttributeError) as exc:
                log.error("Could not read progress from %s: %s", path, exc)

    def unlock(self, command: str) -> str | None:
        """Record a first unlock. Returns its message the first time only."""
        if command in self.unlocked or command not in UNLOCK_MESSAGES:
            return None
        self.unlocked.add(command)
        try:
            self._path.write_text(json.dumps({"unlocked": sorted(self.unlocked)}, indent=2),
                                  encoding="utf-8")
        except OSError as exc:
            log.error("Could not save progress to %s: %s", self._path, exc)
        return UNLOCK_MESSAGES[command]
