"""Interface to structlog."""

from typing import Optional

import structlog
from outcome.logkit.types import StructLogger
from outcome.utils import env


def get_logger(name: Optional[str] = None, *args: object, **kwargs: object) -> StructLogger:
    if not structlog.is_configured():
        raise Exception('Logger is not configured')  # noqa: WPS454

    return structlog.get_logger(*args, env=env.env(), name=name, **kwargs)
