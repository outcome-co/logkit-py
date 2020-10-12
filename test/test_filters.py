import logging
from unittest.mock import Mock

from outcome.logkit.filters import ExcludeFilter


class MockHandler(logging.Handler):
    def __init__(self, mock: Mock, level=logging.NOTSET):
        super().__init__(level)
        self.mock = mock

    def emit(self, record: logging.LogRecord):
        self.mock(record.getMessage())


def test_exclude():
    logger = logging.getLogger(__name__)

    logger.propagate = False
    logger.setLevel(logging.INFO)

    mock = Mock()
    mock_handler = MockHandler(mock)

    logger.addHandler(mock_handler)

    logger.info('test message 1')
    logger.addFilter(ExcludeFilter(__name__))
    logger.info('test message 2')

    mock_handler.mock.assert_called_once_with('test message 1')
