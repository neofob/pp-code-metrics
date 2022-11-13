FROM ubuntu:22.04 as builder
LABEL maintainer "tuan t. pham" <tuan@vt.edu>

ENV PKGS="python3 python3-pip python3-dev gcc virtualenv" \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get -yq update && apt-get dist-upgrade -yq \
    && apt-get -yq install --no-install-recommends  ${PKGS} \
    && mkdir -p /opt/pp-code-metrics

COPY ./requirements.txt /opt/pp-code-metrics

RUN cd /opt/pp-code-metrics \
    && virtualenv metrics \
    && . /opt/pp-code-metrics/metrics/bin/activate \
    && pip install -r requirements.txt \
    && apt-get autoremove -yq \
    && apt-get autoclean \
    && rm -fr /tmp/* /var/lib/apt/lists/*

FROM ubuntu:22.04 as deploy

ENV DOCKERIZE_VERSION=v0.6.1
ENV PKGS="wget python3-minimal python3-pip virtualenv" \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get -yq update && apt-get dist-upgrade -yq \
    && apt-get -yq install --no-install-recommends  ${PKGS} \
    && wget https://github.com/jwilder/dockerize/releases/download/${DOCKERIZE_VERSION}/dockerize-linux-amd64-${DOCKERIZE_VERSION}.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-${DOCKERIZE_VERSION}.tar.gz \
    && rm dockerize-linux-amd64-${DOCKERIZE_VERSION}.tar.gz \
    && mkdir -p /opt/pp-code-metrics/metrics \
    && apt-get autoremove -yq \
    && apt-get autoclean \
    && rm -fr /tmp/* /var/lib/apt/lists/*

COPY ./run_get_metrics.sh /opt/pp-code-metrics
COPY ./get_metrics.py /opt/pp-code-metrics
COPY ./sample_settings.yml /opt/pp-code-metrics
COPY --from=builder /opt/pp-code-metrics/metrics /opt/pp-code-metrics/metrics

WORKDIR /opt/pp-code-metrics

RUN . /opt/pp-code-metrics/metrics/bin/activate 

ENV CONFIG_FILE=/etc/pp-code-metrics.yml

CMD  ["dockerize", \
  "-template", "/etc/pp-code-metrics.tmpl:/etc/pp-code-metrics.yml", \
  "/opt/pp-code-metrics/run_get_metrics.sh"]
