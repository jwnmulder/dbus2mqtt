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
| `dbus_list`         | function  | Returns a list of active subscribed dbus_names matching the given pattern. Function arguments:<ul><li>bus_name_pattern</li></ul>Examples:<ul><li>`dbus_list('*')` -> `['org.mpris.MediaPlayer2.vlc', 'org.bluez']`</li><li>`dbus_list('org.mpris.MediaPlayer2.*')` -> `['org.mpris.MediaPlayer2.vlc']`</li></ul> |
| `dbus_call`         | function  | D-Bus method invocation. Function arguments:<ul><li>bus_name</li><li>path</li><li>interface</li><li>method</li><li>method_args</li></ul>Examples:<ul><li>`dbus_call('org.mpris.MediaPlayer2.firefox', '/org/mpris/MediaPlayer2', 'org.freedesktop.DBus.Properties', 'GetAll', ['org.mpris.MediaPlayer2.Player'])`</li></ul> |

More documentation to be added, for now see the [Mediaplayer integration with Home Assistant](../examples/home_assistant_media_player.md) example for inspiration.
