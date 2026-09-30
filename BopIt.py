"""Start Bop It. The same as python -m bopit, and the script compiler.py builds from.

A built game has no console window, so if it fails before speech is working, the error is
written to crash.txt beside the executable.
"""

import sys
import traceback
from pathlib import Path

from bopit.__main__ import main

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:
        if getattr(sys, "frozen", False):
            crash = Path(sys.executable).resolve().parent / "crash.txt"
            crash.write_text(traceback.format_exc(), encoding="utf-8")
        raise
