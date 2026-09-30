"""Entry point: python -m bopit"""

import argparse
import logging
import time

from bopit.config import load_settings
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

    started = time.perf_counter()
    speech.speak("Bop It. Speech ready.", interrupt=True)
    log.info("speak() returned in %.1f ms", (time.perf_counter() - started) * 1000)
    # Backends like SAPI speak from this process, so give them time before exiting.
    time.sleep(2.0)


if __name__ == "__main__":
    main()
