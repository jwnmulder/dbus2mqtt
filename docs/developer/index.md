# Developer guide

## Specifications

Generic DBus specifications:

* [D-Bus Tutorial](https://dbus.freedesktop.org/doc/dbus-tutorial.html)
* [D-Bus Specification](https://dbus.freedesktop.org/doc/dbus-specification.html)

## Running from source

```bash
uv run main.py --config config.yaml
```

## Activate Python virtual env

```bash
uv sync
source .venv/bin/activate
```

## Linting

```bash
# run pre-commit linters
uv run pre-commit run --all-files

# setup pre-commit to automatically run linters via git hooks
uv run pre-commit install
```

## Publishing and subscribing to MQTT messages

Multiple MQTT client exist that can be used for testing, e.g.

* [MQTT Explorer](https://mqtt-explorer.com/)
* [github.com/RISE-Maritime/mqtt-cli](https://github.com/RISE-Maritime/mqtt-cli)

### Using mqtt-cli

```bash
source .env

mqtt() {
  uvx --from mqtt-cli mqtt \
    --host "$MQTT__HOST" \
    --user "$MQTT__USERNAME" \
    --password "$MQTT__PASSWORD" \
    "$@"
}

mqtt --help
mqtt subscribe --topic 'dbus2mqtt/#'
mqtt publish -t dbus2mqtt/org.mpris.MediaPlayer2/command -m '{ "method": "Play" }'
```
