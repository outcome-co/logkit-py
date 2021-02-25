from importlib import reload

import pytest
import structlog
from outcome.logkit import get_logger


@pytest.fixture(autouse=True)
def reload_structlog():
    reload(structlog)
    structlog.reset_defaults()


def test_get_unconfigured():
    with pytest.raises(Exception):
        get_logger('foo')


def test_get_configured():
    structlog.configure()
    get_logger('foo')
