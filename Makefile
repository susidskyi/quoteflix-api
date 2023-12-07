.PHONY: install run-local check format test-unit test

# Commands
RUN := poetry run

# Apps
CORE_APP := api

# Tests
TEST_UNIT := tests/unit

ALL_APPS := $(CORE_APP)
ALL_TESTS := $(TEST_UNIT)

# Prepare the local development environment
setup:
	poetry install
	poetry run pre-commit install
	docker-compose build

# Run project on local machine
run-local:
	docker-compose up

# Run all tasks the CI runs
ci:	format check 

# Run all static checks
check:
	poetry check
	! poetry install --dry-run | grep "^Warning:"
	$(RUN) mypy $(ALL_APPS)
	$(RUN) flake8 $(ALL_APPS)
	$(RUN) black --diff --check $(ALL_APPS)
	$(RUN) isort --check $(ALL_APPS)

# Automatically format the code and sort imports
format:
	$(RUN) black $(ALL_APPS)
	$(RUN) isort $(ALL_APPS)

test-unit:
	$(RUN) pytest

test:
	$(RUN) pytest $(ALL_TEST)
