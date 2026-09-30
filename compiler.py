"""Build Bop It into a Windows program with PyInstaller.

Double-click this file, or run python compiler.py with nothing after it, for a numbered menu;
it waits for Enter at the end so you can hear how it went. Or give a flag:

    python compiler.py              build
    python compiler.py --console    build with a console window, to see why the game will not start
    python compiler.py --clean      empty PyInstaller's cache first
    python compiler.py --dry-run    say what a build would do, build nothing

The build lands in dist\\BopIt, around BopIt.exe. The game's own files (sounds, images,
layouts, translations, the OpenAL and NVDA libraries) go inside it; VERSION, the license and
the changelog go beside the executable. The player's settings, scores, keys and logs are
written beside the executable when the game runs. releaser.py zips this folder.
"""

import argparse
import importlib.machinery
import importlib.util
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "BopIt"
ENTRY = "BopIt.py"
DIST = HERE / "dist"
OUTPUT = DIST / NAME
# Bundled with the game, as (source, folder inside the build).
DATA = (("sounds", "sounds"), ("images", "images"), ("layouts", "layouts"),
        ("bopit/lang", "bopit/lang"), ("vendor/openal/license.txt", "licenses/openal-soft"),
        ("vendor/nvda/license.txt", "licenses/nvda-controller-client"))
BINARIES = (("vendor/openal/soft_oal.dll", "vendor/openal"),
            ("vendor/nvda/nvdaControllerClient64.dll", "vendor/nvda"))
# Beside the executable, for the player to read: (source, name in the build).
SIDE_FILES = (("VERSION", "VERSION"), ("LICENSE", "license.txt"),
              ("changelog.txt", "changelog.txt"))
# What the game needs installed here to be bundled: (module, what pip calls it).
PACKAGES = (("pygame", "pygame"), ("prism", "prismatoid"), ("cyal", "cyal"),
            ("soundfile", "soundfile"), ("numpy", "numpy"), ("PyInstaller", "pyinstaller"))


def say(text: str = "") -> None:
    print(text, flush=True)


def version() -> str:
    path = HERE / "VERSION"
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def problems() -> list[str]:
    found = []
    if sys.platform != "win32":
        found.append("this builds the Windows version, so run it on Windows")
    missing = [pip for module, pip in PACKAGES if importlib.util.find_spec(module) is None]
    if missing:
        found.append("install these first: pip install " + " ".join(missing))
    for source, _ in DATA + BINARIES:
        if not (HERE / source).exists():
            found.append(f"{source} is missing")
    return found


def prism_native() -> list[Path]:
    """Prism's compiled module in prism/_native, which --collect-all leaves behind."""
    spec = importlib.util.find_spec("prism")
    if spec is None or not spec.submodule_search_locations:
        return []
    folder = Path(list(spec.submodule_search_locations)[0]) / "_native"
    suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
    return sorted(p for p in folder.glob("*") if p.name.endswith(suffixes))


def command(console: bool, clean: bool) -> list[str]:
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--noupx", "--name", NAME,
           "--distpath", str(DIST), "--workpath", str(HERE / "build")]
    for source, inside in BINARIES:
        cmd += ["--add-binary", f"{source}{os.pathsep}{inside}"]
    for source, inside in DATA:
        cmd += ["--add-data", f"{source}{os.pathsep}{inside}"]
    # Imported inside functions, so named outright. Prism loads its compiled half from
    # prism/_native, which is not a package, and needs cffi; soundfile needs its libsndfile.
    cmd += ["--collect-all", "prism", "--collect-all", "cyal", "--collect-all", "soundfile",
            "--collect-all", "_soundfile_data", "--hidden-import", "_cffi_backend"]
    for path in prism_native():
        cmd += ["--add-binary", f"{path}{os.pathsep}prism/_native"]
    if not console:
        cmd += ["--windowed"]
    if clean:
        cmd += ["--clean"]
    return cmd + [ENTRY]


def copy_side_files() -> None:
    for source, name in SIDE_FILES:
        path = HERE / source
        if path.exists():
            shutil.copy2(path, OUTPUT / name)
            say(f"{name} is in the build.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="compiler.py", description="build Bop It")
    parser.add_argument("--console", action="store_true", help="keep a console window")
    parser.add_argument("--clean", action="store_true", help="empty PyInstaller's cache first")
    parser.add_argument("--dry-run", action="store_true", help="build nothing, say what would happen")
    args = parser.parse_args(argv)
    os.chdir(HERE)
    found = problems()
    if found:
        say("The build cannot start:")
        for problem in found:
            say(f"  {problem}")
        return 2
    cmd = command(args.console, args.clean)
    if args.dry_run:
        say("Would run: " + " ".join(cmd[1:]))
        say(f"The build would land in {OUTPUT}.")
        return 0
    say(f"Building Bop It{' build ' + version() if version() else ''} into {OUTPUT}. This takes a minute or two.")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    started = time.perf_counter()
    if subprocess.run(cmd).returncode != 0:
        say("PyInstaller failed. Its own output above says why.")
        return 1
    copy_side_files()
    say(f"Built in {time.perf_counter() - started:.0f} seconds.")
    say(f"The game is {OUTPUT / (NAME + '.exe')}")
    return 0


MENU = (("Build the game", []),
        ("Build with a console window, to see why the game will not start", ["--console"]),
        ("Clean build: empty PyInstaller's cache first", ["--clean"]),
        ("Show what a build would do, without building", ["--dry-run"]))


def run() -> int:
    """Flags build straight away; no flags from a keyboard opens the menu."""
    if sys.argv[1:] or not sys.stdin.isatty():
        return main()
    say(f"Bop It compiler. VERSION is {version() or 'not set yet'}.")
    for number, (text, _) in enumerate(MENU, 1):
        say(f"  {number}. {text}")
    say("  0. Quit")
    while True:
        choice = input("Type a number and press Enter: ").strip()
        if choice == "0":
            return 0
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            break
        say(f"There is no choice {choice}.")
    try:
        return main(MENU[int(choice) - 1][1])
    finally:
        input("Finished. Press Enter to close this window.")


if __name__ == "__main__":
    sys.exit(run())
