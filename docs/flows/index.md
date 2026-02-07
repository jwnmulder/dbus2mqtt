# Flows

**dbus2mqtt** allows you to add additional processing logic (flows) for when events occur. Configuration is done in yaml and a complete example can be found in [home_assistant_media_player.yaml](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples/home_assistant_media_player.yaml) which is part of the [MPRIS to Home Assistant Media Player integration](../examples/home_assistant_media_player.md) example

Flows can be defined on a global or dbus subscription level and can be triggered by any of the following events:

* `schedule` for cron based schedules
* `dbus_signal` for when dbus signal occur
* `object_added` when a new bus_name is registered on dbus
* `object_removed` when a bus_name is removed from dbus
* `mqtt_message` for reacting to MQTT messages

Within each flow a set of actions can be configured. These are executed in the order as defined in yaml

* `log` for logging message
* `context_set` to set variables
* `mqtt_publish` to publish a MQTT message

Global flows are started even when dbus2mqtt is not subscribed to any dbus objects. An example for global flows:

```yaml title="Global flow"
flows:
  - name: Example flow
    triggers:
      - type: schedule
        interval: {seconds: 5}
    actions:
      - type: log
        msg: hello from example flow
```

Subscription based flows are started when dbus2mqtt is subscribed to one or more dbus objects. No matter the number of dbus objects subscribed, there is at most one flow instance running.

```yaml title="Subscription based flows"
dbus:
  subscriptions:
    - bus_name: org.mpris.MediaPlayer2.*
      path: /org/mpris/MediaPlayer2
      flows:
        - name: Example flow
          triggers:
            - type: schedule
              interval: {seconds: 5}
          actions:
            - type: log
              msg: hello from example flow
```

Some action parameters allow the use of templating. When supported, it is documented for each individual trigger and action. See [templating](../templating/index.md) for further templating details.

## Contional flows

Flow actions can be conditionally executed. The `conditions` parameter accepts either a templated string or list of strings.
When using a list of templated strings, all expressions must evaluate to `True` for actions to be executed.

```yaml title="Subscription based flows"
dbus:
  subscriptions:
    - bus_name: org.mpris.MediaPlayer2.*
      path: /org/mpris/MediaPlayer2
      flows:
        - name: Example conditional flow
          triggers:
            - type: dbus_object_added
          conditions:
            - "{{ 'vlc' in bus_name }}"
          actions:
            - type: log
              msg: VLC player registered
```

## Flow state

Flows have three state contexts to store variables.

* `context` - per execution context
* `global_context` - stateful context, shared over all flows and all dbus_objects
* `object_context` - per dbus_object stateful context, shared over all flows, not shared with other dbus_objects

As `object_context` cannot automatically be determined for non-dbus triggers like `schedule`, flows have a `object_context_ref` configuration options which allows one to select the active object_context depending on certain scenarios.

An example of using `object_context` and `object_context_ref` is shown below.

```yaml title="Subscription based flows using object_context_ref"
dbus:
  subscriptions:
    - bus_name: org.mpris.MediaPlayer2.*
      path: /org/mpris/MediaPlayer2
      flows:
        - name: player added
          triggers:
            - type: dbus_object_added
          actions:
            - type: context_set
              global_context:
                active_player_bus_name: "{{ bus_name }}"
              object_context:
                player: "{{ dbus_call(bus_name, path, 'org.freedesktop.DBus.Properties', 'GetAll', ['org.mpris.MediaPlayer2']) }}"
        - name: print current player identity
          triggers:
            - type: context_changed
            - type: schedule
              interval: {seconds: 5}
          object_context_ref: "dbus:{{ active_player_bus_name }}:/org/mpris/MediaPlayer2"
          actions:
            - type: log
              msg: "Active player: {{ player.Identity }} ({{ active_player_bus_name | replace('org.mpris.MediaPlayer2.', '') }})"
```

Next: [flow actions](flow_actions.md) & [flow triggers](flow_triggers.md)
