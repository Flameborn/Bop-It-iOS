"""Copy the original English sounds out of BopIt.app into sounds/, sorted into folders.

Usage: python tools/extract_sounds.py

Filenames are kept exactly as in the original. The first matching rule wins, and any
file that matches no rule stops the script so nothing is silently left behind.
"""

import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bopit.config import ORIGINAL_APP_DIR, ORIGINAL_LANG_DIR, SOUNDS_DIR  # noqa: E402

COMMANDS = "Bop|Brush|Crank|Flick|Nail|Pass|Poke|Pull|Shake|Shout|Spin|Squeeze|Twist"

RULES: list[tuple[str, str]] = [
    (r".*_HLWN$", "themes/halloween"),
    (r".*_XMAS$", "themes/christmas"),
    (rf"VO_({COMMANDS})$", "commands/voice"),
    (r"SFX_[A-Za-z]+_[CR]$", "commands/effects"),
    (r"VO_Banter_\d+$", "voice/banter"),
    (r"VO_Die_\d+$", "voice/die"),
    (r"SFX_(Back|BackButtonOLD|Select|SelectGame|SettingsSelect)$", "menu"),
    (r"SFX_(BonusScore|HighScore|ScoreAnimation)$", "score"),
    (r"(MUSIC|Music)_.+$", "music"),
    (r"basicbeatSilent$", "music"),
]


def folder_for(stem: str) -> str | None:
    for pattern, folder in RULES:
        if re.fullmatch(pattern, stem):
            return folder
    return None


def main() -> None:
    sources = sorted(ORIGINAL_APP_DIR.glob("*.wav")) + sorted(ORIGINAL_LANG_DIR.glob("*.wav"))
    plan: dict[str, tuple[Path, Path]] = {}
    unmatched: list[str] = []
    for source in sources:
        folder = folder_for(source.stem)
        if folder is None:
            unmatched.append(source.name)
            continue
        if source.stem in plan:
            sys.exit(f"Duplicate sound name {source.stem}: {plan[source.stem][0]} and {source}")
        plan[source.stem] = (source, SOUNDS_DIR / folder / source.name)
    if unmatched:
        sys.exit("No folder rule for: " + ", ".join(unmatched))

    counts: dict[str, int] = {}
    for source, target in plan.values():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        folder = target.parent.relative_to(SOUNDS_DIR).as_posix()
        counts[folder] = counts.get(folder, 0) + 1
    for folder in sorted(counts):
        print(f"{folder}: {counts[folder]}")
    print(f"Total: {len(plan)} sounds copied to {SOUNDS_DIR}")


if __name__ == "__main__":
    main()
