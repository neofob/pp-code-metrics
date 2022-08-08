#!/usr/bin/env python

import os
import yaml
import pprint

import requests

"""
Example:
CONFIG_FILE=my_settings.yml ./get_metrics.py
"""
pp = pprint.PrettyPrinter(indent=2)

# load config file
config_file = os.getenv('CONFIG_FILE')
my_config = {}

with open(config_file, "r") as file:
    my_config = yaml.safe_load(file)


"""
TODO: iterate through "Nodes"
for node in my_config['Nodes'].keys()
Check for field names and what not
This only works for 3-sensor temperature node
"""

for node in my_config['Nodes'].keys():
    if "Soil" != node:
        continue

    node_host = my_config['Nodes'][node]['Host']
    node_port = my_config['Nodes'][node]['Port']
    node_key = my_config['Nodes'][node]['Key']
    node_metric_field = my_config['Nodes'][node]['Metric']
    uri = 'http://' + node_host + ':' + str(node_port) + '/' + node_key + '&Stats/json'
    r = requests.get(uri)
    node_metrics = {}
    for metric in r.json()[node_metric_field].keys():
        node_metrics[metric] = r.json()[node_metric_field][metric][:-1]
    pp.pprint(node_metrics)
