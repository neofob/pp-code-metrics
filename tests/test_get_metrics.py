"""Unit tests for the get_metrics collector."""

import contextlib
import unittest
from unittest import mock

import requests

import get_metrics


def make_response(json_data=None, status_code=200):
    """Create a mock sensor HTTP response."""
    response = mock.Mock()
    response.status_code = status_code
    response.json.return_value = json_data
    return response


def base_node():
    """Create a sample node configuration."""
    return {
        'Host': '192.168.1.2',
        'Port': 8000,
        'Key': 'deadbeef',
        'Endpoint': '&Stats/json',
        'Metric': 'Stats',
        'Measurement': 'Air',
        'Tags': {'location': 'Basement'},
        'Fields': {
            'Temp': {'field': 'temperature', 'chomp': True},
        },
    }


class TestGetMetric(unittest.TestCase):
    def test_parses_chomped_value(self):
        r = make_response({'Stats': {'Temp': '82.09F'}})
        self.assertEqual(82.09, get_metrics.getMetric(r, None, 'Temp', 'Stats', True))

    def test_parses_value_without_chomp(self):
        r = make_response({'Stats': {'Press (inHg)': '29.74'}})
        self.assertEqual(
            29.74, get_metrics.getMetric(r, None, 'Press (inHg)', 'Stats', False))

    def test_parses_indexed_metric(self):
        r = make_response([{'internal temperature': 21.5}])
        self.assertEqual(
            21.5, get_metrics.getMetric(r, 0, 'internal temperature', '', False))

    def test_invalid_value_raises_value_error(self):
        r = make_response({'Stats': {'Temp': 'abcF'}})
        with self.assertRaises(ValueError):
            get_metrics.getMetric(r, None, 'Temp', 'Stats', True)

    def test_missing_metric_raises_key_error(self):
        r = make_response({'Stats': {}})
        with self.assertRaises(KeyError):
            get_metrics.getMetric(r, None, 'Temp', 'Stats', True)


class TestGetURI(unittest.TestCase):
    def test_builds_uri_with_key_and_endpoint(self):
        uri = get_metrics.getURI(
            host='192.168.1.2', port=8000, key='abc', endpoint='&Stats/json')
        self.assertEqual('http://192.168.1.2:8000/abc&Stats/json', uri)

    def test_builds_uri_with_defaults(self):
        uri = get_metrics.getURI()
        self.assertEqual('http://localhost:8080/&Stats/json', uri)


class TestDoTransform(unittest.TestCase):
    def test_without_transform_returns_metric(self):
        self.assertEqual(21.5, get_metrics.doTransform(21.5, None))

    def test_applies_linear_transform(self):
        # ax + b with a=1.8, b=32: 21.5 Celsius -> 70.7 Fahrenheit
        self.assertEqual(70.7, get_metrics.doTransform(21.5, {'a': 1.8, 'b': 32}))


class TestGetInfluxDBClient(unittest.TestCase):
    def test_returns_client_and_write_api(self):
        client = mock.Mock()
        with mock.patch.object(
                get_metrics, 'InfluxDBClient', return_value=client) as ctor:
            client_out, write_api_out = get_metrics.getInfluxDBClient(
                'http://localhost:8086', 'token', 'org')
        self.assertIs(client_out, client)
        self.assertIs(write_api_out, client.write_api.return_value)
        ctor.assert_called_once_with(
            url='http://localhost:8086', token='token', org='org')
        client.write_api.assert_called_once_with(write_options=get_metrics.SYNCHRONOUS)

    def test_retries_and_raises_when_client_fails(self):
        with contextlib.ExitStack() as stack:
            ctor = stack.enter_context(mock.patch.object(
                get_metrics, 'InfluxDBClient', side_effect=ConnectionError('boom')))
            sleep = stack.enter_context(mock.patch.object(get_metrics.time, 'sleep'))
            stack.enter_context(self.assertRaises(RuntimeError))
            get_metrics.getInfluxDBClient('http://localhost:8086', 'token', 'org')
        self.assertEqual(get_metrics.INFLUXDB_MAX_RETRIES, ctor.call_count)
        self.assertEqual(get_metrics.INFLUXDB_MAX_RETRIES - 1, sleep.call_count)


class TestGetNodeMetrics(unittest.TestCase):
    def test_writes_valid_metric_to_influxdb(self):
        write_api = mock.Mock()
        response = make_response({'Stats': {'Temp': '82.09F'}})
        with mock.patch.object(
                get_metrics.requests, 'get', return_value=response) as get:
            get_metrics.getNodeMetrics(base_node(), write_api, 'sensor')
        get.assert_called_once_with('http://192.168.1.2:8000/deadbeef&Stats/json')
        write_api.write.assert_called_once()
        kwargs = write_api.write.call_args.kwargs
        self.assertEqual('sensor', kwargs['bucket'])
        point = kwargs['record']
        self.assertEqual('Air,location=Basement temperature=82.09', str(point))

    def test_writes_transformed_metric(self):
        node = base_node()
        node['Transform'] = {'a': 1.8, 'b': 32}
        node['Fields']['Temp']['chomp'] = False
        write_api = mock.Mock()
        response = make_response({'Stats': {'Temp': 21.5}})
        with mock.patch.object(
                get_metrics.requests, 'get', return_value=response) as get:
            get_metrics.getNodeMetrics(node, write_api, 'sensor')
        get.assert_called_once()
        write_api.write.assert_called_once()
        point = write_api.write.call_args.kwargs['record']
        self.assertEqual('Air,location=Basement temperature=70.7', str(point))

    def test_retries_on_transient_http_error(self):
        write_api = mock.Mock()
        error_response = make_response(None, status_code=500)
        ok_response = make_response({'Stats': {'Temp': '82.09F'}})
        get_patcher = mock.patch.object(
            get_metrics.requests, 'get', side_effect=[error_response, ok_response])
        with get_patcher as get, mock.patch.object(get_metrics.time, 'sleep'):
            get_metrics.getNodeMetrics(base_node(), write_api, 'sensor')
        self.assertEqual(2, get.call_count)
        write_api.write.assert_called_once()

    def test_retries_on_network_error(self):
        write_api = mock.Mock()
        ok_response = make_response({'Stats': {'Temp': '82.09F'}})
        get_patcher = mock.patch.object(
            get_metrics.requests, 'get',
            side_effect=[requests.exceptions.ConnectionError(), ok_response])
        with get_patcher as get, mock.patch.object(get_metrics.time, 'sleep'):
            get_metrics.getNodeMetrics(base_node(), write_api, 'sensor')
        self.assertEqual(2, get.call_count)
        write_api.write.assert_called_once()

    def test_retries_when_metric_value_is_invalid(self):
        write_api = mock.Mock()
        bad_response = make_response({'Stats': {'Temp': 'abcF'}})
        ok_response = make_response({'Stats': {'Temp': '82.09F'}})
        get_patcher = mock.patch.object(
            get_metrics.requests, 'get', side_effect=[bad_response, ok_response])
        with get_patcher as get, mock.patch.object(get_metrics.time, 'sleep'):
            get_metrics.getNodeMetrics(base_node(), write_api, 'sensor')
        self.assertEqual(2, get.call_count)
        write_api.write.assert_called_once()

    def test_retries_when_metric_value_is_zero(self):
        write_api = mock.Mock()
        zero_response = make_response({'Stats': {'Temp': '0.00F'}})
        ok_response = make_response({'Stats': {'Temp': '82.09F'}})
        get_patcher = mock.patch.object(
            get_metrics.requests, 'get', side_effect=[zero_response, ok_response])
        with get_patcher as get, mock.patch.object(get_metrics.time, 'sleep'):
            get_metrics.getNodeMetrics(base_node(), write_api, 'sensor')
        self.assertEqual(2, get.call_count)
        write_api.write.assert_called_once()


if __name__ == '__main__':
    unittest.main()
