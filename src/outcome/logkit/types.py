"""Logkit types."""

from typing import Any, MutableMapping, Protocol, Union

# We have to use Any, as MutableMapping is invariant
EventDict = MutableMapping[str, Any]


class Processor(Protocol):  # pragma: no cover
    def __call__(self, logger: object, method_name: str, event_dict: EventDict) -> Union[EventDict, str, bytes]:
        ...
