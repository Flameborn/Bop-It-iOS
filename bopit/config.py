"""Paths and user settings."""

import json
import logging
from dataclasses import asdict, dataclass, fields
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_APP_DIR = PROJECT_ROOT / "BopIt.app"
ORIGINAL_LANG_DIR = ORIGINAL_APP_DIR / "English.lproj"
VENDOR_DIR = PROJECT_ROOT / "vendor"
LOG_DIR = PROJECT_ROOT / "logs"
SETTINGS_PATH = PROJECT_ROOT / "settings.json"


@dataclass
class Settings:
    master_volume: float = 1.0
    effects_volume: float = 1.0
    # Ignored by backends that cannot set volume, including NVDA.
    speech_volume: float = 1.0
    # Used to estimate how long protected speech lasts, since NVDA cannot report it.
    speech_chars_per_second: float = 18.0


def load_settings(path: Path = SETTINGS_PATH) -> Settings:
    if not path.exists():
        return Settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.error("Could not read settings from %s, using defaults: %s", path, exc)
        return Settings()
    known = {f.name for f in fields(Settings)}
    return Settings(**{k: v for k, v in data.items() if k in known})


def save_settings(settings: Settings, path: Path = SETTINGS_PATH) -> None:
    path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
