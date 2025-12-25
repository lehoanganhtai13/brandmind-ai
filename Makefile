.PHONY: help install install-chatbot install-indexer install-dev install-migration install-all
.PHONY: add-chatbot add-indexer add-shared add-core add-dev add-migration
.PHONY: sync update clean test format lint check
.PHONY: services-up services-down services-restart services-logs services-status

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

install-migration: ## Install migration dependencies only
	uv sync --group migration

install-all: ## Install all dependencies (chatbot + indexer + dev + migration)
	uv sync --group chatbot --group indexer --group dev --group migration

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

add-migration: ## Add package to migration group. Usage: make add-migration PKG=langchain
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required. Usage: make add-migration PKG=package-name"; exit 1; fi
	uv add --group migration $(PKG)

add-core-optional: ## Add optional dependency to core. Usage: make add-core-optional GROUP=group_name PKG=package_name
	@if [ -z "$(PKG)" ] || [ -z "$(GROUP)" ]; then echo "Error: PKG and GROUP are required."; exit 1; fi
	uv add --package core --optional $(GROUP) $(PKG)

remove-indexer: ## Remove package from indexer group. Usage: make remove-indexer PKG=package_name
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required."; exit 1; fi
	uv remove --group indexer $(PKG)

remove-chatbot: ## Remove package from chatbot group. Usage: make remove-chatbot PKG=package_name
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required."; exit 1; fi
	uv remove --group chatbot $(PKG)

remove-shared: ## Remove package from shared package. Usage: make remove-shared PKG=package_name
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required."; exit 1; fi
	cd src/shared && uv remove $(PKG)

remove-core: ## Remove package from core package. Usage: make remove-core PKG=package_name
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required."; exit 1; fi
	cd src/core && uv remove $(PKG)

remove-dev: ## Remove development dependency. Usage: make remove-dev PKG=package_name
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required."; exit 1; fi
	uv remove --group dev $(PKG)

remove-migration: ## Remove package from migration group. Usage: make remove-migration PKG=package_name
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required."; exit 1; fi
	uv remove --group migration $(PKG)

## Maintenance
sync: ## Sync dependencies with lock file
	uv sync

update: ## Update all dependencies
	uv lock --upgrade
	uv sync --group chatbot --group indexer --group dev

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

test-unit: ## Run unit tests only
	uv run pytest tests/unit/

format: ## Format code with ruff and black
	uv run ruff format src/
	uv run black src/

lint: ## Lint code with ruff and mypy
	uv run ruff check src/ --fix
	uv run mypy src/shared/src --ignore-missing-imports
	uv run mypy src/core/src --ignore-missing-imports
	uv run mypy src/config --ignore-missing-imports

security-check: ## Run security scan with bandit on src/ folder
	uv run bandit -r src/ -s B101,B603 -ll

secrets-baseline: ## Create/update secrets baseline (excludes .env files - they're allowed to have secrets)
	@echo "Creating baseline (excluding .env files from scan)..."
	@uv run detect-secrets scan --all-files --exclude-files '.venv/|venv/|\.git/|__pycache__/|\.pytest_cache/|\.mypy_cache/|node_modules/|data/|environments/\.env$$|\.env$$|\.env\..*$$|\.secrets\.baseline$$' > .secrets.baseline
	@echo "✓ Baseline created: .secrets.baseline"
	@echo "Note: .env files are excluded - they're allowed to contain secrets"

secrets-scan: ## Scan for NEW secrets in code (fails if found - excludes .env files)
	@if [ ! -f .secrets.baseline ]; then \
		echo "❌ Error: .secrets.baseline not found."; \
		echo "Run 'make secrets-baseline' first to create baseline."; \
		exit 1; \
	fi
	@echo "🔍 Scanning for secrets in code..."
	@uv run detect-secrets scan --all-files --exclude-files '.venv/|venv/|\.git/|__pycache__/|\.pytest_cache/|\.mypy_cache/|node_modules/|data/|environments/\.env$$|\.env$$|\.env\..*$$|\.secrets\.baseline$$' > /tmp/secrets-current-scan.json 2>&1
	@python3 scripts/compare_secrets.py
	@rm -f /tmp/secrets-current-scan.json

secrets-audit: ## Audit detected secrets interactively
	@if [ ! -f .secrets.baseline ]; then \
		echo "Error: .secrets.baseline not found. Run 'make secrets-baseline' first."; \
		exit 1; \
	fi
	uv run detect-secrets audit .secrets.baseline

typecheck: format lint security-check ## Run type checking, linting

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

## Docker Services
services-up: ## Start infrastructure services (SearXNG + Crawl4AI)
	cd infra && docker compose up -d --build

services-down: ## Stop infrastructure services
	cd infra && docker compose down

services-restart: ## Restart infrastructure services
	cd infra && docker compose restart

services-logs: ## Show logs from infrastructure services
	cd infra && docker compose logs -f

services-status: ## Show status of infrastructure services
	cd infra && docker compose ps

services-rebuild: ## Force rebuild all services without cache
	cd infra && docker compose build --no-cache && docker compose up -d

## Processing
.PHONY: parse-docs
parse-docs: ## Parse documents via CLI. Usage: make parse-docs [FILE=doc.pdf]
	@if [ -n "$(FILE)" ]; then \
		uv run parse-docs --file $(FILE); \
	else \
		uv run parse-docs; \
	fi

## Lock file
lock: ## Update lock file without installing
	uv lock

lock-upgrade: ## Upgrade all dependencies in lock file
	uv lock --upgrade

## Database Migration
.PHONY: backup-graph backup-vector backup-all restore-graph restore-vector restore-all

backup-graph: ## Backup FalkorDB graph to CSV files
	@echo "📦 Backing up FalkorDB graph..."
	@mkdir -p backups/falkordb
	uv run python scripts/migration/falkordb_backup.py knowledge_graph \
		--host localhost --port $${FALKORDB_PORT:-6380} \
		--username "$${FALKORDB_USERNAME:-brandmind}" \
		--password "$${FALKORDB_PASSWORD:-password}" \
		--output ./backups/falkordb
	@echo "✅ FalkorDB backup complete → ./backups/falkordb/"

backup-vector: ## Backup Milvus collections and download to local
	@echo "📦 Backing up Milvus collections..."
	@mkdir -p backups/milvus
	uv run --group migration python scripts/migration/milvus_backup.py backup \
		--name brandmind_backup \
		--collections "DocumentChunks,EntityDescriptions,RelationDescriptions" \
		--output ./backups/milvus \
		--minio-endpoint "localhost:$${MINIO_PORT:-9000}" \
		--minio-access-key "$${MINIO_ACCESS_KEY:-minioadmin}" \
		--minio-secret-key "$${MINIO_SECRET_KEY:-minioadmin_secret}"
	@echo "✅ Milvus backup complete → ./backups/milvus/"

backup-download-vector: ## Download existing Milvus backup from MinIO
	@echo "📥 Downloading Milvus backup from MinIO..."
	@mkdir -p backups/milvus
	uv run --group migration python scripts/migration/milvus_backup.py download \
		--name brandmind_backup \
		--output ./backups/milvus \
		--minio-endpoint "localhost:$${MINIO_PORT:-9000}" \
		--minio-access-key "$${MINIO_ACCESS_KEY:-minioadmin}" \
		--minio-secret-key "$${MINIO_SECRET_KEY:-minioadmin_secret}"
	@echo "✅ Milvus backup downloaded → ./backups/milvus/"

backup-all: backup-graph backup-vector ## Backup both FalkorDB and Milvus
	@echo ""
	@echo "✅ Full backup complete → ./backups/"
	@echo "📦 Package for migration: make backup-package"

backup-package: backup-all ## Backup all and create split zip package in backups/
	@echo "📦 Creating backup package..."
	@cd backups && zip -r backup.zip falkordb/ milvus/
	@echo "📦 Splitting into 40MB parts for GitHub..."
	@cd backups && split -b 40m backup.zip backup.zip.part.
	@rm -f backups/backup.zip
	@rm -rf backups/falkordb backups/milvus
	@echo "✅ Package ready: backups/backup.zip.part.* (use 'make restore-package' to restore)"

restore-graph: ## Restore FalkorDB graph from CSV backup
	@echo "🔄 Restoring FalkorDB graph..."
	@uv run python scripts/migration/falkordb_restore.py \
		--backup-dir ./backups/falkordb \
		--graph knowledge_graph \
		--host localhost --port $${FALKORDB_PORT:-6380} \
		--username "$${FALKORDB_USERNAME:-brandmind}" \
		--password "$${FALKORDB_PASSWORD:-password}"
	@echo "✅ FalkorDB restore complete"

restore-vector: ## Restore Milvus from local backup (upload to MinIO + restore)
	@echo "🔄 Restoring Milvus collections..."
	@uv run --group migration python scripts/migration/milvus_restore.py restore \
		--backup-dir ./backups/milvus/brandmind_backup \
		--name brandmind_backup \
		--minio-endpoint "localhost:$${MINIO_PORT:-9000}" \
		--minio-access-key "$${MINIO_ACCESS_KEY:-minioadmin}" \
		--minio-secret-key "$${MINIO_SECRET_KEY:-minioadmin_secret}"
	@echo "✅ Milvus restore complete"

restore-all: restore-graph restore-vector ## Restore both FalkorDB and Milvus
	@echo ""
	@echo "✅ Full restore complete"

restore-package: ## Merge split parts, extract, and restore all databases
	@echo "📦 Merging backup parts..."
	@test -f backups/backup.zip.part.aa || (echo "❌ backups/backup.zip.part.* not found" && exit 1)
	@cd backups && cat backup.zip.part.* > backup.zip
	@echo "📦 Extracting backup package..."
	@cd backups && unzip -o backup.zip
	@rm -f backups/backup.zip
	@echo "🔄 Restoring databases..."
	@$(MAKE) restore-graph
	@$(MAKE) restore-vector
	@echo ""
	@echo "✅ Full migration restore complete"