.PHONY: install run-local check format test-unit test

# Commands
RUN := poetry run
COMMAND := docker compose

# Apps
API_APP := app/api
CORE_APP := app/core

# Tests
TEST_UNIT := tests/unit

ALL_APPS := $(CORE_APP)
ALL_TESTS := $(TEST_UNIT)

# Prepare the local development environment
setup:
	poetry install
	poetry run pre-commit install
	$(COMMAND) build

# Run project on local machine
run-local:
	$(COMMAND) up

# Run all tasks the CI runs
ci:	format check 

# Run all static checks
check:
	poetry check
	! poetry install --dry-run | grep "^Warning:"
	$(RUN) mypy $(ALL_APPS)
	$(RUN) flake8 $(ALL_APPS)
	$(RUN) black --diff --check $(ALL_APPS)
	$(RUN) isort --profile black --check $(ALL_APPS)
	$(RUN) ruff check $(ALL_APPS)

# Automatically format the code and sort imports
format:
	$(RUN) black $(ALL_APPS)
	$(RUN) isort --profile black $(ALL_APPS)
	$(RUN) ruff format $(ALL_APPS)

test-unit:
	$(RUN) pytest

test:
	$(RUN) pytest $(ALL_TEST)
