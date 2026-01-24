# Templating

**dbus2mqtt** leverages Jinja to allow formatting of MQTT messages, D-Bus responses and other configuration aspects of `dbus2mqtt`. If you are not familiar with Jinja based expressions, have a look at Jinjas own [Template Designer Documentation](https://jinja.palletsprojects.com/en/stable/templates/).

Templating is used in these areas of dbus2mqtt:

* [subscriptions](../subscriptions.md)
* [flow actions](../flows/flow_actions.md)

Besides the filters and functions that Jinja provides out of the box, additional extensions are available.

All filters from [jinja2-ansible-filters](https://pypi.org/project/jinja2-ansible-filters/) are included as well as the following global functions, variables and filters:

| Name                | Type      | Description                                                                 |
|---------------------|-----------|-----------------------------------------------------------------------------|
| `dbus2mqtt.version` | `str`     | The current version of the `dbus2mqtt` package.                             |
| `now`               | function  | Returns the current date and time as a `datetime` object.                   |
| `urldecode`         | function  | Decodes a URL-encoded string.                                               |
| `dbus_list`         | function  | Returns a list of active subscribed bus_names, documentation below          |
| `dbus_call`         | function  | D-Bus method invocation, documentation below                                |
| `dbus_property_get` | function  | |

## now()

::: dbus2mqtt.template.templating.now
    options:
      show_root_toc_entry: false
      show_docstring_raises: false

## urldecode()

::: dbus2mqtt.template.templating.urldecode
    options:
      show_root_toc_entry: false
      show_docstring_raises: false

## dbus_list()

::: dbus2mqtt.template.dbus_template_functions.DbusTemplateFunctionsContext.dbus_list_fn
    options:
      show_root_toc_entry: false
      show_docstring_raises: false

## dbus_contexts  ()

::: dbus2mqtt.template.dbus_template_functions.DbusTemplateFunctionsContext.dbus_contexts_fn
    options:
      show_root_toc_entry: false
      show_docstring_raises: false

## dbus_call()

::: dbus2mqtt.template.dbus_template_functions.DbusTemplateFunctionsContext.async_dbus_call_fn
    options:
      show_root_toc_entry: false
      show_docstring_raises: false

## dbus_property_get()

::: dbus2mqtt.template.dbus_template_functions.DbusTemplateFunctionsContext.async_dbus_property_get_fn
    options:
      show_root_toc_entry: false
      show_docstring_raises: false
