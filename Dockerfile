FROM python:3.7.1-slim-stretch
LABEL maintainer="frederic.t.chan@gmail.com"
ENV REFRESHED_AT 20181218
ENV MODE PRODUCTION
ENV FLASK_ENV production
ENV PIPENV_VENV_IN_PROJECT 1
ENV DATADOG_SERVICE_NAME=everyclass-auth DD_TRACE_ANALYTICS_ENABLED=true DD_LOGS_INJECTION=true

WORKDIR /var/app

# Why we need these packages?
# - procps contains useful proccess control commands like: free, kill, pkill, ps, top
# - wget is quite basic tool
# - git for using git in our app
# - gcc, libpcre3-dev for compiling uWSGI
# - libffi-dev for installing Python package cffi
# - libssl-dev for installing Python package cryptography
# - chromedriver for selenium

# See Google Chrome releases on https://www.ubuntuupdates.org/ppa/google_chrome?dist=stable

RUN apt-get update \
    && apt-get install -y --no-install-recommends procps wget gcc libpcre3-dev git libffi-dev libssl-dev chromedriver\
    && wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_72.0.3626.109-1_amd64.deb -O google-chrome-stable_amd64.deb \
    && apt install -y ./google-chrome-stable_amd64.deb \
    && rm ./google-chrome-stable_amd64.deb \
    && pip install uwsgi

COPY . /var/app

# install Python dependencies
RUN pip3 install --upgrade pip \
    && pip3 install pipenv \
    && pipenv sync \
    && pip3 install uwsgitop \
    && rm -r /root/.cache

RUN echo "Asia/Shanghai" > /etc/timezone

ENV UWSGI_HTTP_SOCKET ":80"

CMD ["/var/app/.venv/bin/ddtrace-run", "uwsgi", "--ini", "/var/app/deploy/uwsgi.ini"]