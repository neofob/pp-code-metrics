#!/usr/bin/env python

import os
import yaml
import pprint
import time

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

client = None
write_api = None

def getInfluxDBClient():
    global client, write_api

    for n in range(3):
        try:
            client = InfluxDBClient(url=influxdb_url, token=influxdb_api_token, org=influxdb_org)
        except:
            time.sleep(5)
            continue
        write_api = client.write_api(write_options=SYNCHRONOUS)
        break
    if None == write_api:
        os._exit(1)

def getNodeMetrics(node):
    for n_try in range(3):
        try_again = False
        host = node['Host']
        port = node['Port']
        key = node['Key']
        metric_field = node['Metric']
        uri = 'http://' + host + ':' + str(port) + '/' + key + '&Stats/json'
        r = requests.get(uri)
        if 200 != r.status_code:
            time.sleep(5)
            continue
        metrics = {}
        tags = node['Tags']
        fields = node['Fields']
        measurement = node['Measurement']
        point_fields = {}
        for metric, c_field in fields.items():
            try:
                if c_field['chomp']:
                    metrics[metric] = float(r.json()[metric_field][metric][:-1])
                else:
                    metrics[metric] = float(r.json()[metric_field][metric])
            except ValueError:
                try_again = True
                continue
            # This is a nasty node bug; 0 is a valid metric
            # However, it returns 0 sometimes
            if 0 == metrics[metric]:
                try_again = True
                continue
            point_fields[metric] = c_field['field']
            #pp.pprint(point_fields[metric])
            p = Point(measurement).field(point_fields[metric], metrics[metric])
            # Tags for each node
            for k,v in tags.items():
                p.tag(k,v)
            # Extra tags for each field
            if 'Tags' in c_field:
                for k,v in c_field['Tags'].items():
                    p.tag(k,v)
            write_api.write(bucket=influxdb_bucket, record=p)

        if try_again:
            time.sleep(5)
            continue
        else:
            pp.pprint(metrics)
            break


if __name__ == '__main__':
    getInfluxDBClient()

    for node_k, node in my_config['Nodes'].items():
        #if "Garden" != node_k:
        #    continue
        getNodeMetrics(node)
    client.close()
