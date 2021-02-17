"""Interface to structlog."""

import structlog
from outcome.utils import env
from typing import Optional


def get_logger(name: Optional[str] = None, *args: object, **kwargs: object):
    if not structlog.is_configured():
        raise Exception('Logger is not configured')

    return structlog.get_logger(*args, env=env.env(), name=name, **kwargs)
