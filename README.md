pp-code-metrics
---------------
*Sending metrics from a [`pp-code`][0] sensor to InfluxDB to be visualized by Grafana*

Default Environment Settings
----------------------------
* See repo [`compose-monitor`][1] if you use it for InfluxDB and Grafana.
* `CONFIG_FILE`: this must be set to your config settings, see [`sample_settings.yml`](./sample_settings.yml) for example.


URI Pattern to retrieve metrics from a websever
-----------------------------------------------
```
# From get_metrics.py
uri = protocol + host + ':' + str(port) + '/' + key + endpoint
```


Sample returned json from a pp-code sensor
----------------------------------------
```
{
  "API": {
    "Version": "200"
  },
  "Stats": {
    "Temp": "74.34F",
    "Humi": "55.29%",
    "Press (inHg)": "29.63"
  }
}
```

Build docker image
------------------
```
make docker
# or,
docker-compose build
```

Tests
-----
The unit tests for `get_metrics.py` are in the [`tests/`](./tests) directory and are run with [`pytest`][3].

Install the runtime dependencies plus pytest, then run the test suite from the repo root:
```
pip install -r requirements.txt
pip install pytest
python -m pytest tests/
```

The Python code is linted with [`ruff`][4] (PEP 8, line length 88) and validated with `py_compile`.

```
ruff check get_metrics.py tests/
python -m py_compile get_metrics.py
```

Workflow
--------
First, we need to have `InfluxDB` and `Grafana` run from this [`compose-monitor`][1] docker-compose.

**1.Running from commandline**
```
nohup ./run_get_metrics.sh my_settings.yml 2>&1 > /dev/null &
```
**2.Running as a docker service**


Switch to virtual env with `docker-compose` installed. All settings are in `my_settings.yml` file.
```
workon metrics
docker-compose up -d
```

__author__: *tuan t. pham*


**Note:** The work of generalizing the endpoint, key, and Transformation is sponsored by [Greenfly SAU LLC][2].

[2]: https://greenfly.io
[1]: https://github.com/neofob/compose-monitor
[0]: https://watchman.online/
[3]: https://docs.pytest.org/
[4]: https://docs.astral.sh/ruff/
