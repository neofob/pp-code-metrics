FROM ubuntu:23.04 as builder
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

FROM ubuntu:23.04 as deploy

ENV PKGS="python3-minimal python3-pip virtualenv" \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get -yq update && apt-get dist-upgrade -yq \
    && apt-get -yq install --no-install-recommends  ${PKGS} \
    && mkdir -p /opt/pp-code-metrics/metrics \
    && apt-get autoremove -yq \
    && apt-get autoclean \
    && rm -fr /tmp/* /var/lib/apt/lists/*

COPY ./run_get_metrics.sh /opt/pp-code-metrics
COPY ./get_metrics.py /opt/pp-code-metrics
COPY ./sample_settings.yml /opt/pp-code-metrics
COPY --from=builder /opt/pp-code-metrics/metrics /opt/pp-code-metrics/metrics

WORKDIR /opt/pp-code-metrics
ENV VIRT_PYTHON=/opt/pp-code-metrics/metrics/bin/python3

CMD  ["/opt/pp-code-metrics/run_get_metrics.sh", "my_settings.yml"]
