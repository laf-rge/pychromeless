FROM  --platform=linux/amd64 amazon/aws-lambda-python:3.12
LABEL MAINTAINER=william@wagonermanagement.com
ARG TARGETARCH
# install chrome dependencies
RUN dnf install -y atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb glibc-all-langpacks \
    xorg-x11-xauth dbus-glib dbus-glib-devel nss mesa-libgbm jq unzip

COPY ./chrome-installer.sh ./chrome-installer.sh
RUN ./chrome-installer.sh
RUN rm ./chrome-installer.sh

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip3 install -r requirements.txt
COPY src ${LAMBDA_TASK_ROOT}
