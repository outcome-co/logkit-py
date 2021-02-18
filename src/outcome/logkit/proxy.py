"""Logging proxy. Logs calls to attributes and methods."""

import logging
from typing import Optional

from outcome.logkit.logger import get_logger


class LoggingProxy:
    def __init__(self, target: object, level: int = logging.DEBUG, name: Optional[str] = None):
        self._target = target
        self._logger = get_logger(name)
        self._name = name
        self._level = level

    def __call__(self, *args: object, **kwargs: object) -> object:
        assert callable(self._target)
        rv: object = None
        try:  # noqa: WPS501
            rv = self._target(*args, **kwargs)
        finally:
            self._logger.log(
                self._name or 'unknown',
                type='method',
                args=args,
                kwargs=kwargs,
                retval=rv,
                levelno=self._level,
                logger=self._name,
            )

        return rv

    def __getattr__(self, name: str):
        attr = getattr(self._target, name)

        if callable(attr):
            return LoggingProxy(attr, name=f'{self._name}.{name}', level=self._level)
        else:
            self._logger.log(
                f'{self._name}.{name}', type='attribute', retval=attr, levelno=self._level, logger=f'{self._name}.{name}',
            )

        return attr
