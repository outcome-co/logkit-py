"""Interface to structlog."""

import structlog
from outcome.utils import env


def get_logger(name=None, *args, **kwargs):
    if not structlog.is_configured():
        raise Exception('Logger is not configured')

    return structlog.get_logger(*args, env=env.env(), name=name, **kwargs)
