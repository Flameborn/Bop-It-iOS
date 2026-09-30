"""Decompile the original armv7 binary with Ghidra into research/decompiled/BopIt.c.

Usage: python tools/decompile.py [GHIDRA_DIR]

GHIDRA_DIR defaults to the GHIDRA_DIR environment variable, then D:/Tools/ghidra_12.1.2_PUBLIC.
Takes a while. Output is gitignored because it is large and regenerable.
"""

import os
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BINARY = ROOT / "BopIt.app" / "BopIt"
RESEARCH = ROOT / "research"
ARMV7_SUBTYPE = 9


def extract_armv7(fat: Path, out: Path) -> None:
    data = fat.read_bytes()
    if data[:4] != bytes.fromhex("cafebabe"):
        out.write_bytes(data)
        return
    count = struct.unpack(">I", data[4:8])[0]
    for i in range(count):
        _cpu, subtype, offset, size, _align = struct.unpack(">5I", data[8 + i * 20:28 + i * 20])
        if subtype == ARMV7_SUBTYPE:
            out.write_bytes(data[offset:offset + size])
            return
    sys.exit("No armv7 slice found")


def main() -> None:
    ghidra = Path(sys.argv[1] if len(sys.argv) > 1 else
                  os.environ.get("GHIDRA_DIR", "D:/Tools/ghidra_12.1.2_PUBLIC"))
    launcher = ghidra / "support" / ("analyzeHeadless.bat" if os.name == "nt" else "analyzeHeadless")
    RESEARCH.mkdir(exist_ok=True)
    (RESEARCH / "decompiled").mkdir(exist_ok=True)
    # Ghidra requires the project directory to exist already.
    (RESEARCH / "ghidra_project").mkdir(exist_ok=True)
    thin = RESEARCH / "BopIt_armv7"
    extract_armv7(BINARY, thin)
    subprocess.run([
        str(launcher), str(RESEARCH / "ghidra_project"), "BopIt",
        "-import", str(thin), "-overwrite",
        "-scriptPath", str(ROOT / "tools" / "ghidra"),
        "-postScript", "DumpDecompiled.java", str(RESEARCH / "decompiled" / "BopIt.c"),
    ], check=True)


if __name__ == "__main__":
    main()
