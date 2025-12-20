# Flow triggers

## schedule

```yaml
- type: schedule
  interval: {seconds: 5}
```

Schedule based triggers can be configured by setting either a cron or interval parameter. Scheduling is based on the   APScheduler library and allows the following configuration options

| key | description  |
|------|-------------|
| interval | dict of time units and intervals, see <https://apscheduler.readthedocs.io/en/3.x/modules/triggers/interval.html>    |
| cron     | dict of time units and cron expressions, see <https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html> |

When triggered, the following context parameters are available

| name         | type   | description      |
|--------------|--------|------------------|
| trigger_type | string | 'schedule'       |

## dbus_object_added

This trigger is fired during startup or when a new object appears on D-Bus that matches the `bus2mqtt` subscription.

```yaml
- type: dbus_object_added
```

When triggered, the following context parameters are available

| name         | type   | description      |
|--------------|--------|------------------|
| trigger_type | string | 'object_added'   |
| bus_name     | string | bus_name of the object that was registered on dbus |
| path         | string | path of the object that was registered on dbus |

## dbus_object_removed

```yaml
- type: dbus_object_removed
```

When triggered, the following context parameters are available

| name         | type   | description      |
|--------------|--------|------------------|
| trigger_type | string | 'object_removed' |
| bus_name     | string | bus_name of the object that was registered on dbus |
| path         | string | path of the object that was registered on dbus |

## dbus_signal

```yaml
- type: dbus_signal
  interface: org.freedesktop.DBus.Properties
  signal: PropertiesChanged
```

DBus signals triggers must be configured with an anterface and path. Note that only subscribed signals can be configured as a trigger.

| key | description  |
|------|-------------|
| interface | interface to filter on, e.g. 'org.freedesktop.DBus.Properties' |
| signal    | signal name to filter on, e.g. PropertiesChanged |

When triggered, the following context parameters are available

| name         | type   | description      |
|--------------|--------|------------------|
| trigger_type | string | 'dbus_signal'    |
| bus_name     | string | bus_name of the object that was registered on dbus |
| path         | string | path of the object that was registered on dbus |
| interface    | string | name of interface for which the signal was triggered |
| signal       | string | name of the signal, e.g. 'Seeked' |
| args         | list   | signal arguments, list of objects |

## mqtt_message

```yaml
- type: mqtt_message
  topic: dbus2mqtt/org.mpris.MediaPlayer2/flow-trigger
  filter: "{{ payload.get('action') == 'Mute' }}"
```

Listens for MQTT messages on the configured topic. The message payload is expected to be JSON formatted

Trigger configuration:

| key | description  |
|------|-------------|
| topic     | topic to subscribe to, e.g. 'dbus2mqtt/org.mpris.MediaPlayer2/flow-trigger' |
| filter    | A templated string that must evaluate to a boolean result. When False, the flow is not triggered |

When triggered, the following context parameters are available

| name         | type   | description      |
|--------------|--------|------------------|
| trigger_type | string | 'mqtt_message'   |
| topic        | string | mqtt topic |
| payload      | any    | json deserialized MQTT message payload  |

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

```yaml
- type: context_changed
```

Triggered when the dbus2mqtt context was updated by a `context_set` action. For now only `global_context` updates result in a `context_changed` trigger.

Trigger configuration:

| key | description  |
|------|-------------|
| scope     | `global` |

When triggered, the following context parameters are available

| name         | type   | description      |
|--------------|--------|------------------|
| scope        | string | Scope of the context that changed, for now this can only be `global` |
