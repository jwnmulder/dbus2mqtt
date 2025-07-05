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

    def async_dbus_list_fn(self, bus_name_pattern: str):

        res = []

        self.dbus_client.subscriptions
        for bus_name in self.dbus_client.subscriptions.keys():
            if fnmatch.fnmatchcase(bus_name, bus_name_pattern):
                res.append(bus_name)

        return res

    async def async_dbus_call_fn(self, bus_name: str, path: str, interface: str, method:str, method_args: list[Any] = []):

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
