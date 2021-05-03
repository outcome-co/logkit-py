import logging
import os
import warnings
from importlib import reload
from unittest.mock import Mock, call, patch

import pytest
import structlog

from outcome.logkit import init, stackdriver
from outcome.logkit.types import EventDict

mock_logger = Mock()


def mock_logger_factory():
    return mock_logger


@pytest.fixture(autouse=True)
def reload_structlog():
    reload(structlog)
    mock_logger.reset_mock()
    structlog.reset_defaults()


@patch('outcome.logkit.init.env.is_prod', return_value=False)
def test_get_level_not_prod(mocked_is_prod: Mock):
    assert init.get_level() == logging.DEBUG


@patch.dict(os.environ, {'LOGKIT_LOG_LEVEL': '10'})
def test_get_level_from_env():
    assert init.get_level() == 10


@patch('outcome.logkit.init.env.is_prod', return_value=True)
def test_get_level_prod(mocked_is_prod: Mock):
    assert init.get_level() == logging.INFO


def test_logger_name_processor():
    event_dict: EventDict = {'name': 'logger_name'}
    out = init.logger_name_processor(logger=None, name='', event_dict=event_dict)
    assert 'name' not in out
    assert out['logger'] == 'logger_name'


def test_logger_no_name_processor():
    event_dict = {'no_name': 'logger_name'}
    out = init.logger_name_processor(logger=None, name='', event_dict=event_dict)
    assert out == event_dict


def test_configure_structured_logging():
    init.configure_structured_logging(logging.INFO)

    renderer = structlog.get_config()['processors'][-1]

    assert isinstance(renderer, structlog.dev.ConsoleRenderer)


@patch('outcome.logkit.init.env.is_prod', return_value=True)
def test_configure_structured_logging_prod(mocked_is_prod: Mock):
    init.configure_structured_logging(logging.INFO)

    with warnings.catch_warnings(record=True) as w:
        init.configure_structured_logging(logging.INFO)
        assert w is not None
        assert len(w) == 1
        assert issubclass(w[0].category, RuntimeWarning)


@patch('outcome.logkit.init.env.is_google_cloud', return_value=True)
def test_configure_structured_logging_gcp(mocked_is_google_cloud: Mock):
    init.configure_structured_logging(logging.INFO)

    renderer = structlog.get_config()['processors'][-1]

    assert isinstance(renderer, stackdriver.StackdriverRenderer)


def test_configure_structured_logging_custom_processors():
    def custom_processor(logger: object, name: str, event_dict: EventDict) -> EventDict:
        ...

    init.configure_structured_logging(logging.INFO, processors=[custom_processor])

    processors = structlog.get_config()['processors']

    assert custom_processor in processors
    assert isinstance(processors[-1], structlog.dev.ConsoleRenderer)


standard_levels = {
    logging.FATAL,
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG,
}

valid_level_names = {
    'info',
    'debug',
    'failure',
    'fatal',
    'exception',
    'critical',
    'warn',
    'warning',
    'error',
    'err',
}


def test_level_map():
    for level in standard_levels:
        assert level in init.levels


def test_handled_level_names():
    assert set(valid_level_names) == set(init.level_aliases.keys())


class TestLogLevelProcessor:  # noqa: WPS214
    def test_call(self):
        mock = Mock(init.LogLevelProcessor)
        event = {'event': 'my_event'}
        method = 'my_method'

        init.LogLevelProcessor.__call__(mock, logger=None, method_name=method, event_dict=event)

        assert len(mock.mock_calls) == 2
        assert mock.mock_calls[0] == call.normalize_level(method, event)

    def test_filter_pass(self):
        processor = init.LogLevelProcessor(logging.INFO)
        event_dict = {'levelno': logging.FATAL, 'level': 'fatal'}
        assert processor.filter_on_level(event_dict) == event_dict

    def test_filter_filter(self):
        processor = init.LogLevelProcessor(logging.INFO)
        event_dict = {'levelno': logging.DEBUG, 'level': 'debug'}

        with pytest.raises(structlog.DropEvent):
            processor.filter_on_level(event_dict)

    def test_normalized_level(self):
        processor = init.LogLevelProcessor(logging.INFO)
        event_dict = {'levelno': logging.INFO, 'level': 'info'}

        out = processor.normalize_level(method_name='name', event_dict=event_dict.copy())

        assert event_dict == out

    def test_normalized_level_no_info_standard_method(self):
        processor = init.LogLevelProcessor(logging.INFO)
        event_dict: EventDict = {}

        out = processor.normalize_level(method_name='info', event_dict=event_dict.copy())

        assert out == {'level': 'info', 'levelno': logging.INFO}

    def test_normalized_level_no_info_abnormal_method(self):
        processor = init.LogLevelProcessor(logging.INFO)
        event_dict: EventDict = {}

        out = processor.normalize_level(method_name='haha', event_dict=event_dict.copy())

        assert out == {'level': 'info', 'levelno': logging.INFO}

    def test_normalized_level_levelno_only(self):
        processor = init.LogLevelProcessor(logging.INFO)
        event_dict = {'levelno': logging.FATAL}

        out = processor.normalize_level(method_name='name', event_dict=event_dict.copy())

        assert out == {'level': 'fatal', 'levelno': logging.FATAL}

    def test_normalized_level_levelname_only(self):
        processor = init.LogLevelProcessor(logging.INFO)
        event_dict = {'level': 'fatal'}

        out = processor.normalize_level(method_name='name', event_dict=event_dict.copy())

        assert out == {'level': 'fatal', 'levelno': logging.FATAL}
