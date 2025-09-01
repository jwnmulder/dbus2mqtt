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

| name | description |
|------|-------------|
| N/A  | N/A         |

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

| name | type | description |
|------|------|-------------|
| bus_name  | string | bus_name of the object that was registered on dbus |
| path      | string | path of the object that was registered on dbus |
| interface | string | name of interface for which the signal was triggered |
| signal    | string | name of the signal, e.g. 'Seeked'
| args      | list   | signal arguments, list of objects |

## object_added

This trigger is fired during startup or when a new object appears on D-Bus that matches the `bus2mqtt` subscription.

```yaml
- type: object_added
```

When triggered, the following context parameters are available

| name | description |
|------|-------------|
| bus_name | bus_name of the object that was registered on dbus |
| path     | path of the object that was registered on dbus |

## object_removed

```yaml
- type: object_removed
```

When triggered, the following context parameters are available

| name | description |
|------|-------------|
| bus_name | bus_name of the object that was registered on dbus |
| path     | path of the object that was registered on dbus |

## mqtt_message

```yaml
- type: mqtt_message
  topic: dbus2mqtt/org.mpris.MediaPlayer2/flow-trigger
  filter: "{{ payload.get('action') == 'Mute' }}"
```

Listens for MQTT message on the configured topic. The message payload is expected to be JSON formatted

| key | description  |
|------|-------------|
| topic     | topic to subscribe to, e.g. 'dbus2mqtt/org.mpris.MediaPlayer2/flow-trigger' |
| filter    | A templated string that must evaluate to a boolean result. When False, the flow is not triggered |

!!! note
    If `topic` overlaps with `subscription[].interfaces[].mqtt_command_topic` and the JSON payload structure follows `mqtt_command_topic` layout, a dbus call will be executed as well.

When triggered, the following context parameters are available

| name | type | description |
|------|------|-------------|
| topic     | string | mqtt topic |
| payload   | any | json deserialized MQTT message payload  |

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
