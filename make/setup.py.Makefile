ifndef MK_SETUP
MK_SETUP=1

include make/env.Makefile

# SETUP

USES_PRIVATE_PYPI := $(shell $(READ_PYPROJECT_KEY) tool.poetry.source.name --check-only)

ifeq ($(USES_PRIVATE_PYPI),1)
PRIVATE_PYPI_NAME = $(shell $(READ_PYPROJECT_KEY) tool.poetry.source.name)
PRIVATE_PYPI_URL = $(shell $(READ_PYPROJECT_KEY) tool.poetry.source.url)

# poetry expects the environment variables to match the name of
# the repository, so we have to create dynamic env vars
#
# Example, your repository is called `otc`, poetry expects:
# - PYPI_HTTP_BASIC_OTC_USERNAME
# - PYPI_HTTP_BASIC_OTC_PASSWORD
#

# Currently this normalisation only transforms to uppercase
# if you have a more complicated name, say with hyphens, etc.
# you'll need to change this
PRIVATE_PYPI_NORMALISED_NAME = $(shell echo $(PRIVATE_PYPI_NAME) | tr a-z A-Z)

POETRY_USERNAME_ENV = POETRY_HTTP_BASIC_${PRIVATE_PYPI_NORMALISED_NAME}_USERNAME
POETRY_PASSWORD_ENV = POETRY_HTTP_BASIC_${PRIVATE_PYPI_NORMALISED_NAME}_PASSWORD

ifdef POETRY_USERNAME
POETRY_ENV += $(POETRY_USERNAME_ENV)=$(POETRY_USERNAME) $(POETRY_PASSWORD_ENV)=$(POETRY_PASSWORD)
endif

endif

ifeq ($(PLATFORM),darwin)
# For local usage on OSX
POETRY_ENV += LDFLAGS="-L$$(brew --prefix openssl)/lib"
endif


.PHONY: install-build-system production-setup dev-setup ci-setup cache-friendly-pyproject

install-build-system: ## Install poetry
	# We pass the variable through echo/xargs to avoid whitespacing issues
	$(READ_PYPROJECT_KEY) build-system.requires | xargs pip install


production-setup: install-build-system ## Install the dependencies for prod environments
	poetry config virtualenvs.in-project true
	@${POETRY_ENV} poetry install --no-interaction --no-ansi --no-dev


ci-setup: install-build-system ## Install the dependencies for CI environments
	@${POETRY_ENV} poetry install --no-interaction --no-ansi


dev-setup: install-build-system ## Install the dependencies for dev environments
	@${POETRY_ENV} poetry install
	./pre-commit.sh


cache-friendly-pyproject:
	sed -e 's/^version[[:space:]]*=.*$$/version = "0.0.1-cache-friendly"/g' pyproject.toml > pyproject.cachefriendly.toml
	mv pyproject.cachefriendly.toml pyproject.toml

endif
