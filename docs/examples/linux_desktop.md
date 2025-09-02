---
hide:
  - toc
---

# Linux Desktop

Use dbus2mqtt to interface with your Linux desktop

Pre-requisites:

* Any Linux Desktop will do

## Features

* Desktop notifications (via org.freedesktop.Notifications)

## Setup activities

Just run dbus2mqtt with the example configuration in this repository

```bash
uv run dbus2mqtt --config docs/examples/linux_desktop.yaml
```

## Desktop notifications

Trigger a desktop notification by sending one of the following example payloads to `dbus2mqtt/Notifications/command`

Example notification with no timeout

```json
--8<-- "docs/examples/linux_desktop/notify.json"
```

Example notification with actions and hints, that automatically disappears after 5 seconds

```json
--8<-- "docs/examples/linux_desktop/notify_with_actions_and_hints.json"
```

Further references:

* <https://specifications.freedesktop.org/notification-spec/1.3/>
* <https://specifications.freedesktop.org/icon-naming-spec/latest/>

<!-- ## Gnome SessionManager

!!! note
    work in progress

The following table lists the supported commands, their descriptions, and an example JSON payload for invoking them via MQTT.

dbus methods can be invoked by sendig the JSON payload to MQTT topic `dbus2mqtt/SessionManager/command`.

For an overview of commands have a look at <https://docs.flatpak.org/en/latest/portal-api-reference.html> -->
