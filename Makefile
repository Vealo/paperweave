PYTHON ?= uv run --frozen python
PAPERWEAVE_CONFIG ?= config.toml
COMPOSE_PROJECT_NAME ?= paperweave
export PYTHONPATH := src

.PHONY: init config-check up down restart logs ps migrate test help

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

help:
	$(PYTHON) -m paperweave.cli help
