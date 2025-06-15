# Flows

**dbus2mqtt** allows you to add additional processing logic (flows) for when events occur. Configuration is best done in yaml and a complete example can be found here: [MPRIS to Home Assistant Media Player integration](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples/home_assistant_media_player.md)

Flows can be defined on a global or dbus subscription level and can be triggered by any of the following events:

* `schedule` for cron based schedules
* `dbus_signal` for when dbus signal occur
* `object_added` when a new bus_name is registered on dbus
* `object_removed` when a bus_name is removed from dbus

Within each flow a set of actions can be configured. These are executed in order

* `context_set` to set variables
* `mqtt_publish` to publish a mqtt message

Actions support string templating which is based on jinja2

## Flow triggers

### schedule

```yaml
type: schedule
cron: {second: 5}
interval: {seconds: 5}
```

Schedule based triggers can be configured by setting either a cron or interval parameter. Scheduling is based on the   APScheduler library and allows the following configuration options

| key | description  |
|------|-------------|
| interval | dict of time units and intervals, see <https://apscheduler.readthedocs.io/en/3.x/modules/triggers/interval.html>    |
| cron     | dict of time units and cron expressions, see <https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html> |

When triggered, the following context parameters are available

| name | description |
|------|-------------|
| N/A  | N/A         |

### dbus_signal

DBus signals triggers must be configured with an anterface and path. Note that only subscribed signals can be configured as a trigger.

| key | description  |
|------|-------------|
| interface | interface to filter on, e.g. 'org.freedesktop.DBus.Properties' |
| signal    | signal name to filter on, e.g. PropertiesChanged |

When triggered, the following context parameters are available

| name | type | description |
|------|------|-------------|
| bus_name  | string | bus_name of the object that was registered on dbus |
| path      | string | bus_name path of the object that was registered on dbus |
| interface | string | name of interface for which the signal was triggered |
| args      | list   | signal arguments, list of objects |

### object_added

```yaml
type: object_added
```

When triggered, the following context parameters are available

| name | description |
|------|-------------|
| bus_name | bus_name of the object that was registered on dbus |
| path     | bus_name path of the object that was registered on dbus |

### object_removed

```yaml
type: object_removed
```

When triggered, the following context parameters are available

| name | description |
|------|-------------|
| bus_name | bus_name of the object that was registered on dbus |
| path     | bus_name path of the object that was registered on dbus |

## Flow actions

### context_set

```yaml
type: context_set
context: {}
dbus_object_context: {}
global_context: {}
```

| key                 | type             | description  |
|---------------------|------------------|--------------|
| context             | dict | Per flow execution context. Value can be a dict of strings or dict of templated strings |
| dbus_object_context | dict | Per dbus object context, shared between multiple flow executions. Value can be a dict of strings or dict of templated strings |
| global_context      | dict | Global context, shared between multiple flow executions, over all subscriptions. Value can be a dict of strings or dict of templated strings |



### mqtt_publish

```yaml
type: mqtt_publish
topic: dbus2mqtt/org.mpris.MediaPlayer2/state
payload_type: json
payload_template: {PlaybackStatus: "Off"}
```

| key              | type             | description  |
|------------------|------------------|-------------|
| topic            | string | mqtt topic the messaage is published to |
| payload_type     | string | any of [json, yaml, text], defaults to json, format the message is published in to mqtt |
| payload_template | string, dict | value can be a string, a dict of strings, a templated string or a nested dict of templated strings |

## Jinja2 based templating

Some configuration values allow the use of jinja 2 templating. dbus2mqtt supports both the builtin filters and comes with additional filters from [jinja2-ansible-filters](https://pypi.org/project/jinja2-ansible-filters/)
