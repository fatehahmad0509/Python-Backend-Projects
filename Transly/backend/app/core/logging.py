"""
Centralized logging configuration for the application.
"""

import logging
import sys


def configure_logging(debug: bool = False) -> None:
    """Configure root logging handlers and format for the whole process."""
    level = logging.DEBUG if debug else logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # Avoid duplicate handlers if configure_logging is called more than once.
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Uvicorn's access logger is quite noisy at INFO level; keep it at WARNING
    # unless the application is running in debug mode.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING if not debug else logging.INFO)
