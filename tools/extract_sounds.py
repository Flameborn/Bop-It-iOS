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

from bopit.config import (LANGUAGE_SOUNDS_DIR, ORIGINAL_APP_DIR, ORIGINAL_LANG_DIR,  # noqa: E402
                          SOUNDS_DIR)

# The other languages' own recordings, all voice lines, from each language's folder.
LANGUAGE_FOLDERS = {"de": "de.lproj", "es": "es.lproj", "fr": "fr.lproj", "it": "it.lproj"}
# Recordings 1.1.9 lacked but its code asked for, taken from a later version of the app that
# the developer supplied (see docs/DEVIATIONS.md). German banter line 7 is in the German
# list, but 1.1.9 had no recording, so it played nothing. The later version's folder was
# deleted once the file was copied; the copy in sounds/languages/de is the one kept.
LATER_VERSION = SOUNDS_DIR / "extra voices"
FROM_LATER_VERSION = {"de": ("VO_Banter_07.wav",)}

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
    copy_languages()


def copy_languages() -> None:
    for code, folder in LANGUAGE_FOLDERS.items():
        target = LANGUAGE_SOUNDS_DIR / code
        target.mkdir(parents=True, exist_ok=True)
        sources = sorted((ORIGINAL_APP_DIR / folder).glob("*.wav"))
        for name in FROM_LATER_VERSION.get(code, ()):
            source = LATER_VERSION / code / name
            if source.exists():
                sources.append(source)
            elif not (target / name).exists():
                sys.exit(f"Missing {source}, and no copy of it in {target}")
            # Otherwise the copy made earlier, now in sounds/languages, is kept.
        for source in sources:
            shutil.copy2(source, target / source.name)
        print(f"languages/{code}: {len(sources)}")


if __name__ == "__main__":
    main()
