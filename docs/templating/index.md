# Templating

**dbus2mqtt** leverages Jinja to allow formatting MQTT messages, D-Bus responses or advanced configuration use-cases. If you are not familiar with Jinja based expressions, have a look at Jinjas own [Template Designer Documentation](https://jinja.palletsprojects.com/en/stable/templates/).

Templating is used in these areas of dbus2mqtt:

* [subscriptions](../subscriptions.md)
* [flow actions](../flows/flow_actions.md)

Besides the filters and functions Jinja provides out of the box, additional extensions are available.

All filters from [jinja2-ansible-filters](https://pypi.org/project/jinja2-ansible-filters/) are included as well as the following global functions, variables and filters:

| Name                | Type      | Description                                                                 |
|---------------------|-----------|-----------------------------------------------------------------------------|
| `now`               | function  | Returns the current date and time as a `datetime` object.                   |
| `urldecode`         | function  | Decodes a URL-encoded string.                                               |
| `dbus2mqtt.version` | string    | The current version of the `dbus2mqtt` package.                             |
| `dbus_list`         | function  | Returns a list of active subscribed bus_names, documentation below          |
| `dbus_call`         | function  | D-Bus method invocation, documentation below                                |

## dbus_list()

The `dbus_list` function is used in templates to access active bus_names which `dbus2mqtt` is subscribed to.

It's signature is `dbus_list(bus_name_pattern)` -> `list[str]`

| argument         | type | description  |
|------------------|------|--------------|
| bus_name_pattern | str  | Glob pattern to filter on, e.g. `*` or `org.mpris.MediaPlayer2.* |

Examples

```yaml
all_subscibed_bus_names: "{{ dbus_list('*') }}"
subscribed_mpris_bus_names: "{{ dbus_list('org.mpris.MediaPlayer2.*') }}"
```

## dbus_call()

The `dbus_call` function is used to call D-Bus methods.

It's signature is `dbus_call(bus_name_pattern)` -> `object`

| argument         | type | description  |
|------------------|------|--------------|
| `bus_name`         | str  |  |
| `path`             | str  |  |
| `interface`        | str  |  |
| `method`           | str  |  |
| `method_args`      | list[Any] |  |

Examples

```yaml
player_properties: |
  {{ dbus_call(mpris_bus_name, mpris_path, 'org.freedesktop.DBus.Properties', 'GetAll', ['org.mpris.MediaPlayer2.Player']) }}
```

!!! note
    `dbus_call` can invoke any dbus method on any interface. It's a powerful function that is meant for retrieving state and property values. Although it can be used call methods that change state, it's a bad practice todo so from a template rendering perspective.
