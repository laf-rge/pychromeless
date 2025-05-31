all: websocket validate_token task_status
	@if [ $$? -eq 0 ]; then \
		aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 262877227567.dkr.ecr.us-east-2.amazonaws.com && \
		DOCKER_BUILDKIT=1 docker build --platform linux/amd64 -t wmc . --no-cache && \
		docker tag wmc:latest 262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest && \
		docker push 262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest && \
		cd terraform && \
			terraform apply; \
	else \
		echo "websocket, validate_token, or task_status failed, stopping execution"; \
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

lint: install-dev
	black --check src/
	isort --check-only src/
	flake8 src/
	mypy src/ --ignore-missing-imports

format: install-dev
	black src/
	isort src/

# CI/CD targets
ci-test: install-dev
	PYTHONPATH=src python -m pytest src/tests --cov=src --cov-report=xml --cov-report=term-missing

pre-commit-install: install-dev
	pre-commit install

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

clean:
	rm -rf build/*
	rm -rf deploy/*.zip deploy/*.base64sha256
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

help:
	@echo "Available targets:"
	@echo "  install           - Install development dependencies"
	@echo "  install-prod      - Install production dependencies only"
	@echo "  test              - Run all tests"
	@echo "  test-parallel     - Run tests in parallel"
	@echo "  test-coverage     - Run tests with coverage report"
	@echo "  test-unit         - Run unit tests only"
	@echo "  test-integration  - Run integration tests only"
	@echo "  test-e2e          - Run end-to-end tests only"
	@echo "  test-financial    - Run financial calculation tests only"
	@echo "  lint              - Run code quality checks"
	@echo "  format            - Format code with black and isort"
	@echo "  ci-test           - Run tests for CI/CD"
	@echo "  clean             - Clean build artifacts and test outputs"
	@echo "  help              - Show this help message"
