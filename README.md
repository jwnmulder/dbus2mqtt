# dbus2mqtt

**dbus2mqtt** is a Python application that bridges **Linux D-Bus** with **MQTT**.
It lets you forward D-Bus signals and properties to MQTT topics, call D-Bus methods via MQTT messages, and shape payloads using flexible **Jinja2 templating**.

This makes it easy to integrate Linux desktop services or system signals into MQTT-based workflows - including **Home Assistant**.

## ✨ Features

* 🔗 Forward **D-Bus signals** to MQTT topics.
* 🧠 Enrich or transform **MQTT payloads** using Jinja2 templates and additional D-Bus calls.
* ⚡ Trigger message publishing via **signals, timers, property changes, or startup events**.
* 📡 Expose **D-Bus methods** for remote control via MQTT messages.
* 🏠 Includes example configurations for **MPRIS** and **Home Assistant Media Player** integration.

TODO list

* Improve error handling when deleting message with 'retain' set. WARNING:dbus2mqtt.mqtt_client:on_message: Unexpected payload, expection json, topic=dbus2mqtt/org.mpris.MediaPlayer2/command, payload=, error=Expecting value: line 1 column 1 (char 0)
* Property set only works the first time, need to restart after which the first set will work again
* Print found bus_names at startup (or empty if no matching subscriptions)
* Create a release on pypiPyPI
* Release a docker image

## Getting started with dbus2mqtt

Create a `config.yaml` file with the contents shown below. This configuration will expose all bus properties from the `org.mpris.MediaPlayer2.Player` interface to MQTT on the `dbus2mqtt/org.mpris.MediaPlayer2/state` topic. Have a look at [docs/examples](docs/exmaples.md) for more examples

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
            - type: bus_name_added
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
                {{ dbus_call(mpris_bus_name, path, 'org.freedesktop.DBus.Properties', 'GetAll', ['org.mpris.MediaPlayer2.Player']) | to_yaml }}
```

MQTT connection details can be configured in that same `config.yaml` file or via environment variables. For now create a `.env` file with the following contents.

```bash
MQTT__HOST=localhost
MQTT__PORT=1883
MQTT__USERNAME=
MQTT__PASSWORD=
```

To run dbus2mqtt from source (requires uv to be installed)

```bash
uv run main.py --config config.yaml
```

To build and run dbus2mqtt using Docker with the [home_assistant_media_player.yaml](docs/examples/home_assistant_media_player.yaml) example from this repository

```bash
# setup configuration
mkdir -p $HOME/.config/dbus2mqtt
cp docs/examples/home_assistant_media_player.yaml $HOME/.config/dbus2mqtt/config.yaml
cp .env.example $HOME/.config/dbus2mqtt/.env

# build image
docker build -t jwnmulder/dbus2mqtt:latest .

# run image and automatically start on reboot
docker run --detach --name dbus2mqtt \
  --volume "$HOME"/.config/dbus2mqtt:"$HOME"/.config/dbus2mqtt \
  --env DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" \
  --user $(id -u):$(id -g) \
  --volume /run/user:/run/user \
  --env-file "$HOME"/.config/dbus2mqtt/.env \
  --privileged \
  --restart unless-stopped \
  jwnmulder/dbus2mqtt \
  --config "$HOME"/.config/dbus2mqtt/config.yaml

# view logs
sudo docker logs dbus2mqtt -f
```

## Examples

This repository contains some examples under [docs/examples](docs/examples.md). The most complete one being [MPRIS to Home Assistant Media Player integration](docs/examples/home_assistant_media_player.md)

## Configuration reference

### Exposing dbus methods

```yaml
dbus:
  subscriptions:
    - bus_name: org.mpris.MediaPlayer2.*
      path: /org/mpris/MediaPlayer2
      interfaces:
        - interface: org.mpris.MediaPlayer2.Player
          mqtt_call_method_topic: dbus2mqtt/org.mpris.MediaPlayer2/command
          methods:
            - method: Pause
            - method: Play
```

This configuration will expose 2 methods. Triggering methods can be done by publishing json messages to the `dbus2mqtt/org.mpris.MediaPlayer2/command` MQTT topic. Arguments can be passed along in `args`

```json
{
    "method" : "Play",
}
```

```json
{
    "method" : "OpenUri",
    "args": []
}
```

### Exposing dbus signals

Publishing signals to MQTT topics works by subscribing to the relevant signal and using flows for publishing

```yaml
dbus:
  subscriptions:
    - bus_name: org.mpris.MediaPlayer2.*
      path: /org/mpris/MediaPlayer2
      interfaces:
        - interface: org.freedesktop.DBus.Properties
           signals:
             - signal: PropertiesChanged

      flows:
        - name: "Property Changed flow"
          triggers:
            - type: on_signal
          actions:
            - type: mqtt_publish
              topic: dbus2mqtt/org.mpris.MediaPlayer2/signals/PropertiesChanged
              payload_type: json
```

## Flows

TODO: Document flows, for now see the [MPRIS to Home Assistant Media Player integration](docs/examples/home_assistant_media_player.md) example

## Jinja templating

TODO: Document Jinja templating, for now see the [MPRIS to Home Assistant Media Player integration](docs/examples/home_assistant_media_player.md) example
