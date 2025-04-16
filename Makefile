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

install-dev:
	pip install -r requirements.txt

test: install-dev
	PYTHONPATH=src python -m unittest discover -s src/tests -v

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
