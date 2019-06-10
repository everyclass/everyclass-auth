FROM python:3.7.1-slim-stretch
LABEL maintainer="frederic.t.chan@gmail.com"
ENV REFRESHED_AT 20181218
ENV MODE PRODUCTION
ENV FLASK_ENV production
ENV PIPENV_VENV_IN_PROJECT 1

WORKDIR /var/app

# Why we need these packages?
# - procps contains useful proccess control commands like: free, kill, pkill, ps, top
# - wget is quite basic tool
# - git for using git in our app
# - gcc, libpcre3-dev for compiling uWSGI
# - libffi-dev for installing Python package cffi
# - libssl-dev for installing Python package cryptography
# - chromedriver for selenium
RUN apt-get update \
    && apt-get install -y --no-install-recommends procps wget gcc libpcre3-dev git libffi-dev libssl-dev chromedriver gnupg\
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable=72.0.3626.109-1 \
    && rm -rf /var/lib/apt/lists/* \
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

CMD ["uwsgi", "--ini", "/var/app/deploy/uwsgi.ini"]