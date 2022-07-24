pp-code-metrics
---------------
*Send metrics from a [`pp-code`][0] sensor to InfluxDB to be visualized by Grafana*



Default Environment Settings
----------------------------
```
# Input side
SENSOR_SERVER=localhost
SENSOR_PORT=80
SENSOR_KEY=your_device_key
SENSOR_API="&Stats/json"

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
* We can 


__author__: *tuan t. pham*

[1]: https://www.npmjs.com/package/json-server
[0]: https://watchman.online/
