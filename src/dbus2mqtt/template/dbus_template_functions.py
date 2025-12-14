import fnmatch
import logging

from typing import Any

from dbus_fast.constants import ErrorType
from dbus_fast.errors import DBusError

from dbus2mqtt.dbus.dbus_client import DbusClient

logger = logging.getLogger(__name__)

class DbusContext:

    def __init__(self, dbus_client: DbusClient):
        self.dbus_client = dbus_client

    def async_dbus_list_fn(self, bus_name_pattern: str) -> list[str]:
        """This function is used to access active bus_names which dbus2mqtt is subscribed to.

        Args:
            bus_name_pattern (str): Glob pattern to filter on, e.g. '*' or 'org.mpris.MediaPlayer2.*'

        Returns:
            List of matching bus names found in current subscriptions

        Example:
            Template
            ```yaml
            all_subscibed_bus_names: "{{ dbus_list('*') }}"
            subscribed_mpris_bus_names: "{{ dbus_list('org.mpris.MediaPlayer2.*') }}"
            ```

            Result
            ```yaml
            all_subscibed_bus_names: ['org.bluez', 'org.mpris.MediaPlayer2.firefox']
            subscribed_mpris_bus_names: ['org.mpris.MediaPlayer2.firefox']
            ```
        """
        res = []

        self.dbus_client.subscriptions
        for bus_name in self.dbus_client.subscriptions.keys():
            if fnmatch.fnmatchcase(bus_name, bus_name_pattern):
                res.append(bus_name)

        return res

    async def async_dbus_call_fn(self, bus_name: str, path: str, interface: str, method:str, method_args: list[Any] = []) -> object:
        """Call a method on a active dbus object that dbus2mqtt is subscribed to.

        This function looks up an active subscribed dbus object for the
        given bus name and object path and invokes the specified method on
        the given interface with the provided positional arguments.

        Args:
            bus_name: The unique bus name (e.g. "org.mpris.MediaPlayer2.firefox") on which the
                subscribed object exists.
            path: The object path (e.g. "/org/mpris/MediaPlayer2") for the subscribed
                dbus object.
            interface: The interface name (e.g. "org.freedesktop.DBus.Properties") on which to call the method.
            method: The name of the method to call on the interface.
            method_args: Positional arguments to pass to the D-Bus method. Must be a list.

        Returns:
            The result returned by the underlying D-Bus method call,

        Raises:
            ValueError: If no subscribed proxy object is found for the given bus_name and path.

        Example:
            Template
            ```yaml
            player_properties: |
              {{ dbus_call(mpris_bus_name, mpris_path, 'org.freedesktop.DBus.Properties', 'GetAll', ['org.mpris.MediaPlayer2.Player']) }}
            ```

            Result
            ```yaml
            player_properties:
                Metadata: {}
                Position: 0
                PlaybackStatus: Stopped
                Volume: 0.0
            ```

        Notes:
            - The function assumes the dbus object has been previously subscribed to. It will not create subscriptions.
            - `dbus_call` can invoke any dbus method on any interface.
              It's a powerful function that is meant for retrieving state and property values.
              Although it can be used call methods that change state,
              it's a bad practice todo so from a template rendering perspective.
        """
        if not isinstance(method_args, list):
            # Pylance will mention this line is unreachable. It is not, jinja2 can pass in any type
            raise ValueError("method_args must be a list")

        proxy_object = self.dbus_client.get_subscribed_proxy_object(bus_name, path)
        if not proxy_object:
            raise ValueError(f"No matching subscription found for bus_name: {bus_name}, path: {path}")

        obj_interface = proxy_object.get_interface(interface)

        return await self.dbus_client.call_dbus_interface_method(obj_interface, method, method_args)

    async def async_dbus_property_get_fn(self, bus_name: str, path: str, interface: str, property:str, default_unsupported: Any = None):

        proxy_object = self.dbus_client.get_subscribed_proxy_object(bus_name, path)
        if not proxy_object:
            raise ValueError(f"No matching subscription found for bus_name: {bus_name}, path: {path}")

        obj_interface = proxy_object.get_interface(interface)

        try:
            return await self.dbus_client.get_dbus_interface_property(obj_interface, property)
        except DBusError as e:
            if e.type == ErrorType.NOT_SUPPORTED.value and default_unsupported is not None:
                return default_unsupported

def jinja_custom_dbus_functions(dbus_client: DbusClient) -> dict[str, Any]:

    dbus_context = DbusContext(dbus_client)

    custom_functions: dict[str, Any] = {}
    custom_functions.update({
        "dbus_list": dbus_context.async_dbus_list_fn,
        "dbus_call": dbus_context.async_dbus_call_fn,
        "dbus_property_get": dbus_context.async_dbus_property_get_fn
    })

    return custom_functions
