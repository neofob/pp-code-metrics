#!/usr/bin/env python

import os
import yaml
import pprint
import time
import argparse

import requests

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


"""
Example:
./get_metrics.py --config my_settings.yml
"""
pp = pprint.PrettyPrinter(indent=2)

# load config file
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', dest='config', action='store', help='Config file', required=True)

config_file = parser.parse_args().config

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
    host = node['Host']
    port = node['Port']
    key = node['Key']
    metric_field = node['Metric']
    tags = node['Tags']
    fields = node['Fields']
    measurement = node['Measurement']
    uri = 'http://' + host + ':' + str(port) + '/' + key + '&Stats/json'
    for n_try in range(3):
        try_again = False
        r = requests.get(uri)
        # This is a bug of the DS18B20, I was told.
        if 200 != r.status_code:
            time.sleep(60)
            continue
        metrics = {}
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
            # However, it returns 0 sometimes, DS18B20 bug
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
            time.sleep(60)
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
