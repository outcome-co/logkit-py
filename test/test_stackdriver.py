import json
from datetime import datetime
from importlib import reload
from unittest.mock import Mock

import pytest
import structlog
from freezegun import freeze_time
from outcome.logkit.stackdriver import StackdriverRenderer

mock_logger = Mock()


def mock_logger_factory():
    return mock_logger


@pytest.fixture(autouse=True)
def reload_structlog():
    reload(structlog)
    structlog.reset_defaults()
    structlog.configure(processors=[StackdriverRenderer()], logger_factory=mock_logger_factory)


@pytest.fixture(autouse=True)
def reset_mocked_logger():
    mock_logger.reset_mock()


@freeze_time('2020-10-12')
def test_basic_render():
    logger = structlog.get_logger()
    logger.info('test_message')

    assert len(mock_logger.mock_calls) == 1

    structured_message = mock_logger.mock_calls[0].args[0]
    parsed = json.loads(structured_message)

    assert parsed['message'] == 'test_message'
    assert parsed['timestamp'] == '2020-10-12T00:00:00Z'


def test_level():
    logger = structlog.get_logger()
    logger.info('test_message', level='info')

    assert len(mock_logger.mock_calls) == 1

    structured_message = mock_logger.mock_calls[0].args[0]
    parsed = json.loads(structured_message)

    assert parsed['severity'] == 'info'


def test_event():
    logger = structlog.get_logger()
    logger.info(level='info')

    assert len(mock_logger.mock_calls) == 1

    structured_message = mock_logger.mock_calls[0].args[0]
    parsed = json.loads(structured_message)

    assert parsed['message'] == ''


@freeze_time('2020-01-01')
def test_time():
    logger = structlog.get_logger()
    logger.info(timestamp=datetime.now().timestamp())

    assert len(mock_logger.mock_calls) == 1

    structured_message = mock_logger.mock_calls[0].args[0]
    parsed = json.loads(structured_message)

    assert parsed['timestamp'] == '2020-01-01T00:00:00Z'


def test_invalid_time():
    logger = structlog.get_logger()
    logger.info(timestamp='2020/10/12')

    assert len(mock_logger.mock_calls) == 1

    structured_message = mock_logger.mock_calls[0].args[0]
    parsed = json.loads(structured_message)

    assert parsed['timestamp'] == '2020/10/12'
