---
hide:
  - toc
---

# dbus2mqtt internal state (WIP)

This will publish the dbus2mqtt's internal state to the `dbus2mqtt/state` MQTT topic every 5 seconds

## Setup activities

Execute the following command to run dbus2mqtt with the example configuration in this repository.

```bash
dbus2mqtt --config docs/examples/dbus2mqtt_internal_state.yaml
```

## Example messages

The following message is published every 5 seconds to `dbus2mqtt/state`

```json
{"now": "2025-04-23T16:01:34.985452", "dbus_list": ["org.freedesktop.systemd1", "org.gnome.SessionManager"]}
```
