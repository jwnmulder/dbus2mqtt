---
hide:
  - toc
---

# Linux Desktop (WIP)

## Introduction

> **Warning:** This is not working, dbus-next is validating property names and bails on `power-saver-enable`

## Setup activities

Trying out this example

```bash
uv run dbus2mqtt --config docs/examples/linux_desktop.yaml
```

## Features

* Desktop notifications

## Desktop notifications

<https://specifications.freedesktop.org/notification-spec/1.3/>
<https://specifications.freedesktop.org/icon-naming-spec/latest/>

```bash
mqtt publish -t dbus2mqtt/Notifications/command -m '{ "method": "Notify", "args": ["dbus2mqtt", 0, "dialog-information", "dbus2mqtt", "Message from <b><i>dbus2mqtt</i></b>", [], {}, 5000] }'
```

```xml
      <arg type="s" name="app_name" direction="in"/>
      <arg type="u" name="replaces_id" direction="in"/>
      <arg type="s" name="app_icon" direction="in"/>
      <arg type="s" name="summary" direction="in"/>
      <arg type="s" name="body" direction="in"/>
      <arg type="as" name="actions" direction="in"/>
      <arg type="a{sv}" name="hints" direction="in"/>
      <arg type="i" name="expire_timeout" direction="in"/>
      <arg type="u" name="id" direction="out"/>
```

```bash
gdbus call --session \
  --dest=org.freedesktop.Notifications \
  --object-path=/org/freedesktop/Notifications \
  --method=org.freedesktop.Notifications.Notify \
  "" \
  0 \
  "icon name" \
  "summary" \
  "body message" \
  '[]' \
  '{}' \
  5000
```

## Gnome SessionManager

The following table lists the supported commands, their descriptions, and an example JSON payload for invoking them via MQTT.

dbus methods can be invoked by sendig the JSON payload to MQTT topic `dbus2mqtt/SessionManager/command`.

For an overview of commands have a look at <https://docs.flatpak.org/en/latest/portal-api-reference.html>
