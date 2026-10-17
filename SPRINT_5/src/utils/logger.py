"""Project-wide logging helper (console + rotating-friendly file handler)."""
from __future__ import annotations

import logging
import sys

from config import settings

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    """Return a logger that writes to console and ``logs/sprint5.log``."""
    global _CONFIGURED
    if not _CONFIGURED:
        settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
        fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(fmt)
        root.addHandler(console)
        file_handler = logging.FileHandler(settings.LOG_DIR / "sprint5.log", encoding="utf-8")
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
        _CONFIGURED = True
    return logging.getLogger(name)
