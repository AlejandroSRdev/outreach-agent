import logging
import sys

from src.infrastructure.logging.formatter import JSONFormatter


def configure_logging(level: str) -> None:
    root = logging.getLogger()

    # Remove all existing handlers from root logger
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    log_level = getattr(logging, level.upper(), logging.INFO)
    handler.setLevel(log_level)
    root.setLevel(log_level)

    root.addHandler(handler)
