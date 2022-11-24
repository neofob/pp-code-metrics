#!/usr/bin/env bash
set -o nounset                              # Treat unset variables as an error

INTERVAL=${INTERVAL:=600}

while true; do
    ./get_metrics.py --config $1
    sleep $INTERVAL
done
