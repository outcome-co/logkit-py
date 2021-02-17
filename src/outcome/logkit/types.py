from typing import Protocol, MutableMapping, Union

EventDict = MutableMapping[str, object]

class Processor(Protocol):  # pragma: no cover
    def __call__(self, logger: object, method_name: str, event_dict: EventDict) -> Union[EventDict, str, bytes]: ...
