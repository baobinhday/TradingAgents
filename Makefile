.DEFAULT_GOAL := help

# =============================================================================
# Configuration & Environment Detection
# =============================================================================
VENV ?= .venv
VENV_BIN ?= $(VENV)/bin
SYSTEM_PYTHON ?= $(shell which python3 2>/dev/null || which python)

# Auto-detect local virtualenv if present
ifneq ($(wildcard $(VENV_BIN)/python),)
    PY := $(VENV_BIN)/python
    PIP := $(VENV_BIN)/pip
    PYTEST := $(VENV_BIN)/pytest
    RUFF := $(VENV_BIN)/ruff
    TRADINGAGENTS := $(VENV_BIN)/tradingagents
else
    PY := $(SYSTEM_PYTHON)
    PIP := pip
    PYTEST := pytest
    RUFF := ruff
    TRADINGAGENTS := tradingagents
endif

NPM ?= npm

# Terminal colors for help output
CYAN   := \033[36m
GREEN  := \033[32m
YELLOW := \033[33m
RESET  := \033[0m
BOLD   := \033[1m

# =============================================================================
# Help / Menu
# =============================================================================
.PHONY: help
help: ## Show this help message
	@echo "$(BOLD)TradingAgents Management Commands$(RESET)"
	@echo ""
	@echo "$(BOLD)Usage:$(RESET) make $(CYAN)<target>$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} \
		/^##@/ { printf "\n$(BOLD)$(YELLOW)%s:$(RESET)\n", substr($$0, 5) } \
		/^[a-zA-Z_-]+:.*?## / { printf "  $(CYAN)%-18s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

##@ Setup & Installation
.PHONY: venv install install-web install-all

venv: ## Create Python virtual environment (.venv)
	@echo "$(GREEN)Creating virtual environment in $(VENV)...$(RESET)"
	$(SYSTEM_PYTHON) -m venv $(VENV)
	@echo "$(GREEN)Virtual environment ready. Run 'source $(VENV_BIN)/activate' to activate.$(RESET)"

install: ## Install python dependencies in editable mode [dev,web]
	@echo "$(GREEN)Installing Python package in editable mode with dev & web extras...$(RESET)"
	$(PIP) install -e ".[dev,web]"

install-web: ## Install frontend node modules in web/
	@echo "$(GREEN)Installing web dependencies with $(NPM)...$(RESET)"
	cd web && $(NPM) install

install-all: install install-web ## Install both Python and Web dependencies

##@ Execution & Web Console
.PHONY: cli web web-no-open web-dev web-ui-dev

cli: ## Launch interactive CLI interface
	$(PY) -m cli.main

web: ## Launch Web Console and auto-open browser at http://127.0.0.1:8000
	$(PY) -m cli.main web

web-no-open: ## Launch Web Console without opening browser (headless/server mode)
	$(PY) -m cli.main web --no-open

web-dev: ## Launch backend FastAPI in development mode with auto-reload
	$(PY) -m cli.main web --dev --no-open

web-ui-dev: ## Launch Vite development server with hot-reload (port 5173)
	cd web && $(NPM) run dev

SRC_DIRS ?= tradingagents cli tests

##@ Testing & Code Quality
.PHONY: test test-unit test-api lint lint-fix format check

test: ## Run all tests
	$(PYTEST)

test-unit: ## Run unit tests only
	$(PYTEST) -m unit

test-api: ## Run API & Web Console tests
	$(PYTEST) tests/test_api.py

lint: ## Run ruff linter check on project sources
	$(RUFF) check $(SRC_DIRS)

lint-fix: ## Run ruff linter with auto-fix on project sources
	$(RUFF) check --fix $(SRC_DIRS)

format: ## Format codebase with ruff
	$(RUFF) format $(SRC_DIRS)

check: lint ## Run lint and tests
	$(PYTEST)

##@ Docker & Distribution
.PHONY: build-web build-dist docker-build docker-run docker-ollama

build-web: ## Build frontend assets into web/dist
	@echo "$(GREEN)Building production frontend assets...$(RESET)"
	cd web && $(NPM) run build

build-dist: ## Build Python distribution packages (wheel, sdist)
	@echo "$(GREEN)Building Python distribution packages...$(RESET)"
	$(PY) -m pip install --upgrade build
	$(PY) -m build

docker-build: ## Build Docker container image
	docker compose build

docker-run: ## Run TradingAgents CLI inside Docker container
	docker compose run --rm tradingagents

docker-ollama: ## Run TradingAgents with local Ollama inside Docker
	docker compose --profile ollama run --rm tradingagents-ollama

##@ Cleanup
.PHONY: clean clean-all

clean: ## Remove temporary python cache, test artifacts, and build folders
	@echo "$(YELLOW)Cleaning caches and temporary files...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache build dist .coverage htmlcov

clean-all: clean ## Clean caches, virtualenv, and node_modules
	@echo "$(YELLOW)Removing .venv and web/node_modules...$(RESET)"
	rm -rf $(VENV) web/node_modules
