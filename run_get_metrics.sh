#!/usr/bin/env sh
set -o nounset                              # Treat unset variables as an error

#INTERVAL=$(cat $1 | yq '.General.interval')
#echo "INTERVAL=$INTERVAL"
#INTERVAL=${INTERVAL:=600}

VIRT_PYTHON=${VIRT_PYTHON:=/home/vagrant/.virtualenvs/metrics/bin/python3}

cd /opt/pp-code-metrics
${VIRT_PYTHON} ./get_metrics.py --config $1
