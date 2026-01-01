all: websocket validate_token task_status frontend-build
	@if [ $$? -eq 0 ]; then \
		aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 262877227567.dkr.ecr.us-east-2.amazonaws.com && \
		DOCKER_BUILDKIT=1 docker build --platform linux/amd64 -t wmc . --no-cache && \
		docker tag wmc:latest 262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest && \
		docker push 262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest && \
		cd terraform && \
			terraform apply; \
	else \
		echo "websocket, validate_token, task_status, or frontend-build failed, stopping execution"; \
		exit 1; \
	fi

# Development environment setup
install-dev:
	pip install -e ".[dev,quality]"

install-prod:
	pip install -e .

# Use modern approach by default
install: install-dev

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

# Add comprehensive linting with additional tools
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
test-all: lint test

# CI target that includes linting
ci-test-all: lint ci-test

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

install_lambda_deps:
	mkdir -p build && cd build && \
		pip install --upgrade \
			--platform manylinux2014_x86_64 \
			--only-binary :all: \
			--implementation cp \
			--target ./ \
			pyjwt \
			cryptography \
			cffi

# Frontend targets
frontend-install:
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

# Default environment for frontend deployment (matches Terraform workspace)
DEPLOY_ENV ?= prod

frontend-deploy: frontend-build
	@echo "Deploying frontend to Namecheap..."
	@HOST=$$(aws ssm get-parameter --name "/$(DEPLOY_ENV)/frontend/namecheap/host" --query "Parameter.Value" --output text) && \
	REMOTE_USER=$$(aws ssm get-parameter --name "/$(DEPLOY_ENV)/frontend/namecheap/user" --query "Parameter.Value" --output text) && \
	REMOTE_PATH=$$(aws ssm get-parameter --name "/$(DEPLOY_ENV)/frontend/namecheap/path" --query "Parameter.Value" --output text) && \
	PORT=$$(aws ssm get-parameter --name "/$(DEPLOY_ENV)/frontend/namecheap/port" --query "Parameter.Value" --output text) && \
	KEY_FILE=$$(mktemp) && \
	aws ssm get-parameter --name "/$(DEPLOY_ENV)/frontend/namecheap/ssh_key" --with-decryption --query "Parameter.Value" --output text > $$KEY_FILE && \
	chmod 600 $$KEY_FILE && \
	rsync -avz --delete \
		-e "ssh -i $$KEY_FILE -p $$PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" \
		frontend/dist/ \
		"$$REMOTE_USER@$$HOST:$$REMOTE_PATH/" && \
	rm -f $$KEY_FILE && \
	echo "Deployed to $$HOST:$$REMOTE_PATH"

frontend-clean:
	cd frontend && rm -rf node_modules dist

clean:
	rm -rf build/*
	rm -rf deploy/*.zip deploy/*.base64sha256
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	$(MAKE) frontend-clean

help:
	@echo "Available targets:"
	@echo "  install           - Install development dependencies"
	@echo "  install-prod      - Install production dependencies only"
	@echo "  test              - Run all tests"
	@echo "  test-all          - Run linting + tests"
	@echo "  test-parallel     - Run tests in parallel"
	@echo "  test-coverage     - Run tests with coverage report"
	@echo "  test-unit         - Run unit tests only"
	@echo "  test-integration  - Run integration tests only"
	@echo "  test-e2e          - Run end-to-end tests only"
	@echo "  test-financial    - Run financial calculation tests only"
	@echo "  lint              - Run basic code quality checks"
	@echo "  lint-comprehensive - Run comprehensive linting (includes pylint, bandit)"
	@echo "  security-check    - Run security vulnerability scanning"
	@echo "  format            - Format code with black and isort"
	@echo "  ci-test           - Run tests for CI/CD"
	@echo "  ci-test-all       - Run linting + tests for CI/CD"
	@echo "  pre-commit-install - Install pre-commit hooks"
	@echo "  frontend-install  - Install frontend dependencies (uses Bun)"
	@echo "  frontend-build    - Build frontend for production"
	@echo "  frontend-test     - Run frontend tests"
	@echo "  frontend-lint     - Run frontend linting"
	@echo "  frontend-e2e      - Run frontend E2E tests (Playwright)"
	@echo "  frontend-e2e-ui   - Run frontend E2E tests with Playwright UI"
	@echo "  frontend-e2e-headed - Run frontend E2E tests in headed browser"
	@echo "  frontend-deploy   - Deploy frontend to Namecheap server"
	@echo "  frontend-clean    - Clean frontend build artifacts"
	@echo "  clean             - Clean build artifacts and test outputs"
	@echo "  help              - Show this help message"
