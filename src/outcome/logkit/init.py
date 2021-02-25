"""Setup structured logging."""

import logging
import os
from typing import List, Optional, Sequence, cast

import structlog
from outcome.logkit import intercept
from outcome.logkit.stackdriver import StackdriverRenderer
from outcome.logkit.types import EventDict, Processor
from outcome.utils import env

_os_key = 'LOGKIT_LOG_LEVEL'


def get_level() -> int:
    log_level = os.environ.get(_os_key)

    if log_level:
        return int(log_level)

    if env.is_prod():
        return logging.INFO
    return logging.DEBUG


_critical = 'critical'
_fatal = 'fatal'
_error = 'error'
_warning = 'warning'
_warn = 'warn'
_info = 'info'
_debug = 'debug'

# These are taken from the standard library
levels = {
    logging.FATAL: _fatal,
    logging.ERROR: _error,
    logging.WARNING: _warning,
    logging.INFO: _info,
    logging.DEBUG: _debug,
}

level_numbers = {name: number for number, name in levels.items()}

default_level = _info

# These map variations to canonical labels
level_aliases = {
    default_level: default_level,
    _debug: _debug,
    _warn: _warning,
    _warning: _warning,
    _error: _error,
    'err': _error,
    _fatal: _fatal,
    _critical: _fatal,
    'failure': _error,
    'exception': _fatal,
}


class LogLevelProcessor:
    """This processor class ensures that each log message has a standardized log level.

    It is reponsible for determining the level, and filtering out messages that don't
    meet the level.
    """

    def __init__(self, level: int):
        self.level = level

    # At the end, we want an event dict that has a valid label, and no level number.
    def __call__(self, logger: object, method_name: str, event_dict: EventDict) -> EventDict:
        event_dict = self.normalize_level(method_name, event_dict)
        return self.filter_on_level(event_dict)

    def filter_on_level(self, event_dict: EventDict) -> EventDict:
        levelno = event_dict.pop('levelno')
        assert isinstance(levelno, int)
        if levelno < self.level:
            raise structlog.DropEvent
        return event_dict

    # Try various strategies to determine the message level
    def normalize_level(self, method_name: str, event_dict: EventDict) -> EventDict:
        event_level_number = event_dict.pop('levelno', None)
        event_level_name = event_dict.pop('level', None)

        # If we don't have anything, we tentatively use the method_name as a level
        if not (event_level_number or event_level_name):  # noqa: WPS504
            level = method_name

        # level_number has priority over the provided level name
        elif event_level_number in levels:
            # if levels is a dict with int keys, and event_level_number is a valid key, then it's an int...
            level = levels.get(cast(int, event_level_number))

        # Try using the provided level name
        else:
            assert isinstance(event_level_name, str)
            level = event_level_name.lower()

        # Find its canonical name, or revert to default
        normalized_level_name = level_aliases.get(str(level), default_level)
        normalized_level_number = level_numbers.get(normalized_level_name)

        return {**event_dict, 'level': normalized_level_name, 'levelno': normalized_level_number}


# Normalize the name/logger attribute
def logger_name_processor(logger: object, name: str, event_dict: EventDict) -> EventDict:
    name = event_dict.pop('name', name)
    event_dict['logger'] = name
    return event_dict


# Initialize the logging system
def init(level: Optional[int] = None, processors: Optional[List[Processor]] = None):  # pragma: no cover
    if not level:
        level = get_level()

    with intercept.intercepted_logging(level):
        configure_structured_logging(level, processors)


def configure_structured_logging(level: int, processors: Optional[List[Processor]] = None):

    final_processors = get_final_processors(level, processors)

    # We can leave everything else as default
    # Output will use StructLog's PrintLogger that just prints to stdout
    # https://www.structlog.org/en/stable/api.html#structlog.PrintLogger

    if env.is_prod():
        structlog.configure_once(processors=final_processors)
    else:
        structlog.configure(processors=final_processors)


def get_final_processors(level: int, processors: Optional[Sequence[Processor]] = None) -> List[Processor]:

    if not processors:
        processors = []

    # Some sensible defaults
    final_processors: List[Processor] = [
        structlog.contextvars.merge_contextvars,
        logger_name_processor,
        cast(Processor, LogLevelProcessor(level)),
        *processors,
        # Partially defined type...
        structlog.processors.StackInfoRenderer(),
        cast(Processor, structlog.dev.set_exc_info),
        cast(Processor, structlog.processors.format_exc_info),
        cast(Processor, structlog.processors.ExceptionPrettyPrinter()),
    ]

    # How is the output formatted
    if env.is_google_cloud():
        final_processors.append(structlog.processors.TimeStamper())
        # The renderer needs to be the last processor
        final_processors.append(StackdriverRenderer())
    else:
        final_processors.append(structlog.processors.TimeStamper(fmt='iso'))
        # param name mismatch
        final_processors.append(cast(Processor, structlog.stdlib.PositionalArgumentsFormatter()))
        # The renderer needs to be the last processor
        final_processors.append(structlog.dev.ConsoleRenderer())

    return final_processors
