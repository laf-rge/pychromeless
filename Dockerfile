FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.10
ARG TARGETARCH
MAINTAINER william@wagonermanagement.com

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip3 install -r requirements.txt
RUN yum install libX11 GConf2 -y unzip && \
    curl -Lo "/tmp/chromedriver.zip" "https://chromedriver.storage.googleapis.com/2.32/chromedriver_linux64.zip" && \
    curl -Lo "/tmp/headless-chromium.zip" "https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-29/stable-headless-chromium-amazonlinux-2017-03.zip" && \
    unzip /tmp/chromedriver.zip -d /opt/bin/ && \
    unzip /tmp/headless-chromium.zip -d /opt/bin/ && \
    rm /tmp/headless-chromium.zip && \
    rm /tmp/chromedriver.zip && \
    chmod +x /opt/bin/chromedriver
COPY src ${LAMBDA_TASK_ROOT}
