from importlib import reload
from unittest.mock import Mock

import pytest
import structlog
from outcome.logkit import context

mock_logger = Mock()


def mock_logger_factory():
    return mock_logger


@pytest.fixture(autouse=True)
def reload_structlog():
    reload(structlog)
    structlog.reset_defaults()
    structlog.configure(processors=[structlog.contextvars.merge_contextvars], logger_factory=mock_logger_factory)


def test_context():
    logger = structlog.get_logger()

    logger.info('without_context')

    context.add(var_a='a', var_b='b')
    logger.info('with_context')

    context.remove('var_a')
    logger.info('with_partial_context')

    context.clear()
    logger.info('without_context')

    assert len(mock_logger.mock_calls) == 4
    assert mock_logger.mock_calls[0].kwargs == {'event': 'without_context'}
    assert mock_logger.mock_calls[1].kwargs == {'event': 'with_context', 'var_a': 'a', 'var_b': 'b'}
    assert mock_logger.mock_calls[2].kwargs == {'event': 'with_partial_context', 'var_b': 'b'}
    assert mock_logger.mock_calls[3].kwargs == {'event': 'without_context'}
