

from dataclasses import dataclass
from typing import Any

import dbus_fast.aio as dbus_aio

from dbus2mqtt.config import (
    SignalConfig,
    SubscriptionConfig,
)


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

@dataclass
class DbusSignalWithState:
    bus_name: str
    path: str
    interface_name: str
    subscription_config: SubscriptionConfig
    signal_config: SignalConfig
    args: list[Any]
