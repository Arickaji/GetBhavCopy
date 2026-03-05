import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os

def setup_logging(debug: bool = False):
    logger = logging.getLogger("getbhavcopy")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # Create log directory inside AppData or home
    log_dir = Path(os.getenv("APPDATA") or Path.home()) / "GetBhavCopy"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file_path = log_dir / "getbhavcopy.log"

    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=5_000_000,
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger