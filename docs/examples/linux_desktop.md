# Linux Desktop

> **Warning:** This is not working, dbus-next is validating property names and bails on `power-saver-enable`

Trying out this example

```bash
uv run dbus2mqtt --config docs/examples/linux_desktop.yaml
```

This example shows how this dbus2mqtt can act as a bridge between the MPRIS player and Home Assistant.

Features:

* ...

## Commands

The following table lists the supported commands, their descriptions, and an example JSON payload for invoking them via MQTT.

dbus methods can be invoked by sendig the JSON payload to MQTT topic `dbus2mqtt/Desktop/command`.

For an overview of commands have a look at <https://docs.flatpak.org/en/latest/portal-api-reference.html>
