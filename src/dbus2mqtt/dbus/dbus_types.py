

from dataclasses import dataclass

import dbus_fast.aio as dbus_aio

from dbus2mqtt.config import SubscriptionConfig


class BusNameSubscriptions:

    def __init__(self, bus_name: str, unique_name: str):
        self.bus_name = bus_name
        self.unique_name = unique_name
        self.path_objects: dict[str, dbus_aio.proxy_object.ProxyObject] = {}

@dataclass
class SubscribedInterface:

    # interface_config: InterfaceConfig
    subscription_config: SubscriptionConfig
    bus_name: str
    path: str
    interface_name: str
