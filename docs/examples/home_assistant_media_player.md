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

The configuration shown below creates a few components in Home Assistant

* Media Player
* MQTT sensor listening on topic `dbus2mqtt/org.mpris.MediaPlayer2/state`

```yaml+jinja
mqtt:
  sensor:
    - name: MPRIS Media Player
      state_topic: dbus2mqtt/org.mpris.MediaPlayer2/state
      json_attributes_topic: dbus2mqtt/org.mpris.MediaPlayer2/state
      value_template: >-
        {% set status = value_json.PlaybackStatus %}
        {{ {'Playing': 'playing', 'Paused': 'paused', 'Stopped': 'idle'}.get(status, 'off') }}

  image:
    - name: MPRIS Media Player MQTT image
      image_topic: dbus2mqtt/org.mpris.MediaPlayer2/artUrlImage

media_player:
  - platform: media_player_template
    media_players:
      mpris_media_player:
        device_class: receiver
        friendly_name: MPRIS Media Player
        value_template: "{{ states('sensor.mpris_media_player') }}"

        current_volume_template: "{{ state_attr('sensor.mpris_media_player', 'Volume') }}"
        current_is_muted_template: "{{ state_attr('sensor.mpris_media_player', 'Volume') == 0 }}"
        current_position_template: "{{ state_attr('sensor.mpris_media_player', 'Position') }}"

        # title: 'xesam:title' or filename without extension from 'xesam:url'
        title_template: >-
          {% set metadata = state_attr('sensor.mpris_media_player', 'Metadata') or {} %}
          {% set title = metadata.get('xesam:title', '') %}
          {% if not title or title == '' %}
          {% set title = metadata.get('xesam:url', '') | regex_findall(find='([^\\/]+?)(?:\.[^.\\/]+)?$') | first | default('') %}
          {% endif %}
          {{ title }}

        media_content_type_template: music  # needed to show 'artist'
        media_duration_template: "{{ (state_attr('sensor.mpris_media_player', 'Metadata') or {}).get('mpris:length', 0) }}"
        album_template: "{{ (state_attr('sensor.mpris_media_player', 'Metadata') or {}).get('xesam:album', '') }}"
        artist_template: >-
          {% set artist = (state_attr('sensor.mpris_media_player', 'Metadata') or {}).get('xesam:artist', '') %}
          {% if artist is string %}
          {% set artist = [artist] %}
          {% endif %}
          {{ artist | first }}

        # mpris:artUrl might contain a file:// schema. In these cases we rely on images published via MQTT
        media_image_url_template: >-
          {% set mpris_metadata = state_attr('sensor.mpris_media_player', 'Metadata') or {} %}
          {% set mpris_art_url = mpris_metadata.get('mpris:artUrl', '') %}
          {% set mpris_url = mpris_metadata.get('xesam:url') %}

          {% if mpris_art_url.startswith('http') %}
            {{ mpris_art_url }}
          {% elif mpris_art_url.startswith('file://') %}
            http://127.0.0.1:8123{{ state_attr('image.mpris_media_player_mqtt_image', 'entity_picture') }}
          {% else %}
            {{
                mpris_url | regex_replace(
                  find='https:\/\/www\\.youtube\\.com\/watch\\?v=([^&]+).*',
                  replace='https://img.youtube.com/vi/\\1/maxresdefault.jpg'
                )
            }}
          {% endif %}

        turn_off:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: >
              {"method": "Quit"}
        play:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: >
              {"method": "Play"}
        pause:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: >
              {"method": "Pause"}
        stop:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: >
              {"method": "Stop"}
        next:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: >
              {"method": "Next"}
        previous:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: >
              {"method": "Previous"}
        seek:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: >
              { "method": "SetPosition", "args": ["{{ state_attr('sensor.mpris_media_player', 'Metadata')['mpris:trackid'] }}", {{ position | int }}] }
        set_volume:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: >
              {"property": "Volume", "value": {{volume}} }
        volume_up:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: >
              {"property": "Volume", "value": {{ [1, (state_attr('sensor.mpris_media_player', 'Volume') + 0.1)] | min }} }
        volume_down:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: >
              {"property": "Volume", "value": {{ [0, (state_attr('sensor.mpris_media_player', 'Volume') - 0.1)] | max }} }
```
