"""Print decompiled functions whose names contain the given text.

Usage: python tools/show_function.py NAME [NAME ...]
Reads research/decompiled/BopIt.c, made by tools/decompile.py. Hex constants that are
addresses of string constants are shown with their text, like 0x1b3a48@"SFX_Select.wav".
"""

import os
import re
import sys
from pathlib import Path

from macho import MachO

SOURCE = Path(os.environ.get(
    "BOPIT_DECOMPILED",
    Path(__file__).resolve().parent.parent / "research" / "decompiled" / "BopIt.c"))
MARKER = "// FUNCTION "
HEX = re.compile(r"0x[0-9a-f]{5,8}\b")


def annotator(macho: MachO):
    cfstrings = macho.cfstrings()

    def annotate(match: re.Match[str]) -> str:
        text = cfstrings.get(int(match.group(0), 16))
        return match.group(0) if text is None else f'{match.group(0)}@"{text}"'

    return annotate


def main() -> None:
    wanted = sys.argv[1:]
    annotate = annotator(MachO())
    printing = False
    with SOURCE.open(encoding="utf-8", errors="replace") as source:
        for line in source:
            if line.startswith(MARKER):
                name = line[len(MARKER):]
                printing = any(w in name for w in wanted)
            if printing and line.strip():
                print(HEX.sub(annotate, line), end="")


if __name__ == "__main__":
    main()
