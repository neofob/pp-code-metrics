#!/usr/bin/env python3

import argparse
import pprint
import time

import requests
import yaml
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

"""
Example:
./get_metrics.py --config my_settings.yml
"""
pp = pprint.PrettyPrinter(indent=2)

# Retry policies (seconds between attempts)
INFLUXDB_MAX_RETRIES = 3
INFLUXDB_RETRY_DELAY = 5
REQUEST_MAX_RETRIES = 3
REQUEST_RETRY_DELAY = 15
NODE_RETRY_DELAY = 60
WRITE_RETRY_DELAY = 5


def get_config(config_file):
    """
    Load the sensor and InfluxDB configuration from a YAML file.

    Args:
        config_file: Path to the YAML configuration file.

    Returns:
        The parsed configuration dictionary.

    Raises:
        OSError: When the configuration file cannot be read.
        yaml.YAMLError: When the configuration file is not valid YAML.
    """
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)


def getInfluxDBClient(influxdb_url, influxdb_api_token, influxdb_org):
    """
    Create an InfluxDB client and its write API, retrying transient failures.

    Args:
        influxdb_url: Base URL of the InfluxDB instance (e.g. http://host:8086).
        influxdb_api_token: InfluxDB API token.
        influxdb_org: InfluxDB organization name.

    Returns:
        Tuple of (client, write_api).

    Raises:
        RuntimeError: When the InfluxDB client could not be created after all retries.
    """
    for n_try in range(INFLUXDB_MAX_RETRIES):
        try:
            client = InfluxDBClient(
                url=influxdb_url, token=influxdb_api_token, org=influxdb_org)
            write_api = client.write_api(write_options=SYNCHRONOUS)
            return client, write_api
        except (ConnectionError, TimeoutError):
            if INFLUXDB_MAX_RETRIES - 1 == n_try:
                break
            time.sleep(INFLUXDB_RETRY_DELAY)
    raise RuntimeError(
        f'Could not create InfluxDB client after {INFLUXDB_MAX_RETRIES} attempts')


def getMetric(r, index=None, metric='', metric_field='', chomp=True):
    """
    Extract and convert a single metric value from a sensor response.

    Args:
        r: Sensor HTTP response.
        index: Optional index of the metric entry within the response.
        metric: Metric name (key) to extract.
        metric_field: Optional parent key holding the metric (e.g. 'Stats').
        chomp: When set, strip the trailing unit character(s) before conversion.

    Returns:
        The metric value as float.

    Raises:
        KeyError: When the metric key is missing from the response.
        TypeError: When the metric value is of an unexpected type.
        ValueError: When the metric value cannot be converted to float.
    """
    if None == index:
        r_data = r.json()
    else:
        r_data = r.json()[index]

    if None == metric_field or '' == metric_field:
        # Empty field (not 'Stats' for instance)
        metric_data = r_data[metric]
    else:
        metric_data = r_data[metric_field][metric]

    if chomp:
        metric_data = metric_data[:-1]
    return float(metric_data)


def getURI(
    protocol='http://', host='localhost', port=8080, key='', endpoint='&Stats/json'
):
    """
    Form the URI to send request to
    """
    uri = protocol + host + ':' + str(port) + '/' + key + endpoint
    return uri


def doTransform(metric, transform=None):
    """
    Transform the original metric if transform coefficients are defined.

    Fixed formula is ax + b for now.
    """
    if None == transform:
        return metric
    return float(transform.get('a', 1) * metric + transform.get('b', 0))


def getNodeMetrics(node, write_api, bucket):
    """
    Fetch and write the metrics of a single node, retrying transient failures.

    Args:
        node: Node configuration dictionary.
        write_api: InfluxDB write API instance.
        bucket: InfluxDB bucket name.
    """
    host = node['Host']
    port = node['Port']
    key = node['Key']
    endpoint = node['Endpoint']
    metric_field = node['Metric']
    tags = node['Tags']
    transform = node.get('Transform')
    index = node.get('Index')
    fields = node['Fields']
    measurement = node['Measurement']
    uri = getURI(host=host, port=port, key=key, endpoint=endpoint)
    for n_try in range(REQUEST_MAX_RETRIES):
        try_again = False
        try:
            r = requests.get(uri)
        except requests.RequestException:
            # Transient network error, retry later
            time.sleep(REQUEST_RETRY_DELAY)
            continue
        if 200 != r.status_code:
            # Transient sensor error, retry later
            time.sleep(REQUEST_RETRY_DELAY)
            continue
        metrics = {}
        point_fields = {}
        for metric, c_field in fields.items():
            try:
                metrics[metric] = getMetric(
                    r, index, metric, metric_field, c_field['chomp'])
            except (KeyError, TypeError, ValueError):
                try_again = True
                continue
            # This is a nasty node bug; 0 is a valid metric
            # However, it returns 0 sometimes, DS18B20 bug
            if 0 == metrics[metric]:
                try_again = True
                continue
            metrics[metric] = doTransform(metrics[metric], transform)
            point_fields[metric] = c_field['field']
            p = Point(measurement).field(point_fields[metric], metrics[metric])
            # Tags for each node
            for k, v in tags.items():
                p.tag(k, v)
            # Extra tags for each field
            if 'Tags' in c_field:
                for k, v in c_field['Tags'].items():
                    p.tag(k, v)
            for i in range(3):
                try:
                    write_api.write(bucket=bucket, record=p)
                    break
                except requests.RequestException:
                    time.sleep(WRITE_RETRY_DELAY)
        if try_again:
            time.sleep(NODE_RETRY_DELAY)
            continue
        else:
            pp.pprint(metrics)
            break


def parse_args(argv=None):
    """
    Parse command-line arguments.

    Returns:
        The parsed argument namespace with the config file path.

    Raises:
        SystemExit: When required arguments are missing.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--config', dest='config', action='store',
        help='Config file', required=True,
    )
    return parser.parse_args(argv)


def main(config_file):
    """
    Run the metrics collection over all configured nodes.

    Args:
        config_file: Path to the YAML configuration file.
    """
    my_config = get_config(config_file)
    influxdb_cfg = my_config['InfluxDB']
    client, write_api = getInfluxDBClient(
        influxdb_url='http://' + influxdb_cfg['Host'] + ':' + str(influxdb_cfg['Port']),
        influxdb_api_token=influxdb_cfg['API_TOKEN'],
        influxdb_org=influxdb_cfg['Org'],
    )
    influxdb_bucket = influxdb_cfg['Bucket']
    for node in my_config['Nodes'].values():
        getNodeMetrics(node, write_api, influxdb_bucket)
    client.close()


if __name__ == '__main__':
    args = parse_args()
    main(args.config)