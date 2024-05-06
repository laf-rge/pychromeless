FROM umihico/aws-lambda-selenium-python:latest
ARG TARGETARCH
MAINTAINER william@wagonermanagement.com

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN dnf --assumeyes install glibc-all-langpacks
RUN pip3 install -r requirements.txt
COPY src ${LAMBDA_TASK_ROOT}
