# ═══════════════════════════════════════════════════════════════════════════
# Aurora AI Refactor Assistant - Self-Documenting Makefile
# ═══════════════════════════════════════════════════════════════════════════
# Author: Ruslan Magana (ruslanmv.com)
# License: Apache 2.0
#
# This Makefile provides convenient commands for development, testing, and
# deployment. All targets include inline documentation accessible via 'make help'.
# ═══════════════════════════════════════════════════════════════════════════

.DEFAULT_GOAL := help
.PHONY: help install install-dev start clean test lint format audit security docker-build docker-run

# ANSI Colors for beautiful output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m
BOLD := \033[1m

##@ General

help: ## Display this help message with available targets
	@echo "$(BOLD)$(CYAN)╔═══════════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(BOLD)$(CYAN)║           Aurora AI Refactor Assistant - Makefile            ║$(RESET)"
	@echo "$(BOLD)$(CYAN)╚═══════════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "$(BOLD)Usage:$(RESET) make $(CYAN)<target>$(RESET)\n\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(BOLD)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	@echo ""

##@ Installation & Setup

install: ## Install production dependencies using uv
	@echo "$(GREEN)Installing production dependencies with uv...$(RESET)"
	uv pip install -e .

install-dev: ## Install all dependencies including dev tools
	@echo "$(GREEN)Installing all dependencies (including dev tools)...$(RESET)"
	uv pip install -e ".[dev,server]"
	@echo "$(GREEN)Installing pre-commit hooks...$(RESET)"
	pre-commit install
	@echo "$(BOLD)$(GREEN)✅ Development environment ready!$(RESET)"

##@ Development

start: ## Start Aurora CLI (alias for 'aurora --help')
	@echo "$(CYAN)Launching Aurora CLI...$(RESET)"
	aurora --help

serve: ## Start Aurora API server
	@echo "$(CYAN)Starting Aurora API server on http://localhost:8000$(RESET)"
	uvicorn aurora.api.server:app --reload --host 0.0.0.0 --port 8000

##@ Code Quality

lint: ## Run ruff linter and check code quality
	@echo "$(YELLOW)Running ruff linter...$(RESET)"
	ruff check src/ tests/
	@echo "$(GREEN)✅ Linting complete$(RESET)"

format: ## Format code with ruff
	@echo "$(YELLOW)Formatting code with ruff...$(RESET)"
	ruff format src/ tests/
	ruff check --fix src/ tests/
	@echo "$(GREEN)✅ Code formatted$(RESET)"

typecheck: ## Run mypy type checker
	@echo "$(YELLOW)Running mypy type checker...$(RESET)"
	mypy src/aurora/
	@echo "$(GREEN)✅ Type checking complete$(RESET)"

##@ Testing

test: ## Run test suite with pytest
	@echo "$(YELLOW)Running test suite...$(RESET)"
	pytest tests/ -v --cov=aurora --cov-report=term-missing
	@echo "$(GREEN)✅ Tests complete$(RESET)"

test-fast: ## Run tests without coverage (faster)
	@echo "$(YELLOW)Running fast tests...$(RESET)"
	pytest tests/ -v -x
	@echo "$(GREEN)✅ Fast tests complete$(RESET)"

test-watch: ## Run tests in watch mode
	@echo "$(YELLOW)Running tests in watch mode...$(RESET)"
	pytest-watch tests/ -v

##@ Security & Audit

security: ## Run security audit with bandit
	@echo "$(YELLOW)Running security audit with bandit...$(RESET)"
	bandit -r src/aurora/ -c pyproject.toml
	@echo "$(GREEN)✅ Security audit complete$(RESET)"

audit: lint typecheck security test ## Run complete audit: lint, typecheck, security, tests
	@echo ""
	@echo "$(BOLD)$(GREEN)╔═══════════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(BOLD)$(GREEN)║              ✅ COMPLETE AUDIT PASSED ✅                       ║$(RESET)"
	@echo "$(BOLD)$(GREEN)╚═══════════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""

##@ Docker

docker-build: ## Build production Docker image
	@echo "$(CYAN)Building Docker image: aurora-refactor:latest$(RESET)"
	docker build -t aurora-refactor:latest -f Dockerfile .
	@echo "$(GREEN)✅ Docker image built successfully$(RESET)"

docker-run: ## Run Aurora in Docker container
	@echo "$(CYAN)Running Aurora in Docker container...$(RESET)"
	docker run --rm -it \
		--env-file .env \
		-v $(PWD):/workspace \
		aurora-refactor:latest \
		aurora --help

docker-shell: ## Open shell in Docker container
	@echo "$(CYAN)Opening shell in Docker container...$(RESET)"
	docker run --rm -it \
		--env-file .env \
		-v $(PWD):/workspace \
		--entrypoint /bin/bash \
		aurora-refactor:latest

##@ Cleanup

clean: ## Remove build artifacts, cache, and temporary files
	@echo "$(YELLOW)Cleaning build artifacts...$(RESET)"
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -rf htmlcov/ .coverage coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "$(GREEN)✅ Cleanup complete$(RESET)"

clean-all: clean ## Remove all generated files including venv
	@echo "$(YELLOW)Removing virtual environment...$(RESET)"
	rm -rf .venv/
	@echo "$(GREEN)✅ Deep cleanup complete$(RESET)"

##@ Documentation

docs-serve: ## Serve documentation locally (if using mkdocs)
	@echo "$(CYAN)Serving documentation at http://localhost:8080$(RESET)"
	mkdocs serve -a localhost:8080

##@ Release

build: clean ## Build distribution packages
	@echo "$(YELLOW)Building distribution packages...$(RESET)"
	python -m build
	@echo "$(GREEN)✅ Build complete - check dist/ directory$(RESET)"

publish-test: build ## Publish to TestPyPI
	@echo "$(YELLOW)Publishing to TestPyPI...$(RESET)"
	twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI (production)
	@echo "$(RED)$(BOLD)Publishing to PyPI (production)...$(RESET)"
	@echo "$(YELLOW)Press Ctrl+C to cancel, or Enter to continue$(RESET)"
	@read -r
	twine upload dist/*
