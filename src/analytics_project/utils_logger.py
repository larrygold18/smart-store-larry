# src/analytics_project/utils_logger.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Import your settings (adjust the path if your package differs)
from . import settings

LOG_DIR = Path(settings.LOG_DIR)
LOG_DIR.mkdir(parents=True, exist_ok=True)

_FMT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def init_logger(name: str) -> logging.Logger:
    """
    Create (or return cached) stdlib logger that logs to logs/<name>.log and console.
    """
    logger = logging.getLogger(name)

    # If already configured, return it
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # File handler (rotating)
    fh = RotatingFileHandler(LOG_DIR / f"{name}.log", maxBytes=500_000, backupCount=2)
    fh.setFormatter(logging.Formatter(fmt=_FMT, datefmt=_DATEFMT))
    logger.addHandler(fh)

    # Console handler
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter(fmt=_FMT, datefmt=_DATEFMT))
    logger.addHandler(sh)

    return logger
