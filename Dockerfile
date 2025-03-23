FROM amazon/aws-lambda-python:3.13
LABEL MAINTAINER=william@wagonermanagement.com
ARG TARGETARCH

# install chrome dependencies
RUN dnf install -y atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt glibc-all-langpacks git \
    xorg-x11-xauth dbus-glib dbus-glib-devel nss mesa-libgbm jq unzip

#RUN dnf install -y jq unzip glibc-all-langpacks nss \
#    dbus-glib dbus-glib-devel atk atk-devel at-spi2-atk libXcomposite libXdamage \
#    libXrandr mesa-libgbm alsa-lib

COPY ./chrome-installer.sh ./chrome-installer.sh
RUN ./chrome-installer.sh
RUN rm ./chrome-installer.sh

# Copy and install requirements first (for better caching)
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip3 install -r requirements.txt

# Copy source code (excluding .env files via .dockerignore)
COPY src ${LAMBDA_TASK_ROOT}

# Set production environment variables
ENV CHROME_HEADLESS=0
