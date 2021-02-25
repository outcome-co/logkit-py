"""This module contains the functionality to redirect the standard library logging system into our logging system."""

import inspect
import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Dict, List, MutableSequence, Optional, Protocol, Sequence, Union, cast  # noqa: WPS235

from outcome.logkit.logger import get_logger
from outcome.logkit.types import StructLogger
from outcome.utils import env

if TYPE_CHECKING:  # pragma: no cover
    ArgsType = logging._ArgsType  # type: ignore
    ExcInfoType = logging._ExcInfoType  # type: ignore
else:
    ArgsType = object
    ExcInfoType = object


class SupportsIndex(Protocol):  # pragma: no cover
    def __index__(self) -> int:
        ...


class HandlerList(MutableSequence[logging.Handler]):  # noqa: WPS214
    __slots__ = ('_items', '_restricted')  # noqa: WPS607

    def __init__(self, items: Optional[List[logging.Handler]] = None) -> None:
        self._items = items or []
        self._restricted = False

    def restrict(self):
        self._restricted = True

    def relax(self):
        self._restricted = False

    def __len__(self) -> int:
        return self._items.__len__()  # noqa: WPS609

    def __getitem__(self, s: SupportsIndex):
        return self._items.__getitem__(s)  # noqa: WPS609

    def insert(self, index: int, value: logging.Handler) -> None:
        self._modification_guard(value)
        self._items.insert(index, value)

    def __setitem__(self, s: SupportsIndex, v: logging.Handler) -> None:
        self._modification_guard(v)
        self._items.__setitem__(s, v)  # noqa: WPS609

    def __delitem__(self, i: int) -> None:  # noqa: WPS603
        v = self._items[i]
        self._modification_guard(v)
        self._items.__delitem__(i)  # noqa: WPS609

    def _modification_guard(self, value: logging.Handler) -> None:
        if not self._restricted:
            return

        # The only modifications we allow are for pytest loggers
        handler_module = inspect.getmodule(value)

        if handler_module and 'pytest' in handler_module.__name__ and env.is_pytest():
            return

        raise RuntimeError('Cannot modify restricted list')


# Extract some useful attributes to a dict
def record_to_dict(record: logging.LogRecord) -> Dict[str, object]:
    d: Dict[str, object] = {
        # These keys have specific meanings
        'levelno': record.levelno,
        'level': record.levelname,
        'logger': record.name,
    }

    # Bindings contains additional information added by the InterceptLogger
    bindings = getattr(record, 'bindings', {})
    d.update(bindings)

    if record.exc_info:
        d['exc_info'] = record.exc_info

    return d


# Behave exactly like a normal logger, except don't allow
# any local handlers and always forward to root
class InterceptLogger(logging.Logger):
    @property
    def propagate(self):
        return True

    @propagate.setter  # type: ignore
    def propagate(self, v: bool):
        # No-op
        ...

    @property
    def handlers(self):
        return []

    @handlers.setter  # type: ignore
    def handlers(self, v: List[object]):
        # No-op
        ...

    def _log(  # noqa: WPS211
        self,
        level: int,
        msg: str,
        args: ArgsType,
        exc_info: ExcInfoType = None,
        extra: Optional[Dict[str, object]] = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        **kwargs: object,
    ):
        # The built-in logger library actually has support for arbitrary fields, they're just
        # passed around the the `extra` parameter. We'll mark them so they're easy to find later

        bindings = extra or {}
        extra = {'bindings': bindings}

        if kwargs:
            bindings.update(kwargs)

        return super()._log(level, msg, args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel)


# This is the bridge between the two logging systems - messages are
# handled by being forwarded to the struct logger
class StructlogHandler(logging.Handler):
    def __init__(self, struct_logger: StructLogger, level: int = logging.NOTSET):
        super().__init__(level)
        self.struct_logger = struct_logger

    def emit(self, record: logging.LogRecord):
        # We need to retrieve the name of the method based on the level, and re-dispatch
        # the event
        getattr(self.struct_logger, record.levelname.lower())(record.getMessage().strip(), **record_to_dict(record))


# This handler stores emitted records in a buffer
# so they can be processed later
class BufferHandler(logging.Handler):
    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level)
        self.buffer: List[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord):
        self.buffer.append(record)


def reset_standard_library_logging(level: int):
    # Send warnings to the standard library log system
    logging.captureWarnings(True)

    # Set the level
    logging.root.setLevel(level)

    # Ensure all future loggers use the InterceptLogger as the base class
    logging.setLoggerClass(InterceptLogger)

    # Iterate over all existing loggers and configure them to
    # behave like InterceptLoggers
    intercept_existing_loggers()


# There's no stub for manager
class Manager(Protocol):
    loggerDict: Dict[str, Union[logging.Logger, logging.PlaceHolder]]  # noqa: WPS115,N815


def intercept_existing_loggers():
    # All existing loggers (at least those retrieved via `getLogger`)
    # are in the loggerDict dict on the manager object
    manager = cast(Manager, logging.Logger.manager)  # type: ignore

    for logger in manager.loggerDict.values():

        # The log manager inserts placeholders into the hierarchy
        # there's no processing to do
        if not isinstance(logger, logging.Logger):
            continue

        # Remove existing handlers
        replace_handlers(logger, [])

        # Ensure it propagates its messages up to root
        logger.propagate = True


@contextmanager
def intercepted_logging(level: int):
    reset_standard_library_logging(level)
    buffer = setup_buffer_intercept(level)

    yield

    structlog_handler = setup_structlog_intercept(level)
    handle_records(buffer.buffer, structlog_handler)


def setup_buffer_intercept(level: int) -> BufferHandler:
    # Create a buffer to store all of the log records
    # that may occur during the setup so we can process
    # them after the config is complete
    buffer_handler = BufferHandler(level)

    # Use a frozenlist to make sure no-one tries to modify handlers
    handlers = HandlerList([buffer_handler])
    handlers.restrict()

    replace_handlers(logging.root, handlers)

    return buffer_handler


def setup_structlog_intercept(level: int) -> StructlogHandler:
    # Now reconfigure root to use structlog
    # We want to intercept everything that's sent to the standard
    # library's logging module, and redirect it to our log system.
    #
    # We can create a Handler instance and attach it to the root logger
    # and replace all other handlers.

    # Create a handler that we'll put on the root
    structlog_handler = StructlogHandler(get_logger(), level)

    # To make ipython bearable, we filter some log messages
    if env.is_ipython():  # pragma: no cover
        parso_loggers = {'parso', 'parso.python.diff', 'parso.cache'}
        # `parso` prints a log of messages when ipython tries to autocomplete
        for logger in parso_loggers:
            logging.getLogger(logger).disabled = True

    # Instead of adding the handler to the root's list of handlers
    # we'll go a step further by replacing the list object
    # with a frozenlist that will throw an Exception if another
    # piece of code tries to modify it
    handlers = HandlerList([structlog_handler])
    handlers.restrict()

    replace_handlers(logging.root, handlers)

    return structlog_handler


def replace_handlers(logger: logging.Logger, handlers: Sequence[logging.Handler]):
    # Be a good citizen
    for handler in logger.handlers:
        handler.flush()
        handler.close()

    logger.handlers = list(handlers)


def handle_records(records: List[logging.LogRecord], handler: logging.Handler):
    for record in records:
        handler.handle(record)
