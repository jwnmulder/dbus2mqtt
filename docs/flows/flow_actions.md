# Flow actions

## log

```yaml
- type: log
  msg: your log message
  level: INFO
```

| key              | type             | description  |
|------------------|------------------|--------------|
| msg              | str              | A `string` or `templated string` |
| level            | str              | One of `DEBUG`, `INFO` (default), `WARNING`, `ERROR`, `CRITICAL` |

## context_set

```yaml
- type: context_set
  context: {}
  global_context: {}
```

| key                 | type             | description  |
|---------------------|------------------|--------------|
| context             | dict | Per flow execution context. Value can be a `dict of strings` or `dict of templated strings` |
| global_context      | dict | Global context, shared between multiple flow executions, over all subscriptions. Value can be a `dict of strings` or `dict of templated strings` |

## mqtt_publish

```yaml
- type: mqtt_publish
  topic: dbus2mqtt/org.mpris.MediaPlayer2/state
  payload_type: json
  payload_template: {PlaybackStatus: "Off"}
```

| key              | type             | description  |
|------------------|------------------|--------------|
| topic            | string | mqtt topic the messaage is published to |
| payload_type     | string | Message format for MQTT: `json` (default), `yaml`, `text` or `binary`. When set to `binary`, payload_template is expected to return a url formatted string where scheme is either `file`,`http` or `https` |
| payload_template | string, dict | value can be a `string`, a `dict of strings`, a `templated string` or a nested `dict of templated strings` |
