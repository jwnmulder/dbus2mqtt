# Flow triggers

## schedule

Schedule based triggers can be configured by setting either a `cron` or `interval` parameter.
Scheduling is based on the APScheduler library and allows the following configuration options.

```yaml
- type: schedule
  interval: {seconds: 5}
```

Trigger configuration:

| Name      | Type  | Description  | Default |
|-----------|-------|--------------|---------|
| interval | `dict` | dict of time units and intervals, see <https://apscheduler.readthedocs.io/en/3.x/modules/triggers/interval.html>    | |
| cron     | `dict` | dict of time units and cron expressions, see <https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html> | |

When triggered, the following context parameters are available

| Name         | Type   | Description      |
|--------------|--------|------------------|
| trigger_type | `str`  | 'schedule'       |

## dbus_object_added

This trigger is fired during startup or when a new object appears on D-Bus that matches the `bus2mqtt` subscription.

```yaml
- type: dbus_object_added
```

When triggered, the following context parameters are available

| Name         | Type   | Description      |
|--------------|--------|------------------|
| trigger_type | `str`  | 'object_added'   |
| bus_name     | `str`  | bus_name of the object that was registered on dbus |
| path         | `str`  | path of the object that was registered on dbus |

## dbus_object_removed

```yaml
- type: dbus_object_removed
```

When triggered, the following context parameters are available

| Name         | Type   | Description      |
|--------------|--------|------------------|
| trigger_type | `str`  | 'object_removed' |
| bus_name     | `str`  | bus_name of the object that was registered on dbus |
| path         | `str`  | path of the object that was registered on dbus |

## dbus_signal

DBus signals triggers must be configured with an anterface and path. Note that only subscribed signals can be configured as a trigger.

```yaml
- type: dbus_signal
  interface: org.freedesktop.DBus.Properties
  signal: PropertiesChanged
```

Trigger configuration:

| Name      | Type  | Description  | Default |
|-----------|-------|--------------|---------|
| interface | `str` | interface to filter on, e.g. 'org.freedesktop.DBus.Properties' | *required* |
| signal    | `str` | signal name to filter on, e.g. PropertiesChanged | *required* |

When triggered, the following context parameters are available

| Name         | Type   | Description      |
|--------------|--------|------------------|
| trigger_type | `str`  | 'dbus_signal'    |
| bus_name     | `str`  | bus_name of the object that was registered on dbus |
| path         | `str`  | path of the object that was registered on dbus |
| interface    | `str`  | name of interface for which the signal was triggered |
| signal       | `str`  | name of the signal, e.g. 'Seeked' |
| args         | `list` | signal arguments, list of objects |

## mqtt_message

Listens for MQTT messages on the configured topic. The message payload is expected to be JSON formatted

```yaml
- type: mqtt_message
  topic: dbus2mqtt/org.mpris.MediaPlayer2/flow-trigger
  filter: "{{ payload.get('action') == 'Mute' }}"
```

Trigger configuration:

| Name         | Type  | Description  | Default |
|--------------|-------|--------------|---------|
| topic        | `str` | topic to subscribe to, e.g. 'dbus2mqtt/org.mpris.MediaPlayer2/flow-trigger' | *required* |
| content_type | `str` | One of `json` or `text` | `json`|
| filter       | `str` \| `None` | Optional templated string that must evaluate to a boolean result. When False, the flow is not triggered | |

When triggered, the following context parameters are available

| Name         | Type   | Description      |
|--------------|--------|------------------|
| trigger_type | `str`  | 'mqtt_message'   |
| topic        | `str`  | MQTT topic       |
| payload      | `any`  | text or json deserialized MQTT message payload |

Example flow

```yaml
flows:
  - name: "Mute"
    triggers:
      - type: mqtt_message
        topic: dbus2mqtt/org.mpris.MediaPlayer2/command
        filter: "{{ payload.get('action') == 'Mute' }}"
    actions:
      - type: log
        msg: |
          Flow triggered by MQTT message, payload.action={{ payload.get('action') }}
```

!!! note
    If `topic` overlaps with `subscription[].interfaces[].mqtt_command_topic` and the JSON payload structure follows `mqtt_command_topic` layout, a dbus call will be executed as well. Similar, warnings will be logged if a message does not match any flow or D-Bus method.

## context_changed

Triggered when the dbus2mqtt context was updated by a `context_set` action. For now only `global_context` updates result in a `context_changed` trigger.

```yaml
- type: context_changed
```

Trigger configuration:

| Name   | Type | Description  | Default |
|-------|------|--------------|---------|
| scope | `str` | For now, only `global` is supported | `global` |

When triggered, the following context parameters are available

| Name         | Type   | Description      |
|--------------|--------|------------------|
| scope        | `str`  | Scope of the context that changed, for now this can only be `global` |
