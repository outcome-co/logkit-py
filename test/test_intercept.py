import logging
from importlib import reload
from unittest.mock import Mock

import pytest
import structlog
from outcome.logkit import intercept


@pytest.fixture(autouse=True)
def reload_libs():
    reload(logging)
    reload(intercept)


def test_record_to_dict():
    name = 'logger'

    record = logging.LogRecord(name, logging.DEBUG, __name__, 0, 'message', (), None)
    record.__dict__['bindings'] = {'extra': 'key'}

    event = intercept.record_to_dict(record)

    assert event['levelno'] == logging.DEBUG
    assert event['level'] == 'DEBUG'
    assert event['logger'] == name
    assert event['extra'] == 'key'


def test_record_to_dict_with_exc():
    name = 'logger'
    record = logging.LogRecord(name, logging.DEBUG, __name__, 0, 'message', (), 'exc')
    event = intercept.record_to_dict(record)
    assert event['exc_info'] == 'exc'


class MockHandler:
    def __init__(self, buffer):
        self.buffer = buffer
        self.level = 0
        self.flushed = False
        self.closed = False

    def handle(self, record):
        self.buffer.append(record)

    def flush(self, *args, **kwargs):
        self.flushed = True

    def close(self, *args, **kwargs):
        self.closed = True


class MockLogger:
    def __init__(self) -> None:
        self.records = []
        self.handlers = [MockHandler(self.records)]
        self.propagate = False
        self.level = 0


class TestInterceptLogger:
    def test_propagate(self):
        logger = intercept.InterceptLogger('test')
        assert logger.propagate
        logger.propagate = False
        assert logger.propagate

    def test_handlers(self):
        logger = intercept.InterceptLogger('test')
        assert not bool(logger.handlers)
        logger.addHandler(True)
        assert not bool(logger.handlers)

    def test_extras(self):
        logging.setLoggerClass(intercept.InterceptLogger)
        logger = logging.getLogger('test_extras')
        logging.setLoggerClass(logging.Logger)

        logger.setLevel(logging.DEBUG)

        assert isinstance(logger, intercept.InterceptLogger)

        mock_logger = MockLogger()
        logger.parent = mock_logger

        logger.info('hello', user_id=1, tenant_id=1)

        assert len(mock_logger.records) == 1
        assert mock_logger.records[0].bindings == {'user_id': 1, 'tenant_id': 1}

    def test_no_extras(self):
        logging.setLoggerClass(intercept.InterceptLogger)
        logger = logging.getLogger('test_no_extras')
        logging.setLoggerClass(logging.Logger)

        logger.setLevel(logging.DEBUG)

        assert isinstance(logger, intercept.InterceptLogger)

        mock_logger = MockLogger()
        logger.parent = mock_logger

        logger.info('hello')

        assert len(mock_logger.records) == 1
        assert not bool(mock_logger.records[0].bindings)


def test_structlog_handler():

    # This class has to be defined in the test, to ensure the `logging` module
    # hasn't been reloaded since it was defined
    class InterceptLoggerWithStructHandler(intercept.InterceptLogger):
        def __init__(self, name, level=logging.NOTSET) -> None:
            super().__init__(name, level)
            self.mock_struct_logger = Mock()
            self.handler = intercept.StructlogHandler(self.mock_struct_logger)

        @property
        def handlers(self):
            return [self.handler]

        @handlers.setter
        def handlers(self, v):
            ...

    logging.setLoggerClass(InterceptLoggerWithStructHandler)
    logger = logging.getLogger('test_structlog_handler')
    logging.setLoggerClass(logging.Logger)

    logger.setLevel(logging.DEBUG)

    logger.info(' hello  ', user_id=1)

    logger.mock_struct_logger.log.assert_called_once_with(
        'hello', levelno=logging.INFO, level='INFO', logger='test_structlog_handler', user_id=1,
    )


def test_buffer_handler():
    logger = logging.getLogger('test_buffer_handler')
    assert isinstance(logger, logging.Logger)

    buffer = intercept.BufferHandler(logging.DEBUG)

    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    logger.handlers = [buffer]

    logger.info('hello')
    logger.info('goodbye')

    assert len(buffer.buffer) == 2
    assert buffer.buffer[0].getMessage() == 'hello'


mock_logger = Mock()


def mock_logger_factory():
    return mock_logger


def test_intercepted_logging():  # noqa: WPS218,WPS231
    mock_logger.reset_mock()

    root_handlers = logging.root.handlers

    # We need to ensure the root logger is restored afterwards
    try:  # noqa: WPS501
        some_logger = logging.getLogger('my.nested.logger')
        some_logger.setLevel(logging.DEBUG)

        handler = MockHandler([])
        some_logger.propagate = False
        some_logger.handlers = [handler]

        other_logger = None

        with intercept.intercepted_logging(logging.DEBUG):
            some_logger.info('some_logger_message')
            other_logger = logging.getLogger('other_logger')

            other_logger.setLevel(logging.DEBUG)
            other_logger.debug('some_other_logger_message')

            structlog.configure(processors=[], logger_factory=mock_logger_factory)

        final_logger = logging.getLogger('final')
        final_logger.debug('final')

        assert not bool(some_logger.handlers)
        assert some_logger.propagate
        assert not bool(other_logger.handlers)
        assert other_logger.propagate

        assert handler.flushed
        assert handler.closed

        assert len(mock_logger.mock_calls) == 3
        assert mock_logger.mock_calls[0].kwargs.get('event') == 'some_logger_message'
        assert mock_logger.mock_calls[1].kwargs.get('event') == 'some_other_logger_message'
        assert mock_logger.mock_calls[2].kwargs.get('event') == 'final'
    finally:
        logging.setLoggerClass(logging.Logger)
        logging.root.handlers = root_handlers
