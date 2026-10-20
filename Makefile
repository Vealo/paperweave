PYTHON ?= uv run --frozen python
PAPERWEAVE_CONFIG ?= config.toml
COMPOSE_PROJECT_NAME ?= paperweave
export PYTHONPATH := src
.DEFAULT_GOAL := help

.PHONY: init config-check up down restart logs ps migrate test storage-check help

init:
	$(PYTHON) -m paperweave.cli --config "$(PAPERWEAVE_CONFIG)" init

config-check:
	$(PYTHON) -m paperweave.cli --config "$(PAPERWEAVE_CONFIG)" config-check

up:
	$(PYTHON) -m paperweave.cli --config "$(PAPERWEAVE_CONFIG)" --project-name "$(COMPOSE_PROJECT_NAME)" up

down:
	$(PYTHON) -m paperweave.cli --config "$(PAPERWEAVE_CONFIG)" --project-name "$(COMPOSE_PROJECT_NAME)" down

restart:
	$(PYTHON) -m paperweave.cli --config "$(PAPERWEAVE_CONFIG)" --project-name "$(COMPOSE_PROJECT_NAME)" restart

logs:
	$(PYTHON) -m paperweave.cli --config "$(PAPERWEAVE_CONFIG)" --project-name "$(COMPOSE_PROJECT_NAME)" logs

ps:
	$(PYTHON) -m paperweave.cli --config "$(PAPERWEAVE_CONFIG)" --project-name "$(COMPOSE_PROJECT_NAME)" ps

migrate:
	$(PYTHON) -m paperweave.cli --config "$(PAPERWEAVE_CONFIG)" --project-name "$(COMPOSE_PROJECT_NAME)" migrate

test:
	$(PYTHON) -m paperweave.cli --config "$(PAPERWEAVE_CONFIG)" --project-name "$(COMPOSE_PROJECT_NAME)" test

storage-check:
	$(PYTHON) -m paperweave.cli --config "$(PAPERWEAVE_CONFIG)" --project-name "$(COMPOSE_PROJECT_NAME)" storage-check

help:
	$(PYTHON) -m paperweave.cli help
