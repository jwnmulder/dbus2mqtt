

from dataclasses import dataclass
from typing import Any

import dbus_next.aio as dbus_aio

from dbus2mqtt.config import InterfaceConfig, SubscriptionConfig


class BusNameSubscriptions:

    def __init__(self, bus_name: str):
        self.bus_name = bus_name
        self.path_objects: dict[str, dbus_aio.proxy_object.ProxyObject] = {}
        self.dbus_object_context: dict[str, Any] = {}
        """Mutable context for each dbus object"""

@dataclass
class SubscribedInterface:

    interface_config: InterfaceConfig
    subscription_config: SubscriptionConfig
    bus_name: str
    path: str
    interface_name: str
