# Flow actions

## log

```yaml
- type: log
  msg: your log message
```

| Name             | Type  | Description  | Default |
|------------------|-------|--------------|---------|
| msg              | `str` | A `string` or `templated string` | *required* |
| level            | `str` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | `INFO` |

## context_set

```yaml
- type: context_set
  context: {}
  object_context: {}
  global_context: {}
```

| Name             | Type   | Description  | Default |
|------------------|--------|--------------|---------|
| context          | `dict` | Per flow execution context. Value can be a `dict of strings` or `dict of templated strings` | `{}` |
| object_context | `dict` | Per (dbus) object context, shared between multiple flow executions. Value can be a `dict of strings` or `dict of templated strings` | `{}`|
| global_context   | `dict` | Global context, shared between multiple flow executions, over all subscriptions. Value can be a `dict of strings` or `dict of templated strings` | `{}` |

## mqtt_publish

```yaml
- type: mqtt_publish
  topic: dbus2mqtt/org.mpris.MediaPlayer2/state
  payload_type: json
  payload_template: {PlaybackStatus: "Off"}
```

| Name             | Type             | Description  | Default |
|------------------|------------------|--------------|---------|
| topic            | `str`            | MQTT topic the messaage is published to | *required* |
| payload_type     | `str`            | Message format for MQTT: `json`, `yaml`, `text` or `binary`. When set to `binary`, payload_template is expected to return a url formatted string where scheme is either `file`,`http` or `https` | `json` |
| payload_template | `str` \| `dict`  | value can be a `string`, a `dict of strings`, a `templated string` or a nested `dict of templated strings` | *required* |
