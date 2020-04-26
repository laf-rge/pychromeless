.PHONY: help check clean fetch-dependencies docker-build build-lambda-package

help:
	@python -c 'import fileinput,re; \
	ms=filter(None, (re.search("([a-zA-Z_-]+):.*?## (.*)$$",l) for l in fileinput.input())); \
	print("\n".join(sorted("\033[36m  {:25}\033[0m {}".format(*m.groups()) for m in ms)))' $(MAKEFILE_LIST)

check:		## print versions of required tools
	@docker --version
	@docker-compose --version
	@python3 --version

clean:		## delete pycache, build files
	@rm -rf build
	@rm -rf __pycache__
	@rm -rf deploy

fetch-dependencies:		## download chromedriver, headless-chrome to `./bin/`
	@mkdir -p bin/

	# Get chromedriver
	curl -SL https://chromedriver.storage.googleapis.com/2.32/chromedriver_linux64.zip > chromedriver.zip
	unzip chromedriver.zip -d bin/

	# Get Headless-chrome
	curl -SL https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-29/stable-headless-chromium-amazonlinux-2017-03.zip > headless-chromium.zip
	unzip headless-chromium.zip -d bin/

	# Clean
	@rm headless-chromium.zip chromedriver.zip

docker-build:		## create Docker image
	docker-compose build

docker-run:			## run `src.lambda_function.lambda_handler` with docker-compose
	docker-compose run lambda src.lambda_function.daily_sales_handler

build-lambda-package: clean fetch-dependencies			## prepares zip archive for AWS Lambda deploy (-> build/build.zip)
	mkdir -p deploy
	mkdir build
	cp -r bin build/.
	cp -r lib build/.
	pip install -r requirements.txt -t build/lib/.
	cd build; zip -9qr layer.zip . 
	mv build/layer.zip deploy/ 
	rm -rf build
	mkdir build
	cp -r src build/.
	cd build; zip -9qr build.zip . 
	mv build/build.zip deploy/ 
	rm -rf build
	openssl dgst -sha256 -binary deploy/layer.zip | openssl enc -base64 > deploy/layer.zip.base64sha256
	openssl dgst -sha256 -binary deploy/build.zip | openssl enc -base64 > deploy/build.zip.base64sha256

upload: build-lambda-package
	cd deploy \
	&& aws s3 cp . s3://wagonermanagementcorp/artifacts --exclude "*" --include "*.zip" --recursive \
	&& aws s3 cp . s3://wagonermanagementcorp/artifacts --exclude "*" --content-type "text/*" --include "*.base64sha256" --recursive
