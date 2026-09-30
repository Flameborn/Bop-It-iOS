"""Line-based logging to the console and a file."""

import logging
from pathlib import Path

from bopit.config import LOG_DIR

LOG_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s"
DATE_FORMAT = "%H:%M:%S"


def setup_logging(level: int = logging.INFO, log_dir: Path = LOG_DIR) -> Path:
    """Configure root logging and return the log file path."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "bopit.log"
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    return log_path
