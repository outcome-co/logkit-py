"""Logkit types."""

from typing import Any, Mapping, Protocol, TypeVar, Union

from structlog.types import EventDict

# We have to use Any, as MutableMapping is invariant
ImmutuableEventDict = Mapping[str, Any]


class Processor(Protocol):  # pragma: no cover
    def __call__(self, logger: object, name: str, event_dict: EventDict) -> Union[EventDict, str, bytes]:
        ...


L = TypeVar('L')


class StructLogger(Protocol):  # noqa: WPS214  # pragma: no cover
    def log(self, message: str, **kwargs: object) -> None:
        ...

    def debug(self, message: str, **kwargs: object) -> None:
        ...

    def info(self, message: str, **kwargs: object) -> None:
        ...

    def warning(self, message: str, **kwargs: object) -> None:
        ...

    def warn(self, message: str, **kwargs: object) -> None:
        ...

    def error(self, message: str, **kwargs: object) -> None:
        ...

    def msg(self, message: str, **kwargs: object) -> None:
        ...

    def fatal(self, message: str, **kwargs: object) -> None:
        ...

    def failure(self, message: str, **kwargs: object) -> None:
        ...

    def err(self, message: str, **kwargs: object) -> None:
        ...

    def critical(self, message: str, **kwargs: object) -> None:
        ...

    def exception(self, message: str, **kwargs: object) -> None:
        ...

    def bind(self: L, **kwargs: object) -> L:
        ...

    def unbind(self: L, *args: str) -> L:
        ...
