ifndef MK_ENV_PY
MK_ENV_PY=1

# Have we found a read-toml yet?
READ_PYPROJECT_KEY = 

# Test if read-toml is properly installed
HAS_LOCAL_READ_TOML := $(shell (read-toml --help 2>&1 > /dev/null) && echo 1 || echo 0)

ifeq ($(HAS_LOCAL_READ_TOML),1)
# Environment has read-toml installed, use it to read pyroject.toml
READ_PYPROJECT_KEY = read-toml --path pyproject.toml --key
endif

# If we haven't found a read-toml yet, let's try installing it in an isolated directory
ifeq ($(READ_PYPROJECT_KEY),)
READ_TOML_ENV = .cache/read-toml
READ_TOML_EXECUTABLE_PATH = $(READ_TOML_ENV)/bin/read-toml

# Test if read-toml is properly installed - sometimes it isn't...
HAS_LOCAL_READ_TOML = $(shell test -f $(READ_TOML_EXECUTABLE_PATH) && PYTHONPATH=$(READ_TOML_ENV) $(READ_TOML_EXECUTABLE_PATH) --help > /dev/null 2>&1 && echo 1 || echo 0)

ifeq ($(HAS_LOCAL_READ_TOML),0)
READ_TOML_INSTALL := $(shell pip install -t $(READ_TOML_ENV) --no-cache --upgrade outcome-read-toml 2> /dev/null)
endif

# We do this two step check since some environments can't find read-toml, even after explicitly installing it
ifneq ($(HAS_LOCAL_READ_TOML),0)
READ_PYPROJECT_KEY = PYTHONPATH=$(READ_TOML_ENV) $(READ_TOML_EXECUTABLE_PATH) --path pyproject.toml --key
endif

endif

# If we haven't found a read-toml yet, let's try docker
ifeq ($(READ_PYPROJECT_KEY),)
HAS_DOCKER = $(shell (which docker 2>&1 > /dev/null) && echo 1 || echo 0)

ifeq ($(HAS_DOCKER),1)
READ_PYPROJECT_KEY = docker run --rm -v $$(pwd):/work/ outcomeco/action-read-toml:latest --path /work/pyproject.toml --key
endif
endif

# If we haven't found it yet, time to give up - but this will only fail if/when READ_PYPROJECT_KEY is called
ifeq ($(READ_PYPROJECT_KEY),)
$(READ_PYPROJECT_KEY) = $(error Cannot use read-toml in the environment)
endif

endif
