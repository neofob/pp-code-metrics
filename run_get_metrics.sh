#!/usr/bin/env bash
set -o nounset                              # Treat unset variables as an error

INTERVAL=${INTERVAL:=600}

VIRT_PYTHON=${VIRT_PYTHON:=/home/vagrant/.virtualenvs/metrics/bin/python3}

while true; do
  ${VIRT_PYTHON} ./get_metrics.py --config $1
  sleep ${INTERVAL}
done
