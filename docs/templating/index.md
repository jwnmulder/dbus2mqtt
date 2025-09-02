# Templating

**dbus2mqtt** leverages Jinja to allow formatting MQTT messages, D-Bus responses or advanced configuration use-cases. If you are not familiar with Jinja based expressions, have a look at Jinjas own [Template Designer Documentation](https://jinja.palletsprojects.com/en/stable/templates/).

Besides the filters and functions Jinja provides out of the box, the following extensions are available:

* [jinja2-ansible-filters](https://pypi.org/project/jinja2-ansible-filters/)

More documentation to be added, for now see the [Mediaplayer integration with Home Assistant](../examples/home_assistant_media_player.md) example for inspiration.

Templating is used in these areas of dbus2mqtt:

* [subscriptions](../subscriptions.md)
* [flow actions](../flows/flow_actions.md)
