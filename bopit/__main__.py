"""Entry point: python -m bopit"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

if not __package__:
    # Started as "python bopit" or "python bopit/__main__.py" rather than "python -m bopit":
    # make the project folder importable so the bopit package can be found.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Keep pygame's startup banner out of the console, which a screen reader would read.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from bopit.app import App
from bopit.audio import Audio
from bopit.config import LANGUAGE_SOUNDS_DIR, SOUNDS_DIR, UNLOADED_SOUND_DIRS, load_settings
from bopit.debug.event_log import EventLog
from bopit.debug.options import add_arguments, from_arguments
from bopit.logging_setup import setup_logging
from bopit.speech import create_speech

log = logging.getLogger("bopit")


def main() -> None:
    parser = argparse.ArgumentParser(prog="bopit", description="Accessible Bop It.")
    parser.add_argument("-v", "--verbose", action="store_true", help="log debug detail")
    add_arguments(parser)
    args = parser.parse_args()
    debug = from_arguments(args)

    log_path = setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    log.info("Logging to %s", log_path)
    settings = load_settings()
    speech = create_speech(settings.speech_chars_per_second)

    audio = Audio(lambda message: speech.speak(message, interrupt=True),
                  settings.master_volume, settings.sfx_volume / 100, settings.music_volume / 100)
    started = time.perf_counter()
    count = audio.load_directory(SOUNDS_DIR, skip=UNLOADED_SOUND_DIRS)
    if LANGUAGE_SOUNDS_DIR.is_dir():
        for folder in sorted(p for p in LANGUAGE_SOUNDS_DIR.iterdir() if p.is_dir()):
            count += audio.load_language(folder.name, folder)
    log.info("Decoded %d sounds in %.0f ms", count, (time.perf_counter() - started) * 1000)
    audio.open()
    event_log = None
    if debug is not None:
        event_log = EventLog.open()
        state = "the bot plays" if debug.bot else "you play, the bot is off"
        # Printed, so a screen reader reads it in the console.
        print(f"Debug mode: {state}. Event log: {event_log.path}")
        log.info("Debug mode %s, event log %s", debug, event_log.path)
    try:
        App(speech, audio, settings, debug, event_log).run()
    finally:
        audio.close()
        if event_log is not None:
            event_log.close()


if __name__ == "__main__":
    main()
