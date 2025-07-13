# dbus2mqtt

**dbus2mqtt** is a Python application that bridges **DBus** with **MQTT**.
It lets you forward Linux D-Bus signals and properties to MQTT topics, call D-Bus methods via MQTT messages, and shape payloads using flexible **Jinja2 templating**.

This makes it easy to integrate Linux desktop services or system signals into MQTT-based workflows - including **Home Assistant**.

## ✨ Features

* 🔗 Forward **D-Bus signals** to MQTT topics.
* 🧠 Enrich or transform **MQTT payloads** using Jinja2 templates and additional D-Bus calls.
* ⚡ Trigger message publishing via **signals, timers, property changes, or startup events**.
* 📡 Expose **D-Bus methods** for remote control via MQTT messages.
* 🏠 Includes example configurations for **MPRIS** and **Home Assistant Media Player** integration.

## Project status

**dbus2mqtt** is considered stable for the use-cases it has been tested against, and is actively being developed. Documentation is continuously being improved.

Initial testing has focused on MPRIS integration. A table of tested MPRIS players and their supported methods can be found here: [home_assistant_media_player.md](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples/home_assistant_media_player.md)

## Getting started with dbus2mqtt

Create a `config.yaml` file with the contents shown below. This configuration will expose all bus properties from the `org.mpris.MediaPlayer2.Player` interface to MQTT on the `dbus2mqtt/org.mpris.MediaPlayer2/state` topic. Have a look at [docs/examples](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples.md) for more examples

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


### Run using docker with auto start behavior

To build and run dbus2mqtt using Docker with the [home_assistant_media_player.yaml](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples/home_assistant_media_player.yaml) example from this repository.

```bash
# setup configuration
mkdir -p $HOME/.config/dbus2mqtt
cp docs/examples/home_assistant_media_player.yaml $HOME/.config/dbus2mqtt/config.yaml
cp .env.example $HOME/.config/dbus2mqtt/.env

# run image and automatically start on reboot
sudo docker pull jwnmulder/dbus2mqtt
sudo docker run --detach --name dbus2mqtt \
  --volume "$HOME"/.config/dbus2mqtt:"$HOME"/.config/dbus2mqtt \
  --volume /run/user:/run/user \
  --env DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" \
  --env-file "$HOME"/.config/dbus2mqtt/.env \
  --user $(id -u):$(id -g) \
  --privileged \
  --restart unless-stopped \
  jwnmulder/dbus2mqtt \
  --config "$HOME"/.config/dbus2mqtt/config.yaml

# view logs
sudo docker logs dbus2mqtt -f
```

## Examples

This repository contains examples under [docs/examples](https://github.com/jwnmulder/dbus2mqtt/blob/main//docs/examples.md). The most complete one being [MPRIS to Home Assistant Media Player integration](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples/home_assistant_media_player.md)

## Configuration reference

dbus2mqtt leverages [jsonargparse](https://jsonargparse.readthedocs.io/en/stable/) which allows configuration via either yaml configuration, CLI or environment variables. Until this is fully documented have a look at the examples in this repository.

### MQTT and D-Bus connection details

```bash
# dbus_fast configuration
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

# dbus2mqtt configuration
MQTT__HOST=localhost
MQTT__PORT=1883
MQTT__USERNAME=
MQTT__PASSWORD=
```

or

```yaml
mqtt:
  host: localhost
  port: 1883
  subscription_topics:
    - dbus2mqtt/#
```

### Exposing dbus methods

```yaml
dbus:
  subscriptions:
    - bus_name: org.mpris.MediaPlayer2.*
      path: /org/mpris/MediaPlayer2
      interfaces:
        - interface: org.mpris.MediaPlayer2.Player
          mqtt_command_topic: dbus2mqtt/org.mpris.MediaPlayer2/command
          methods:
            - method: Pause
            - method: Play
```

This configuration will expose 2 methods. Triggering methods can be done by publishing json messages to the `dbus2mqtt/org.mpris.MediaPlayer2/command` MQTT topic. Arguments can be passed along in `args`.

Some examples that call methods  on **all** bus_names matching the configured pattern

```json
{
    "method": "Play",
}
```

```json
{
    "method": "OpenUri",
    "args": []
}
```

To specifically target objects the properties `bus_name` and/or `path` can be used. Both properties support wildcards

```json
{
    "method": "Play",
    "bus_name": "*.firefox",
    "path": "/org/mpris/MediaPlayer2"
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

A reference of all supported flow triggers and actions can be found on [Flows](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/flows.md)

## Jinja templating

TODO: Document Jinja templating, for now see the [MPRIS to Home Assistant Media Player integration](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples/home_assistant_media_player.md) example
