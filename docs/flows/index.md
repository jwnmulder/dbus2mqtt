# Flows

**dbus2mqtt** allows you to add additional processing logic (flows) for when events occur. Configuration is done in yaml and a complete example can be found in [home_assistant_media_player.yaml](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples/home_assistant_media_player.yaml) which is part of the [MPRIS to Home Assistant Media Player integration](../examples/home_assistant_media_player.md) example

Flows can be defined on a global or dbus subscription level and can be triggered by any of the following events:

* `schedule` for cron based schedules
* `dbus_signal` for when dbus signal occur
* `object_added` when a new bus_name is registered on dbus
* `object_removed` when a bus_name is removed from dbus

Within each flow a set of actions can be configured. These are executed in the order as defined in yaml

* `log` for logging message
* `context_set` to set variables
* `mqtt_publish` to publish a mqtt message

An example

```yaml
flows:
  - name: "Example flow"
    triggers:
      - type: schedule
        interval: {seconds: 5}
    actions:
      - type: log
        msg: hello from example flow
```

Some action parameters allow the use of jinja2 templating. dbus2mqtt supports both builtin jinja2 filters and comes with additional filters from [jinja2-ansible-filters](https://pypi.org/project/jinja2-ansible-filters/). When supported, it is documented below.

Next: [flow actions](flow_actions.md) & [flow triggers](flow_triggers.md)
