#!/usr/bin/env python

import os
import yaml
import pprint

import requests

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


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


# InfluxDB
influxdb_bucket = my_config['InfluxDB']['Bucket']
influxdb_api_token = my_config['InfluxDB']['API_TOKEN']
influxdb_host = my_config['InfluxDB']['Host']
influxdb_port = my_config['InfluxDB']['Port']
influxdb_url = 'http://' + influxdb_host + ':' + str(influxdb_port)
influxdb_org = my_config['InfluxDB']['Org']
client = InfluxDBClient(url=influxdb_url, token=influxdb_api_token, org=influxdb_org)
write_api = client.write_api(write_options=SYNCHRONOUS)

"""
TODO: iterate through "Nodes"
for node in my_config['Nodes'].keys()
Check for field names and what not
This only works for 3-sensor temperature node
"""

for node in my_config['Nodes'].keys():
    if "Garden" != node:
        continue

    my_node = my_config['Nodes'][node]
    node_host = my_node['Host']
    node_port = my_node['Port']
    node_key = my_node['Key']
    node_metric_field = my_node['Metric']
    node_uri = 'http://' + node_host + ':' + str(node_port) + '/' + node_key + '&Stats/json'
    node_r = requests.get(node_uri)
    node_metrics = {}
    node_tags = my_node['Tags']
    node_fields = my_node['Fields']
    node_measurement = my_node['Measurement']
    point_fields = {}
    for metric, c_field in node_fields.items():
        node_metrics[metric] = float(node_r.json()[node_metric_field][metric][:-1])
        point_fields[metric] = c_field['field']
        #pp.pprint(point_fields[metric])
        p = Point(node_measurement).field(point_fields[metric], node_metrics[metric])
        for k,v in node_tags.items():
            p.tag(k,v)
        if 'Tags' in c_field:
            for k,v in c_field['Tags'].items():
                p.tag(k,v)
        write_api.write(bucket=influxdb_bucket, record=p)
    pp.pprint(node_metrics)
