# dbus2mqtt

**dbus2mqtt** is a Python application that bridges **DBus** with **MQTT**.
It lets you forward Linux D-Bus signals and properties to MQTT topics, call D-Bus methods via MQTT messages, and shape payloads using flexible **Jinja2 templating**.

This makes it easy to integrate Linux desktop services or system signals into MQTT-based workflows - including **Home Assistant**.

## Features

* 🔗 Forward **D-Bus signals** to MQTT topics.
* 🧠 Enrich or transform **MQTT payloads** using Jinja2 templates and additional D-Bus calls.
* ⚡ Trigger message publishing via **signals, timers, property changes, or startup events**.
* 📡 Expose **D-Bus methods** for remote control via MQTT messages.
* 🏠 Includes example configurations for **MPRIS** and **Home Assistant Media Player** integration.

## Project status

**dbus2mqtt** is considered stable for the use-cases it has been tested against, and is actively being developed. Documentation is continuously being improved.

Initial testing has focused on MPRIS integration. A table of tested MPRIS players and their supported methods can be found on [Mediaplayer integration with Home Assistant](https://jwnmulder.github.io/dbus2mqtt/examples/home_assistant_media_player.html)

## Getting started with dbus2mqtt

Create a `config.yaml` file with the contents shown below. This configuration will expose all bus properties from the `org.mpris.MediaPlayer2.Player` interface to MQTT on the `dbus2mqtt/org.mpris.MediaPlayer2/state` topic.

```yaml
dbus:
  subscriptions:
    - bus_name: org.mpris.MediaPlayer2.*
      path: /org/mpris/MediaPlayer2
      interfaces:
        - interface: org.freedesktop.DBus.Properties
          methods:
            - method: GetAll

      flows:
        - name: "Publish MPRIS state"
          triggers:
            - type: object_added
            - type: schedule
              interval: {seconds: 5}
          actions:
            - type: context_set
              context:
                mpris_bus_name: '{{ dbus_list("org.mpris.MediaPlayer2.*") | first }}'
                path: /org/mpris/MediaPlayer2
            - type: mqtt_publish
              topic: dbus2mqtt/org.mpris.MediaPlayer2/state
              payload_type: json
              payload_template: |
                {{ dbus_call(mpris_bus_name, path, 'org.freedesktop.DBus.Properties', 'GetAll', ['org.mpris.MediaPlayer2.Player']) }}
```

MQTT connection details can be configured in that same `config.yaml` file or via environment variables. For now create a `.env` file with the following contents.

```bash
MQTT__HOST=localhost
MQTT__PORT=1883
MQTT__USERNAME=
MQTT__PASSWORD=
```

### Install and run dbus2mqtt

```bash
python -m pip install dbus2mqtt
dbus2mqtt --config config.yaml
```

See [setup](https://jwnmulder.github.io/dbus2mqtt/setup.html) for more installation options and configuration details.

## Examples

More dbus2mqtt examples can be found in the [examples](https://jwnmulder.github.io/dbus2mqtt/examples/index.html) section.
The most complete one being [Mediaplayer integration with Home Assistant](https://jwnmulder.github.io/dbus2mqtt/examples/home_assistant_media_player.html)

## Exposing dbus methods, properties and signals

See [subscriptions](https://jwnmulder.github.io/dbus2mqtt/subscriptions.html) for documentation on calling methods, setting properties and exposing D-Bus signals to MQTT. When configured, D-Bus methods can be invoked by publishing a message like

```json
{
    "method": "Play"
}
```

## Flows and Jinja based templating

For more advanced use-cases, dbus2mqtt has support for flows and Jinja2 based templates. A reference of all supported flow triggers and actions can be found on [flows](https://jwnmulder.github.io/dbus2mqtt/flows/index.html)

Jinja templating documentation can be found here: [templating](templating/index.md)
