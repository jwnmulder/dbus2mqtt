# D-Bus subscriptions

In order to call D-Bus methods, update properties or expose signals, configure `dbus2mqtt` with at least one subscription to one or more D-Bus objects.

```yaml
dbus:
  subscriptions:
    - bus_name: org.mpris.MediaPlayer2.*
      path: /org/mpris/MediaPlayer2
      interfaces:
        - interface: /org/mpris/MediaPlayer2
          ...
```

`bus_name`, `path` and `interface` should match the dbus object you want to subscribe to. Wildcard patterns are supported for both `bus_name` and `path`

For each subscription, you can configure the behavior of `dbus2mqtt` using any of the options below.

| Field       | Description                    |
|-------------|--------------------------------|
| `interface`  | The D-Bus interface that defines the set of methods, signals, and properties available |
| `mqtt_command_topic` | MQTT topic where `dbus2mqtt` listens for JSON commands. For example `dbus2mqtt/mpris/command`. Value can be a `string` or `templated string` |
| `mqtt_response_topic` | MQTT topic where `dbus2mqtt` published responses on. For example `dbus2mqtt/mpris/response`. Value can be a `string` or `templated string` |
| `methods` | List of methods to expose over MQTT |
| `properties` | List of properties to expose over MQTT |
| `signals` | List of D-Bus signals to subscribe to |

!!! note
    Setting `mqtt_command_topic` will automatically make all configured methods and properties available over MQTT without any additional work

## MQTT commands

Any D-Bus method (when configured) can be called by publishing a MQTT message to the configured `mqtt_command_topic`.

The example configuration below expose 3 methods and one property.

```yaml
dbus:
  subscriptions:
    - bus_name: org.mpris.MediaPlayer2.*
      path: /org/mpris/MediaPlayer2
      interfaces:
        - interface: org.mpris.MediaPlayer2.Player
          mqtt_command_topic: dbus2mqtt/org.mpris.MediaPlayer2/command
          mqtt_response_topic: dbus2mqtt/org.mpris.MediaPlayer2/response/{{ method }}
          methods:
            - method: Pause
            - method: Play
            - method: Seek
          properties:
            - property: Volume
```

### Calling methods

Methods are invoked after publishing a specific JSON message to the `dbus2mqtt/org.mpris.MediaPlayer2/command` MQTT topic. Arguments can be passed along in `args`.

| key          | type   | description  |
|--------------|--------|--------------|
| method       | str    | Method name  |
| args         | list   | Optional list of arguments that matches the methods D-Bus signature |
| bus_name     | str    | Only invoke on dbus objects where bus_name matches, defaults to `*` |
| path         | str    | Only invoke on dbus objects where path matches, defaults to `*`     |

!!! note
    If no `bus_name` and `path` is given, commands are executed against all matching
    dbus objects. To target specific dbus objects make sure to set both keys.

Example 1, calling `Play` on all registered MPRIS players

```json
{
    "method": "Play"
}
```

Example 2, invoking `Seek` with arguments and targeting only the VLC MPRIS player

```json
{
    "method": "Seek",
    "args": [60000000],
    "bus_name": "*.vlc",
    "path": "/org/mpris/MediaPlayer2"
}
```

### Property updates

Properties can be updated by publishing a specific JSON message to the `dbus2mqtt/org.mpris.MediaPlayer2/command` MQTT topic.

| key          | type   | description    |
|--------------|--------|----------------|
| property     | str    | Property name  |
| value        | any    | Property value |
| bus_name     | str    | Only invoke on dbus objects where bus_name matches, defaults to `*`  |
| path         | str    | Only invoke on dbus objects where path matches, defaults to `*`      |

Example, setting `Volume` to 1.0 for Firefox MPRIS player only

```json
{
    "property": "Volume",
    "value": 1.0,
    "bus_name": "*.firefox",
    "path": "/org/mpris/MediaPlayer2"
}
```

### Command responses

If set, D-Bus responses to commands will be published the configured `mqtt_response_topic` MQTT topic.

!!! note
    `dbus2mqtt` publishes one response per targeted dbus object.
    When two dbus objects are targeted, two separate responses will be published.

Example response for method calls

```json
{
  "bus_name": "org.mpris.MediaPlayer2.vlc",
  "path": "/org/mpris/MediaPlayer2",
  "interface": "org.freedesktop.DBus.Properties",
  "timestamp": "2025-08-24T16:36:42.522104",
  "method": "GetAll",
  "args": ["org.mpris.MediaPlayer2.Player"],
  "success": true,
  "result": {
    "Metadata": {},
    "Position": 0,
    "PlaybackStatus": "Stopped",
    "LoopStatus": "None",
    "Shuffle": false,
    "Volume": 0.0,
    "Rate": 1.0,
    "MinimumRate": 0.032,
    "MaximumRate": 32.0,
    "CanControl": true,
    "CanPlay": false,
    "CanGoNext": true,
    "CanGoPrevious": true,
    "CanPause": false,
    "CanSeek": false
  }
}
```

Example response for property updates

```json
{
  "bus_name": "org.mpris.MediaPlayer2.vlc",
  "path": "/org/mpris/MediaPlayer2",
  "interface": "org.mpris.MediaPlayer2.Player",
  "timestamp": "2025-08-24T16:39:13.199826",
  "property": "Volume",
  "value": 0.99,
  "success": true,
  "result": 0.99
}
```

## Exposing dbus signals

Publishing signals to MQTT topics works by subscribing to the relevant signal and using flows for publishing.

Signals configuration parameters

| Field       | Description                    |
|-------------|--------------------------------|
| `signal`    | Name of the signal |
| `filter`    | Templated string that should evaluate to a boolean result. `True` will accept signals, `False` will drop signals |

In contrast to calling methods or setting properties, signals are not automatically published to MQTT topcis.
To do so, configure a flow as shown below.

```yaml
dbus:
  subscriptions:
    - bus_name: org.mpris.MediaPlayer2.*
      path: /org/mpris/MediaPlayer2
      interfaces:
        - interface: org.freedesktop.DBus.Properties
          signals:
            - signal: PropertiesChanged
              filter: "{{ args[0] == 'org.mpris.MediaPlayer2.Player' }}"

      flows:
        - name: "Property Changed flow"
          triggers:
            - type: on_signal
          actions:
            - type: mqtt_publish
              topic: dbus2mqtt/org.mpris.MediaPlayer2/signals/PropertiesChanged
              payload_type: json
```

More information on flows can be found in the [flows](flows/index.md) section.
