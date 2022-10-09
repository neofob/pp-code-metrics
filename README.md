pp-code-metrics
---------------
*Sending metrics from a [`pp-code`][0] sensor to InfluxDB to be visualized by Grafana*

Default Environment Settings
----------------------------
* See repo [`compose-monitor`][1] if you use it for InfluxDB and Grafana.
* `CONFIG_FILE`: this must be set to your config settings, see [`sample_settings.yml`](./sample_settings.yml) for example.

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

Workflow
--------
First, we need to have InfluxDB` and `Grafana` run from this [`compose-monitor`][1] docker-compose.
Then we run the shell script (or some sort of cron job) to send metric data to InfluxDB.
```
# or, source my_env/bin/activate
workon metrics
nohup ./run_get_metrics.sh 2>&1 > /dev/null &
```

__author__: *tuan t. pham*

[1]: https://github.com/neofob/compose-monitor
[0]: https://watchman.online/
