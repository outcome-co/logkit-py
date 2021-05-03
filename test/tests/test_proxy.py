import logging
from unittest.mock import Mock, patch

from outcome.logkit.proxy import LoggingProxy

attribute_value = 321
method_value = '123'


class Target:
    def __init__(self) -> None:
        self.attribute = attribute_value

    def method(self):
        return method_value


@patch('outcome.logkit.proxy.get_logger', autospec=True)
class TestProxy:
    def test_proxy_attribute(self, mocked_get_logger: Mock):
        logger = Mock()
        mocked_get_logger.return_value = logger

        proxied = LoggingProxy(Target(), level=logging.FATAL, name='my_test')

        assert proxied.attribute == attribute_value
        mocked_get_logger.assert_called_once_with('my_test')

        logger.log.assert_called_once_with(
            'my_test.attribute',
            type='attribute',
            retval=attribute_value,
            levelno=logging.FATAL,
            logger='my_test.attribute',
        )

    def test_proxy_callable(self, mocked_get_logger: Mock):
        logger = Mock()
        mocked_get_logger.return_value = logger

        proxied = LoggingProxy(Target(), level=logging.FATAL, name='my_test')

        assert proxied.method() == method_value

        logger.log.assert_called_once_with(
            'my_test.method',
            type='method',
            args=(),
            kwargs={},
            retval=method_value,
            levelno=logging.FATAL,
            logger='my_test.method',
        )
