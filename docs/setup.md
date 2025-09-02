# Setup

## Installation

First, create your own dbus2mqtt configuration file or pick one of the examples. Like the [home_assistant_media_player.yaml](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples/home_assistant_media_player.yaml) example from this repository.

```bash
mkdir -p $HOME/.config/dbus2mqtt
cp .env.example $HOME/.config/dbus2mqtt/.env
curl https://raw.githubusercontent.com/jwnmulder/dbus2mqtt/main/docs/examples/home_assistant_media_player.yaml -o $HOME/.config/dbus2mqtt/config.yaml
```

Make sure to update the .env file with your correct MQTT connection details. It will look like this

```bash
MQTT__HOST=localhost
MQTT__PORT=1883
MQTT__USERNAME=
MQTT__PASSWORD=
```

### Installing dbus2mqtt with pip

```bash
python -m pip install dbus2mqtt

cd $HOME/.config/dbus2mqtt
dbus2mqtt --config config.yaml
```

### Docker based setup (with auto start behavior)

```bash
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

## Configuration reference

dbus2mqtt leverages [jsonargparse](https://jsonargparse.readthedocs.io/en/stable/) which allows configuration via either yaml configuration, CLI or environment variables. Until this is fully documented have a look at the examples in this repository.

### dbus2mqtt **mqtt** config

MQTT connection details can be configured via a mix of environment variables and yaml configuration.

| YAML config key            | Env vars         | Description              |
| -------------------------- | ---------------- | ------------------------ |
| `mqtt.host`                | `MQTT__HOST`     | Hostname or IP           |
| `mqtt.port`                | `MQTT__PORT`     | Port, defaults to `1883` |
| `mqtt.username`            | `MQTT__USERNAME` | Username                 |
| `mqtt.password`            | <nobr>`MQTT__PASSWORD`</nobr> | Password    |
| `mqtt.subscription_topics` |                  | List of topics that dbus2mqtt will subscribe to, defaults to `["dbus2mqtt/#"]` |

### dbus2mqtt **dbus** config

| YAML config key            | Description              |
| -------------------------- | ------------------------ |
| `dbus.bus_type`            | One of `SESSION` or `SYSTEM`, defaults to `SESSION` |
| `dbus.subscriptions`       | See [subscriptions](subscriptions.md) |

### dbus2mqtt **flow** config

Flows allow for additional actions to be executed on pre-defined triggers. Details in flow action and flow triggers can be found on: [flows](flows/index.md)

| YAML config key              | Description              |
| ---------------------------- | ------------------------ |
| `flows`                      | Global flow definitions, see [flows](flows/index.md) for details       |
| `dbus.subscriptions[].flows` | Subscription specific flow definitions, see [flows](flows/index.md) for details       |
