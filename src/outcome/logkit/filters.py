"""Helper filter for logging."""

import logging


# Excludes records that match the name provided to the
# filter on init
class ExcludeFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003,WPS125
        return not super().filter(record)
