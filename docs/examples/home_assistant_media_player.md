# Mediaplayer integration with Home Assistant

With dbus2mqtt as a bridge between MPRIS players and Home Assistant, it becomes possible to control Linux based media players via Home Assistant.

The Media Player Remote Interfacing Specification (MPRIS) is a standard for controlling Linux media players. It provides a mechanism for compliant media players discovery, basic playback and media player state control as well as a tracklist interface which is used to add context to the current item.

Pre-requisites:

* Home-Assistant with a working MQTT setup, the [media_player.template](https://github.com/Sennevds/media_player.template/tree/master) plugin installed and a working MQTT setup
plugins installed

Features:

* dbus subscription using `org.mpris.MediaPlayer2.*` wildcard to support multiple concurrent MRPIS players
* Every 5 seconds, the state if the `first` known MPRIS player is published to MQTT topic `dbus2mqtt/org.mpris.MediaPlayer2/state`
* Every MPRIS property update immediately publishes the state to MQTT topic `dbus2mqtt/org.mpris.MediaPlayer2/state`
* Support for player commands (see below)

Configuration activities

* MQTT Sensor and player configuration in Home Assistant (see below)
* dbus2mqtt setup using the supplied `home_assistant_media_player.yaml`

Execute the following command to run dbus2mqtt with the example configuration in this repository.

```bash
dbus2mqtt --config docs/examples/home_assistant_media_player.yaml
```


## Tested configurations

The following setup is known to work with Home Assistant.

| Application  | Play<br />Pause<br /> | Stop | Next<br />Previous | Seek<br />SetPosition | Volume | Quit | Media Info | Media Image |
|--------------|-----------------------|------|--------------------|------|--------|------|------------|-------------|
| `Firefox`    | ✅ | ✅ | ✅ | ✅ | | ❌ | ✅ | Youtube only |
| `VLC` | | | | | | | | | |

## Player commands

The following table lists player commands, their descriptions, and an example JSON payload for invoking them via MQTT.

Dbus methods can be invoked by sendig the JSON payload to MQTT topic `dbus2mqtt/org.mpris.MediaPlayer2/command`. Method calls will be done for all matching players

| Interface                       | Method<br />Property | Description                       | Example MQTT JSON Payload                           |
|---------------------------------|---------------|------------------------------------------|------------------------------------------------|
| `org.mpris.MediaPlayer2.Player` | `Play`        | Starts playback                          | `{ "method": "Play" }`                         |
| `org.mpris.MediaPlayer2.Player` | `Pause`       | Pauses playback                          | `{ "method": "Pause" }`                        |
| `org.mpris.MediaPlayer2.Player` | `PlayPause`   | Toggles between play and pause           | `{ "method": "PlayPause" }`                    |
| `org.mpris.MediaPlayer2.Player` | `Next`        | Next                                     | `{ "method": "Next" }`                         |
| `org.mpris.MediaPlayer2.Player` | `Previous`    | Previous                                 | `{ "method": "Previous" }`                     |
| `org.mpris.MediaPlayer2.Player` | `Stop`        | Stops playback                           | `{ "method": "Stop" }`                         |
| `org.mpris.MediaPlayer2.Player` | `Seek`        | Seek forward or backward in micro seconds  | `{ "method": "Seek", "args": [60000000] }`   |
| `org.mpris.MediaPlayer2.Player` | `Volume`      | Set volume                               | `{ "property": "Volume", "value": 50 }`        |
| `org.mpris.MediaPlayer2.Player` | `SetPosition` | Set / seek to position in micro seconds. First arguments needs to be trackid which can be determined via Metadata.mpris:trackid | `{ "method": "SetPosition", "args": ["/org/mpris/MediaPlayer2/firefox", 170692139] }`                         |
| `org.mpris.MediaPlayer2`        | `Quit`        | Quits the media player                   | `{ "method": "Quit" }`                         |

For an overview of MPRIS commands have a look at <https://mpris2.readthedocs.io/en/latest/interfaces.html#mpris2.MediaPlayer2>

## Home Assistant configuration

The configuration shown below creates a few components in Home Assistant

* Media Player
* MQTT sensor listening on topic `dbus2mqtt/org.mpris.MediaPlayer2/state`

```yaml
mqtt:
  sensor:
    - name: MPRIS Media Player
      state_topic: dbus2mqtt/org.mpris.MediaPlayer2/state
      json_attributes_topic: dbus2mqtt/org.mpris.MediaPlayer2/state
      value_template: >-
        {% set status = value_json.PlaybackStatus %}
        {% if status == 'Playing' %}
          playing
        {% elif status == 'Paused' %}
          paused
        {% elif status == 'Stopped' %}
          idle
        {% else %}
          off
        {% endif %}

media_player:
  - platform: media_player_template
    media_players:
      mpris_media_player:
        device_class: generic
        friendly_name: MPRIS Media Player
        value_template: "{{ states('sensor.mpris_media_player') }}"

        current_volume_template: "{{ state_attr('sensor.mpris_media_player', 'Volume') }}"
        current_is_muted_template: "{{ state_attr('sensor.mpris_media_player', 'Volume') == 0 }}"
        current_position_template: "{{ state_attr('sensor.mpris_media_player', 'Position') }}"
        title_template: "{{ state_attr('sensor.mpris_media_player', 'Metadata')['xesam:title'] }}"

        media_content_type_template: music  # needed to show 'artist'
        media_duration_template: "{{ state_attr('sensor.mpris_media_player', 'Metadata')['mpris:length'] }}"
        album_template: "{{ state_attr('sensor.mpris_media_player', 'Metadata')['xesam:album'] }}"
        artist_template: "{{ state_attr('sensor.mpris_media_player', 'Metadata')['xesam:artist'] | first }}"

        # mpris:artUrl is referencing a local file when firefox is used, for now this will provide Youtube img support
        media_image_url_template: >-
          {{ state_attr('sensor.mpris_media_player', 'Metadata')['xesam:url']
            | regex_replace(
                find='https:\/\/www\\.youtube\\.com\/watch\\?v=([^&]+).*',
                replace='https://img.youtube.com/vi/\\1/maxresdefault.jpg'
              )
          }}

        turn_off:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: '{"method": "Quit"}'
        play:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: '{"method": "Play"}'
        pause:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: '{"method": "Pause"}'
        stop:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: '{"method": "Stop"}'
        next:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: '{"method": "Next"}'
        previous:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: '{"method": "Previous"}'
        seek:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: >-
              { "method": "SetPosition", "args": ["{{  state_attr('sensor.mpris_media_player', 'Metadata')['mpris:trackid'] }}", {{ position | int }}] }
        set_volume:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: '{"property": "Volume", "value": {{volume}} }'
        volume_up:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: '{"property": "Volume", "value": 0.0 }'
        volume_down:
          service: mqtt.publish
          data:
            topic: dbus2mqtt/org.mpris.MediaPlayer2/command
            payload: '{"property": "Volume", "value": 0.0 }'
```
