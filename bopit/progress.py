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
        # One-time things already shown, such as the Quick Play hint.
        self.seen: set[str] = set()
        # Trophies earned, by title. Unlock trophies are also recorded here.
        self.trophies: set[str] = set()
        # Lifetime successful moves per command (the original's "<command> count").
        self.hits: dict[str, int] = {}
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                self.unlocked = set(raw.get("unlocked", []))
                self.seen = set(raw.get("seen", []))
                self.trophies = set(raw.get("trophies", []))
                self.hits = dict(raw.get("hits", {}))
            except (OSError, ValueError, AttributeError) as exc:
                log.error("Could not read progress from %s: %s", path, exc)

    def unlock(self, command: str) -> str | None:
        """Record a first unlock. Returns its message the first time only."""
        if command in self.unlocked or command not in UNLOCK_MESSAGES:
            return None
        self.unlocked.add(command)
        # The unlock message is also that BopJect's trophy.
        self.trophies.add(UNLOCK_MESSAGES[command])
        self._save()
        return UNLOCK_MESSAGES[command]

    def hit(self, command: str) -> None:
        """Count a successful move. Saved with save(), at the end of a game, as the original did."""
        self.hits[command] = self.hits.get(command, 0) + 1

    def earn(self, titles: list[str]) -> None:
        self.trophies.update(titles)
        self._save()

    def save(self) -> None:
        self._save()

    def first_time(self, flag: str) -> bool:
        """True the first time a flag is asked about, then never again."""
        if flag in self.seen:
            return False
        self.seen.add(flag)
        self._save()
        return True

    def _save(self) -> None:
        raw = {"unlocked": sorted(self.unlocked), "seen": sorted(self.seen),
               "trophies": sorted(self.trophies), "hits": self.hits}
        try:
            self._path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        except OSError as exc:
            log.error("Could not save progress to %s: %s", self._path, exc)
