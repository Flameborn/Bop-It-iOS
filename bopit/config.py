"""Paths and user settings."""

import json
import logging
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_APP_DIR = PROJECT_ROOT / "BopIt.app"
ORIGINAL_LANG_DIR = ORIGINAL_APP_DIR / "English.lproj"
SOUNDS_DIR = PROJECT_ROOT / "sounds"
VENDOR_DIR = PROJECT_ROOT / "vendor"
LOG_DIR = PROJECT_ROOT / "logs"
SETTINGS_PATH = PROJECT_ROOT / "settings.json"
KEYS_PATH = PROJECT_ROOT / "keys.json"


# The original's three kinds of command. Silent showed commands as pictures only; it is
# kept here for reference but not offered, see docs/DEVIATIONS.md.
COMMAND_MODES = ("VOX", "SFX", "Silent")
SELECTABLE_COMMAND_MODES = ("VOX", "SFX")


@dataclass
class Settings:
    # The original's settings, with its defaults from GameSettings::loadGameSettings.
    commands: str = "VOX"
    banter: bool = True
    shout_it: bool = True
    music_volume: int = 100
    sfx_volume: int = 60
    # Index into themes.THEMES. The original starts on Original (SkinsManager::init).
    theme: int = 0
    # With no choice saved, Play started Basic (LandingPage::executePlayButtonPressed).
    quick_play: str = "Basic"
    # Commands last picked in the multiplayer command picker. Empty means its defaults.
    picked: list[str] = field(default_factory=list)
    # Our additions.
    # Shout It X-Move through the microphone (the original's "shout Yeah!" move).
    microphone: bool = True
    master_volume: float = 1.0
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
    settings = Settings(**{k: v for k, v in data.items() if k in known})
    if settings.commands not in SELECTABLE_COMMAND_MODES:
        log.warning("Commands setting %r is not available, using VOX", settings.commands)
        settings.commands = "VOX"
    return settings


def save_settings(settings: Settings, path: Path = SETTINGS_PATH) -> None:
    path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
