pp-code-metrics
---------------
*Send metrics from a [`pp-code`][0] sensor to InfluxDB to be visualized by Grafana*



Default Environment Settings
----------------------------
```
# Output side
INFLUXDB_HOST=localhost
INFLUXDB_PORT=8086
INFLUXDB_USER=influxdb
INFLUXDB_PASSWORD=metrics
```



Testing
-------
We use [`json-server`][1] to mock some data for testing.



Sample return json from a pp-code sensor
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
* `json-server` is used to mock the sensor server, serving the data in json format.
* `influxdb` runs from this [`compose-monitor`][2] 


__author__: *tuan t. pham*

[2]: https://github.com/neofob/compose-monitor
[1]: https://www.npmjs.com/package/json-server
[0]: https://watchman.online/
