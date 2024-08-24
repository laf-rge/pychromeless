all: websocket validate_token
	@if [ $$? -eq 0 ]; then \
		aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 262877227567.dkr.ecr.us-east-2.amazonaws.com && \
		docker build -t wmc . --platform=linux/amd64 --no-cache && \
		docker tag wmc:latest 262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest && \
		docker push 262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest && \
		cd terraform && \
			terraform apply; \
	else \
		echo "websocket or validate_token failed, stopping execution"; \
		exit 1; \
	fi

websocket:
	cd src && zip -r ../deploy/websocket.zip ws*.py 

validate_token:
	cd build && \
		pip install --upgrade --platform manylinux2014_x86_64 --no-deps pyjwt cryptography cffi pycparser -t ./ && \
		cp ../src/validate_token.py .  && \
	    zip -r ../deploy/validate_token.zip .

clean:
	rm -rf build/*
	rm -rf deploy/*.zip deploy/*.base64sha256
