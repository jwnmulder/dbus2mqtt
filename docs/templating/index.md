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

More documentation to be added, for now see the [Mediaplayer integration with Home Assistant](../examples/home_assistant_media_player.md) example for inspiration.
