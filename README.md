# logkit-py
![ci-badge](https://github.com/outcome-co/logkit-py/workflows/Release/badge.svg?branch=v0.4.0) ![version-badge](https://img.shields.io/badge/version-0.4.0-brightgreen)

Logging helpers.

## Installation

```sh
poetry add outcome-logkit
```

## Usage

`logkit` is a wrapper around [structlog](https://www.structlog.org/en/stable/) that configures it with the following:

- Sets log level based on `APP_ENV` environment variable
- Automatically outputs Stackdriver-compliant JSON to stdout when running in a GCP environment (AppEngine, CloudRun, GKE, etc.)
- Intercepts all messages sent to the standard library loggers and processes them transparently
- Configures structlog to provide async-safe context values

### Initialization
`logkit` needs to be initialized before being used. This initialization configures `structlog` and sets up the intercept for the standard logging library.

**Note** It's important to do this as early as possible in the program to ensure that no other imports start logging messages before the intercept has been configured. You can use `# isort:skip` to ensure `isort` doesn't reorder the import.

```py
# Important that this happens before any other imports
from outcome.logkit import init_logging  # isort:skip

init_logging()  # isort:skip
```

#### Log Level
You can provide a `level` parameter to `init_logging` to define the default log-level. You can use the built-in log levels from the `logging` module (e.g. `logging.INFO`). If you don't provide a level, it will automatically be set based on the `env.is_prod()` method from the [outcome-utils](https://github.com/outcome-co/utils-py/blob/master/src/outcome/utils/env.py) package.

```py
import logging

init_logging(level=logging.INFO)
```


#### Custom Processors
You can provide an array of your own [structlog processors](https://www.structlog.org/en/stable/processors.html) to `init_logging`. They will be merged into the processors provided by `logkit`.

```py
init_logging(processors=[my_custom_processor])
```

### Logging
To log with `logkit`, you can either use the standard library logging, or use the structlog interface. Both can be used to pass structured data to the log entries. Using the structlog interface is _marginally_ faster, since all the messages sent to the standard logging library are sent to structlog anyway.

```py
import logging
from outcome.logkit import get_logger

# Using the standard library
logger = logging.getLogger(__name__)
logger.info('my_message', user_id='1')

# Using the structlog interface
structured_logger = get_logger(__name__)
structured_logger.info('my_message', user_id='1')
```

#### Async-safe context vars
You can set "global" variables that are async safe using `outcome.logkit.context`.

```py
import logging
from outcome.logkit import get_logger, context

context.add(user_id='1')

structured_logger = get_logger(__name__)
structured_logger.info('my_message')  # user_id=1 will be added to this log event

context.remove('user_id')
```

## Development

Remember to run `./pre-commit.sh` when you clone the repository.
