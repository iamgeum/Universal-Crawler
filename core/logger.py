"""구조화 로깅."""

from __future__ import annotations

import logging
import sys

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    global _configured
    if _configured:
        return
    logging.basicConfig(
        level=level,
        format=_LOG_FORMAT,
        stream=sys.stderr,
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
