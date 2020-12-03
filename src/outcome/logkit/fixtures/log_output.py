"""Log output fixtures.

To capture log output during tests, you can use `log_output` fixture.
If you need to add custom processors or define `log_level`, please use `log_level` and `log_processors` fixtures.

Example:
    @pytest.mark.usefixtures('configure_structlog')
    def test_log_output(log_ouput):
        assert log_output.entries == []
        # do something
        assert log_output.entries == [...]

"""
import logging

import pytest
import structlog
from outcome.logkit.init import get_final_processors
from structlog.testing import LogCapture


@pytest.fixture
def log_output():  # pragma: no cover
    return LogCapture()


@pytest.fixture
def log_level():  # pragma: no cover
    return logging.DEBUG


@pytest.fixture
def log_processors(log_output):  # pragma: no cover
    return [log_output]


@pytest.fixture
def configure_structlog(log_level, log_processors):  # pragma: no cover
    processors = get_final_processors(log_level, log_processors)
    structlog.configure(processors=processors)
