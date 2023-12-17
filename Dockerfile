# Builder stage
FROM python:3.11.7-alpine3.19 AS builder
LABEL maintainer "tuan t. pham" <tuan@vt.edu>

ENV PKGS="py3-virtualenv"
RUN apk update && apk add ${PKGS} && mkdir -p /opt/pp-code-metrics
COPY ./requirements.txt /opt/pp-code-metrics
RUN cd /opt/pp-code-metrics \
    && virtualenv metrics \
    && source /opt/pp-code-metrics/metrics/bin/activate \
    && pip install -U pip \
    && pip install -r requirements.txt \
    && rm -fr /tmp/*

# Intermediate stage for yq
FROM mikefarah/yq:latest AS yq_base

# Deployment stage
FROM python:3.11.7-alpine3.19 AS deploy

ENV PKGS="py3-virtualenv tini" \
    DOCKERIZE_URL="https://github.com/jwilder/dockerize/releases/download/v0.7.0/dockerize-alpine-linux-amd64-v0.7.0.tar.gz"

RUN apk update && apk add --no-cache ${PKGS} \
    && rm -rf /var/cache/apk/* \
    && mkdir -p /opt/pp-code-metrics

COPY --from=yq_base /usr/bin/yq /usr/bin/yq

WORKDIR /opt/pp-code-metrics
ENV VIRT_PYTHON=/opt/pp-code-metrics/metrics/bin/python3

RUN wget -O - ${DOCKERIZE_URL} | tar xzf - -C /usr/local/bin

COPY run_get_metrics.sh get_metrics.py sample_settings.yml /opt/pp-code-metrics/
COPY --from=builder /opt/pp-code-metrics/metrics /opt/pp-code-metrics/metrics
RUN chmod +x run_get_metrics.sh

RUN mkdir -p /etc/cron.d
COPY crontab/pp-code-metrics.tmpl /tmp/
# This can be overridden at runtime
ENV INTERVAL=10
ENTRYPOINT ["/sbin/tini", "--", "dockerize", "--template", "/tmp/pp-code-metrics.tmpl:/etc/crontabs/root", "/usr/sbin/crond", "-f", "-d", "0"]
