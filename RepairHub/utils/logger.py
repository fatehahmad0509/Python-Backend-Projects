# Centralized logger for the RepairHub application.
# Writes DEBUG+ messages to a rotating log file and INFO+ messages to the console.
# Thread-safe initialization using a lock to avoid duplicate handlers.

import logging
import os
import threading
from logging.handlers import RotatingFileHandler

_lock = threading.Lock()

# Resolve log file path relative to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "repairhub.log")


def get_logger(name: str = "repairhub") -> logging.Logger:
    """Create and return a named logger with file and console handlers.

    If the logger already has handlers attached (e.g. called more than once),
    the existing logger is returned immediately to prevent duplicate output.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    with _lock:
        if logger.handlers:
            return logger
        logger.setLevel(logging.DEBUG)
        # Common log format including timestamp, thread name, level, and message
        fmt = logging.Formatter(
            "%(asctime)s [%(threadName)-15s] %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # Rotating file handler — max 5 MB per file, keep 3 backups
        fh = RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        fh.setFormatter(fmt)
        fh.setLevel(logging.DEBUG)
        # Console handler — only INFO and above to avoid clutter
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(logging.INFO)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger


# Module-level logger instance used throughout the application
logger = get_logger()
