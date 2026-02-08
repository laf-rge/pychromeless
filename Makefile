# Scripts directory
SCRIPTS_DIR := scripts

# Default environment for frontend deployment (matches Terraform workspace)
DEPLOY_ENV ?= prod

# Prerequisites checking
check-prerequisites:
	@$(SCRIPTS_DIR)/check-prerequisites.sh

check: check-prerequisites

# Development environment setup
install-dev:
	pip install -e ".[dev,quality]"

install-prod:
	pip install -e .

# Use modern approach by default
install: install-dev

# Testing targets
test: install-dev
	PYTHONPATH=src python -m pytest src/tests -v

test-parallel: install-dev
	PYTHONPATH=src python -m pytest src/tests -v -n auto

test-coverage: install-dev
	PYTHONPATH=src python -m pytest src/tests --cov=src --cov-report=html --cov-report=term

test-unit: install-dev
	PYTHONPATH=src python -m pytest src/tests -v -m "unit"

test-integration: install-dev
	PYTHONPATH=src python -m pytest src/tests -v -m "integration"

test-e2e: install-dev
	PYTHONPATH=src python -m pytest src/tests -v -m "e2e"

test-financial: install-dev
	PYTHONPATH=src python -m pytest src/tests -v -m "financial"

# Linting targets
lint-comprehensive: install-dev
	black --check src/
	isort --check-only src/
	flake8 src/
	mypy src/ --ignore-missing-imports
	bandit -r src/ -f json || true
	pylint src/ --output-format=json || true

# Enhanced lint target (backwards compatible)
lint: install-dev
	black --check src/
	isort --check-only src/
	flake8 src/
	mypy src/ --ignore-missing-imports

# New target that runs both linting and tests
test-all: lint test frontend-lint frontend-test

# CI target that includes linting
ci-test-all: lint ci-test

# Formatting
format: install-dev
	black src/
	isort src/

# CI/CD targets
ci-test: install-dev
	PYTHONPATH=src python -m pytest src/tests --cov=src --cov-report=xml --cov-report=term-missing

pre-commit-install: install-dev
	pre-commit install

# Security checking
security-check: install-dev
	bandit -r src/
	safety check

# Lambda dependency installation (using script)
install_lambda_deps: check-prerequisites
	@$(SCRIPTS_DIR)/install-lambda-deps.sh

# Lambda package building
websocket: ws_validate_token
	mkdir -p deploy && cd src && zip -r ../deploy/websocket.zip ws*.py auth_utils.py

ws_validate_token: install_lambda_deps
	mkdir -p deploy && cd build && \
		cp ../src/ws_validate_token.py . && \
		cp ../src/auth_utils.py . && \
		zip -r ../deploy/ws_validate_token.zip * && \
		rm ws_validate_token.py auth_utils.py

validate_token: install_lambda_deps
	mkdir -p deploy && cd build && \
		cp ../src/validate_token.py . && \
		cp ../src/auth_utils.py . && \
		zip -r ../deploy/validate_token.zip .

task_status: install_lambda_deps
	mkdir -p deploy && cd build && \
		cp ../src/task_status.py . && \
		cp ../src/logging_utils.py . && \
		zip -r ../deploy/task_status.zip * && \
		rm task_status.py logging_utils.py

# QuickBooks MCP server (Node.js Lambda)
QUICKBOOKS_MCP_DIR ?= ../quickbooks-mcp
qb-mcp:
	cd $(QUICKBOOKS_MCP_DIR) && npm run build:lambda
	mkdir -p deploy
	cp $(QUICKBOOKS_MCP_DIR)/dist-lambda/handler.mjs deploy/
	cd deploy && zip -j qb-mcp.zip handler.mjs && rm handler.mjs

# Build all Lambda packages
build-lambda: websocket validate_token task_status qb-mcp

# Frontend targets
frontend-install: check-prerequisites
	cd frontend && bun install --frozen-lockfile

frontend-build: frontend-install
	cd frontend && bun run build

frontend-test: frontend-install
	cd frontend && bun run test

frontend-lint: frontend-install
	cd frontend && bun run lint

frontend-e2e: frontend-install
	cd frontend && bun run test:e2e

frontend-e2e-ui: frontend-install
	cd frontend && bun run test:e2e:ui

frontend-e2e-headed: frontend-install
	cd frontend && bun run test:e2e:headed

# Frontend deployment (using script)
frontend-deploy: frontend-build check-prerequisites
	@DEPLOY_ENV=$(DEPLOY_ENV) $(SCRIPTS_DIR)/deploy-frontend.sh

# Frontend-only deployment (build + deploy)
deploy-frontend-only: frontend-deploy

frontend-clean:
	cd frontend && rm -rf node_modules dist

# Build everything without deploying
build-all: build-lambda frontend-build

# Deployment targets
deploy-docker: check-prerequisites
	@$(SCRIPTS_DIR)/deploy-docker.sh

deploy-terraform: check-prerequisites
	@$(SCRIPTS_DIR)/deploy-terraform.sh

# Deploy everything (original 'all' target behavior)
deploy-all: build-all deploy-docker deploy-terraform

# Legacy 'all' target for backwards compatibility
all: deploy-all

# Clean targets
clean:
	rm -rf build/*
	rm -rf deploy/*.zip deploy/*.base64sha256
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	$(MAKE) frontend-clean

# Help target (will be enhanced in next step)
help:
	@echo "Available targets:"
	@echo ""
	@echo "Prerequisites:"
	@echo "  check                 - Check for required development tools"
	@echo "  check-prerequisites   - Same as 'check'"
	@echo ""
	@echo "Development:"
	@echo "  install               - Install development dependencies"
	@echo "  install-prod          - Install production dependencies only"
	@echo "  format                - Format code with black and isort"
	@echo "  pre-commit-install   - Install pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  test                  - Run all tests"
	@echo "  test-all              - Run linting + tests"
	@echo "  test-parallel         - Run tests in parallel"
	@echo "  test-coverage         - Run tests with coverage report"
	@echo "  test-unit             - Run unit tests only"
	@echo "  test-integration      - Run integration tests only"
	@echo "  test-e2e              - Run end-to-end tests only"
	@echo "  test-financial        - Run financial calculation tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint                  - Run basic code quality checks"
	@echo "  lint-comprehensive    - Run comprehensive linting (includes pylint, bandit)"
	@echo "  security-check        - Run security vulnerability scanning"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci-test               - Run tests for CI/CD"
	@echo "  ci-test-all           - Run linting + tests for CI/CD"
	@echo ""
	@echo "Lambda Functions:"
	@echo "  build-lambda          - Build all Lambda packages"
	@echo "  websocket             - Build websocket Lambda package"
	@echo "  validate_token        - Build validate_token Lambda package"
	@echo "  task_status           - Build task_status Lambda package"
	@echo ""
	@echo "Frontend:"
	@echo "  frontend-install     - Install frontend dependencies (uses Bun)"
	@echo "  frontend-build        - Build frontend for production"
	@echo "  frontend-test        - Run frontend tests"
	@echo "  frontend-lint        - Run frontend linting"
	@echo "  frontend-e2e         - Run frontend E2E tests (Playwright)"
	@echo "  frontend-e2e-ui      - Run frontend E2E tests with Playwright UI"
	@echo "  frontend-e2e-headed  - Run frontend E2E tests in headed browser"
	@echo "  frontend-deploy      - Build and deploy frontend to Namecheap server"
	@echo "  deploy-frontend-only - Same as frontend-deploy (alias)"
	@echo "  frontend-clean       - Clean frontend build artifacts"
	@echo ""
	@echo "Deployment:"
	@echo "  build-all             - Build everything (Lambda + frontend) without deploying"
	@echo "  deploy-docker         - Build and push Docker image to ECR"
	@echo "  deploy-terraform     - Deploy infrastructure using Terraform"
	@echo "  deploy-all            - Build and deploy everything (Lambda + Docker + Terraform)"
	@echo "  all                   - Same as deploy-all (legacy, for backwards compatibility)"
	@echo ""
	@echo "Utilities:"
	@echo "  clean                 - Clean build artifacts and test outputs"
	@echo "  help                  - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make check                    - Check prerequisites"
	@echo "  make test-all                - Run linting and tests"
	@echo "  make deploy-frontend-only    - Build and deploy frontend only"
	@echo "  make build-lambda            - Build all Lambda packages"
	@echo "  make deploy-all              - Full deployment (build + deploy everything)"

.PHONY: check check-prerequisites install install-dev install-prod test test-parallel test-coverage test-unit test-integration test-e2e test-financial test-all lint lint-comprehensive format ci-test ci-test-all pre-commit-install security-check install_lambda_deps websocket ws_validate_token validate_token task_status build-lambda frontend-install frontend-build frontend-test frontend-lint frontend-e2e frontend-e2e-ui frontend-e2e-headed frontend-deploy deploy-frontend-only frontend-clean build-all deploy-docker deploy-terraform deploy-all all clean help
