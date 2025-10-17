.PHONY: help install install-chatbot install-indexer install-dev install-all
.PHONY: add-chatbot add-indexer add-shared add-core add-dev
.PHONY: sync update clean test format lint check

# Default target
.DEFAULT_GOAL := help

## Help
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

## Installation
install: ## Install base dependencies (shared + core only)
	uv sync

install-chatbot: ## Install dependencies for chatbot service
	uv sync --group chatbot --group dev

install-indexer: ## Install dependencies for indexer service
	uv sync --group indexer --group dev

install-dev: ## Install development dependencies only
	uv sync --group dev

install-all: ## Install all dependencies (chatbot + indexer + dev)
	uv sync --group chatbot --group indexer --group dev

## Package Management
add-chatbot: ## Add package to chatbot group. Usage: make add-chatbot PKG=langchain
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required. Usage: make add-chatbot PKG=package-name"; exit 1; fi
	uv add --group chatbot $(PKG)

add-indexer: ## Add package to indexer group. Usage: make add-indexer PKG=elasticsearch
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required. Usage: make add-indexer PKG=package-name"; exit 1; fi
	uv add --group indexer $(PKG)

add-shared: ## Add package to shared package. Usage: make add-shared PKG=fastapi
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required. Usage: make add-shared PKG=package-name"; exit 1; fi
	cd src/shared && uv add $(PKG)

add-core: ## Add package to core package. Usage: make add-core PKG=sqlalchemy
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required. Usage: make add-core PKG=package-name"; exit 1; fi
	cd src/core && uv add $(PKG)

add-dev: ## Add development dependency. Usage: make add-dev PKG=pytest-asyncio
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required. Usage: make add-dev PKG=package-name"; exit 1; fi
	uv add --group dev $(PKG)

## Maintenance
sync: ## Sync dependencies with lock file
	uv sync

update: ## Update all dependencies
	uv lock --upgrade
	uv sync

clean: ## Clean cache and virtual environment
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

## Development
test: ## Run tests
	uv run pytest tests/ -v

test-watch: ## Run tests in watch mode
	uv run pytest-watch tests/

format: ## Format code with black and isort
	uv run black src/ tests/
	uv run isort src/ tests/

lint: ## Lint code with flake8 and mypy
	uv run flake8 src/
	uv run mypy src/

check: format lint test ## Run format, lint, and test

## Info
show-deps: ## Show installed packages
	uv pip list

show-tree: ## Show dependency tree
	uv tree

## Python Shell
shell: ## Start Python shell with environment
	uv run python

ipython: ## Start IPython shell
	uv run ipython

## Lock file
lock: ## Update lock file without installing
	uv lock

lock-upgrade: ## Upgrade all dependencies in lock file
	uv lock --upgrade