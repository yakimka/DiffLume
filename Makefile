SHELL:=/usr/bin/env bash

RUN=docker compose exec -it devtools

.PHONY: all
all: help

.PHONY: start-devtools
start-devtools:  ## Start devtools container
	docker compose up -d devtools

.PHONY: stop-devtools
stop-devtools:  ## Stop devtools container
	docker compose stop devtools

.PHONY: pre-commit
pre-commit:  ## Run pre-commit with args
	$(RUN) poetry run pre-commit $(args)

.PHONY: poetry
poetry:  ## Run poetry with args
	$(RUN) poetry $(args)

.PHONY: lint
lint:  ## Run flake8, mypy, other linters and verify formatting
	@make pre-commit args="run --all-files"
	@make mypy

.PHONY: mypy
mypy:  ## Run mypy
	$(RUN) poetry run mypy

.PHONY: test
test:  ## Run tests
	$(RUN) poetry run pytest --cov
	$(RUN) poetry run pytest --dead-fixtures

.PHONY: package
package:  ## Run packages (dependencies) checks
	$(RUN) poetry check
	$(RUN) poetry run pip check

.PHONY: build-package
build-package:  ## Run packages (dependencies) checks
	$(RUN) poetry build
	$(RUN) poetry export --format=requirements.txt --output=dist/requirements.txt

.PHONY: checks
checks: lint package test  ## Run linting and tests

.PHONY: run-ci
run-ci:  ## Run CI locally
	$(RUN) ./ci.sh

.PHONY: clean
clean:  ## Clean up
	rm -rf dist
	rm -rf htmlcov
	rm -f .coverage coverage.xml

.PHONY: clean-all
clean-all:  ## Clean up all
	@make clean
	rm -rf .cache
	rm -rf .mypy_cache
	rm -rf .pytest_cache

.PHONY: bash
bash:  ## Run bash
	$(RUN) bash

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
