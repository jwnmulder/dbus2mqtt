---
hide:
  - toc
---

# Mediaplayer integration with Home Assistant

With dbus2mqtt as a bridge between MPRIS players and Home Assistant, it becomes possible to control Linux based media players via Home Assistant.

The Media Player Remote Interfacing Specification (MPRIS) is a standard for controlling Linux media players. It provides a mechanism for compliant media players discovery, basic playback and media player state control as well as a tracklist interface which is used to add context to the current item.

Pre-requisites:

* Home-Assistant with a working MQTT setup
* The community Home-Assistant plugin [github.com/Sennevds/media_player.template](https://github.com/Sennevds/media_player.template)

## Features

* dbus subscription using `org.mpris.MediaPlayer2.*` wildcard to support multiple concurrent MRPIS players
* Every 5 seconds, the state of the `first` known MPRIS player is published to MQTT topic `dbus2mqtt/org.mpris.MediaPlayer2/state`
* Every MPRIS property update immediately publishes the state to MQTT topic `dbus2mqtt/org.mpris.MediaPlayer2/state`
* Support for player commands (see below)

## Setup activities

* Configure the MQTT Sensor and player configuration in Home Assistant with the configuration listed below
* Config dbus2mqtt using the supplied [home_assistant_media_player.yaml](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples/home_assistant_media_player.yaml)

To run, execute the following commands

```bash
dbus2mqtt --config docs/examples/home_assistant_media_player.yaml
```

## Tested configurations

The following MPRIS players are known to work with Home Assistant.

| Application  | Play<br />Pause<br /> | Stop | Next<br />Previous | Seek<br />SetPosition | Volume | Quit | Media Info | Media Image | Notes |
|--------------|-----------------------|------|--------------------|------|--------|------|------------|-------------|-------------------|
| `Firefox`    | ✅ | ✅ | ✅ | ✅ |    | ❌ | ✅ | ✅ |  |
| `VLC`        | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |    |  |
| `Chromium`   | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✔️ | Images not working when Chromium is running as snap |
| `Kodi`       | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | Requires Kodi plugin [MediaPlayerRemoteInterface](https://github.com/wastis/MediaPlayerRemoteInterface) |

!!! note
    More players that support MPRIS (but have not been tested) can be found here: <https://wiki.archlinux.org/title/MPRIS>

## Player commands

The following table lists player commands, their descriptions, and an example JSON payload for invoking them via MQTT.

Dbus methods can be invoked by sendig the JSON payload to MQTT topic `dbus2mqtt/org.mpris.MediaPlayer2/command`. Method calls will be done for all matching players. The same applies to property updates.

| Method<br />Property | Description                       | Example MQTT JSON Payload                           |
|---------------|------------------------------------------|------------------------------------------------|
| `Play`        | Starts playback                          | `#!json { "method": "Play" }`                         |
| `Pause`       | Pauses playback                          | `#!json { "method": "Pause" }`                        |
| `PlayPause`   | Toggles between play and pause           | `#!json { "method": "PlayPause" }`                    |
| `Stop`        | Stops playback                           | `#!json { "method": "Stop" }`                         |
| `Next`        | Next                                     | `#!json { "method": "Next" }`                         |
| `Previous`    | Previous                                 | `#!json { "method": "Previous" }`                     |
| `Seek`        | Seek forward or backward in micro seconds  | `#!json { "method": "Seek", "args": [60000000] }`   |
| `Volume`      | Set volume (double between 0 and 1)      | `#!json { "property": "Volume", "value": 1.0 }`        |
| `SetPosition` | Set / seek to position in micro seconds. First arguments needs to be trackid which can be determined via Metadata.mpris:trackid | `#!json { "method": "SetPosition", "args": ["/org/mpris/MediaPlayer2/firefox", 170692139] }`                         |
| `Quit`        | Quits the media player                   | `#!json { "method": "Quit" }`                         |

For an overview of MPRIS commands have a look at <https://mpris2.readthedocs.io/en/latest/interfaces.html#mpris2.MediaPlayer2>

## Home Assistant configuration

Besides setting up `dbus2mqtt`, Home Assistant needs to be configured as well. The configuration shown below creates the necessary components in Home Assistant for controlling MPRIS Media Players. Three components will be setup.

* MQTT sensor listening on topic `dbus2mqtt/org.mpris.MediaPlayer2/state`
* MQTT image listening on topic `dbus2mqtt/org.mpris.MediaPlayer2/artUrlImage`
* Media Player

```yaml+jinja title='config/packages/mqtt_mediaplayer.yaml'
--8<-- "docs/examples/home_assistant_media_player/mqtt_mediaplayer.yaml"
```

Source: [mqtt_mediaplayer.yaml](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples/home_assistant_media_player/mqtt_mediaplayer.yaml)
