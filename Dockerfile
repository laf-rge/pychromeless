FROM lambci/lambda:python3.7
MAINTAINER william@wagonermanagement.com

USER root

ENV APP_DIR /var/task

WORKDIR $APP_DIR

COPY requirements.txt .
RUN mkdir -p /opt
COPY bin /opt/bin
COPY lib /opt/lib

RUN mkdir -p /opt/lib
RUN pip3 install -r requirements.txt -t /opt/lib
