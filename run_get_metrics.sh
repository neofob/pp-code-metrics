#!/usr/bin/env bash
set -o nounset                              # Treat unset variables as an error

while true; do
    CONFIG_FILE=my_settings.yml ./get_metrics.py
    sleep 60
done
