"""Entry point: python -m bopit"""

import argparse
import logging
import time

from bopit.audio import Audio
from bopit.config import SOUNDS_DIR, load_settings
from bopit.logging_setup import setup_logging
from bopit.speech import create_speech

log = logging.getLogger("bopit")


def main() -> None:
    parser = argparse.ArgumentParser(prog="bopit", description="Accessible Bop It.")
    parser.add_argument("-v", "--verbose", action="store_true", help="log debug detail")
    args = parser.parse_args()

    log_path = setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    log.info("Logging to %s", log_path)
    settings = load_settings()
    speech = create_speech(settings.speech_chars_per_second)

    audio = Audio(lambda message: speech.speak(message, interrupt=True),
                  settings.master_volume, settings.effects_volume)
    started = time.perf_counter()
    count = audio.load_directory(SOUNDS_DIR)
    log.info("Decoded %d sounds in %.0f ms", count, (time.perf_counter() - started) * 1000)
    if not audio.open():
        time.sleep(3.0)
        return

    # Stage 2 proof: a command voice line, its success sound, then a spoken confirmation.
    for name in ("VO_Bop", "SFX_Bop_C"):
        voice = audio.play(name)
        log.info("Playing %s, %.2f seconds", name, audio.duration(name))
        while voice is not None and voice.playing:
            audio.update()
            time.sleep(0.01)
    speech.speak(f"Audio ready. {count} sounds loaded.", interrupt=True)
    time.sleep(2.0)
    audio.close()


if __name__ == "__main__":
    main()
