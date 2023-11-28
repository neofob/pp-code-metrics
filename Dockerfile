FROM python:3.9.18-alpine3.18 as builder
LABEL maintainer "tuan t. pham" <tuan@vt.edu>

ENV PKGS="py3-virtualenv"

RUN apk update && apk add ${PKGS} \
    && mkdir -p /opt/pp-code-metrics
COPY ./requirements.txt /opt/pp-code-metrics
RUN cd /opt/pp-code-metrics \
    && virtualenv metrics \
    && source /opt/pp-code-metrics/metrics/bin/activate \
    && pip install -U pip \
    && pip install -r requirements.txt \
    && rm -fr /tmp/*

FROM mikefarah/yq:latest as yq_base

FROM python:3.9.18-alpine3.18 as deploy

ENV PKGS="py3-virtualenv tini"
ENV DOCKERIZE_URL="https://github.com/jwilder/dockerize/releases/download/v0.7.0/dockerize-alpine-linux-amd64-v0.7.0.tar.gz"

RUN apk update && apk add --no-cache ${PKGS} \
    && mkdir -p /opt/pp-code-metrics
COPY ./requirements.txt /opt/pp-code-metrics

COPY ./run_get_metrics.sh /opt/pp-code-metrics
COPY ./get_metrics.py /opt/pp-code-metrics
COPY ./sample_settings.yml /opt/pp-code-metrics
COPY --from=builder /opt/pp-code-metrics/metrics /opt/pp-code-metrics/metrics
COPY --from=yq_base /usr/bin/yq /usr/bin/yq

WORKDIR /opt/pp-code-metrics
ENV VIRT_PYTHON=/opt/pp-code-metrics/metrics/bin/python3

RUN wget -O - ${DOCKERIZE_URL} | tar xzf - -C /usr/local/bin

RUN mkdir -p /etc/cron.d
COPY crontab/pp-code-metrics.tmpl /tmp/
# This can be overridden at runtime
ENV INTERVAL=10
ENTRYPOINT /sbin/tini -- dockerize --template /tmp/pp-code-metrics.tmpl:/etc/crontabs/root /usr/sbin/crond -f -d 0
