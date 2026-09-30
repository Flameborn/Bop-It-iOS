"""The saved game (the original's saveGame.dat). There is at most one, and loading it or
starting any new game removes it."""

import json
import logging
from pathlib import Path

from bopit.config import PROJECT_ROOT

log = logging.getLogger(__name__)

SAVE_PATH = PROJECT_ROOT / "savegame.json"


class SavedGame:
    def __init__(self, path: Path = SAVE_PATH) -> None:
        self._path = path

    def exists(self) -> bool:
        return self._path.exists()

    def write(self, data: dict) -> None:
        try:
            self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError as exc:
            log.error("Could not save the game to %s: %s", self._path, exc)

    def take(self) -> dict | None:
        """Read the saved game and remove it, as the original's loadGame did."""
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            log.error("Could not read the saved game from %s: %s", self._path, exc)
            data = None
        self.remove()
        return data

    def remove(self) -> None:
        try:
            self._path.unlink(missing_ok=True)
        except OSError as exc:
            log.error("Could not remove the saved game %s: %s", self._path, exc)
