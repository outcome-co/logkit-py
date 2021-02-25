"""Outputs Stackdriver-compliant JSON."""

from datetime import datetime
from typing import Union, cast

import structlog
from outcome.logkit.types import EventDict


class StackdriverRenderer(structlog.processors.JSONRenderer):
    def __call__(self, logger: object, name: str, event_dict: EventDict) -> Union[str, bytes]:
        return super().__call__(logger, name, self.format_for_stackdriver(event_dict))

    @classmethod
    def format_for_stackdriver(cls, event_dict: EventDict):
        formatted_dict = dict(event_dict)
        level = formatted_dict.pop('level', None)
        if level:
            formatted_dict['severity'] = level

        event = formatted_dict.pop('event', None)
        if event:
            formatted_dict['message'] = event
        else:
            formatted_dict['message'] = ''

        timestamp = formatted_dict.pop('timestamp', None)
        if timestamp:
            try:
                ts = datetime.fromtimestamp(cast(float, timestamp)).isoformat('T')
                timestamp_str = f'{ts}Z'
            except Exception:
                timestamp_str = timestamp
        else:
            ts = datetime.now().isoformat('T')
            timestamp_str = f'{ts}Z'

        formatted_dict['timestamp'] = timestamp_str

        return formatted_dict
