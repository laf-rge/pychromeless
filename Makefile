all:
	aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 262877227567.dkr.ecr.us-east-2.amazonaws.com
	docker build -t wmc . --platform=linux/amd64 --no-cache
	docker tag wmc:latest 262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest
	docker push 262877227567.dkr.ecr.us-east-2.amazonaws.com/wmc:latest
	cd terraform; \
		terraform apply