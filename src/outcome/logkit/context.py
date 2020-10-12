"""Interface to structlog."""

from structlog.contextvars import bind_contextvars, clear_contextvars, unbind_contextvars

# For these to work, structlog needs to be configured with the structlog.contextvars.merge_contextvars processor
# This is handled for you when you use `init()`


def add(**kwargs):
    bind_contextvars(**kwargs)


def remove(*args):
    unbind_contextvars(*args)


def clear():
    clear_contextvars()
