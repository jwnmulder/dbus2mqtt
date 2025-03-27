import asyncio
import fnmatch
import json
import logging
import re

import dbus_next.aio as dbus_aio
import dbus_next.introspection as dbus_introspection
import dbus_next.signature as dbus_signature

from dbus2mqtt.config import (
    DbusConfig,
    InterfaceConfig,
    SignalConfig,
    SubscriptionConfig,
)
from dbus2mqtt.handler import DbusSignalHandler

# from dbus_next.aio.proxy_object import ProxyObject as DbusProxyObject
# from dbus_next.introspection import Interface as DbusInterface

logger = logging.getLogger(__name__)

class BusNameSubscriptions:
    bus_name: str
    signal_handler: DbusSignalHandler
    path_objects: dict[str, dbus_aio.proxy_object.ProxyObject] = {}

def variant_serializer(obj):
    if isinstance(obj, dbus_signature.Variant):
        return obj.value
    return obj

def unwrap_dbus_object(o):
    # an easy way to get rid of dbus_next.signature.Variant types
    res = json.dumps(o, default=variant_serializer)
    json_obj = json.loads(res)
    return json_obj

async def on_signal(bus_name_subscriptions: BusNameSubscriptions, path, interface_name, signal: SignalConfig, *args):

    bus_name = bus_name_subscriptions.bus_name
    proxy_object = bus_name_subscriptions.path_objects[path]
    signal_handler = bus_name_subscriptions.signal_handler

    unwrapped_args = [unwrap_dbus_object(o) for o in args]

    matches_filter = signal.matches_filter(*args)
    if matches_filter:

        payload = signal.render_payload_template(*unwrapped_args)
        logger.info(f"name={signal.signal}, msg=\n{payload}")

        properties = proxy_object.get_interface("org.freedesktop.DBus.Properties")

        msg = {}
        msg["mediaplayer2_properties"] = unwrap_dbus_object(await properties.call_get_all("org.mpris.MediaPlayer2"))
        msg["mediaplayer2_player_properties"] = unwrap_dbus_object(await properties.call_get_all("org.mpris.MediaPlayer2.Player"))
        msg.update(payload)

        logger.debug(f"on_signal: {bus_name}, {path}, {interface_name}, {msg}")
        signal_handler.on_dbus_signal(bus_name, path, interface_name, signal.signal, msg)

# INFO:dbus2mqtt.dbus_client:subscribed signal: bus_name=org.mpris.MediaPlayer2.vlc, path=/org/mpris/MediaPlayer2, interface=org.freedesktop.DBus.Properties, signal=PropertiesChanged


class DbusClient:

    def __init__(self, config: DbusConfig, bus: dbus_aio.message_bus.MessageBus, signal_handler: DbusSignalHandler):
        self.config = config
        self.bus = bus
        self.subscriptions: dict[str, BusNameSubscriptions] = {}
        self.signal_handler = signal_handler

    async def connect(self):

        if not self.bus.connected:
            # self.proxies.clear()
            await self.bus.connect()

            if self.bus.connected:
                logger.info(f"Connected to {self.bus._bus_address}")
            else:
                logger.warning(f"Failed to connect to {self.bus._bus_address}")

            introspection = await self.bus.introspect('org.freedesktop.DBus', '/org/freedesktop/DBus')
            obj = self.bus.get_proxy_object('org.freedesktop.DBus', '/org/freedesktop/DBus', introspection)
            properties = obj.get_interface('org.freedesktop.DBus')

            # def message_handler(msg: dbus_message.Message):
            #     logger.info(f"message_handler: body=, {msg.interface}, {msg.destination}, {msg.message_type}, {msg.path}")
                # if msg.interface == 'com.test.interface' and msg.member == 'MyMember':
                    # return dbus_message.Message.new_method_return(msg, 's', ['got it'])

            # self.bus.add_message_handler(message_handler)

            # for signal in interface.signals:
            properties.on_name_owner_changed(self.dbus_name_owner_changed_callback)

    def get_proxy_object_subscription(self, bus_name: str, path: str, introspection: dbus_introspection.Node):

        bus_name_subscriptions = self.subscriptions.get(bus_name)
        if not bus_name_subscriptions:
            bus_name_subscriptions = BusNameSubscriptions()
            bus_name_subscriptions.bus_name = bus_name
            bus_name_subscriptions.signal_handler = self.signal_handler
            self.subscriptions[bus_name] = bus_name_subscriptions

        proxy_object = bus_name_subscriptions.path_objects.get(path)
        if not proxy_object:
            proxy_object = self.bus.get_proxy_object(bus_name, path, introspection)
            bus_name_subscriptions.path_objects[path] = proxy_object

        return proxy_object, bus_name_subscriptions

    def is_bus_name_configured(self, bus_name: str) -> bool:

        for subscription in self.config.subscriptions:
            if fnmatch.fnmatchcase(bus_name, subscription.bus_name):
                return True

        return False

    def get_subscription(self, bus_name: str, path: str) -> SubscriptionConfig | None:
        for subscription in self.config.subscriptions:
            if fnmatch.fnmatchcase(bus_name, subscription.bus_name) and fnmatch.fnmatchcase(path, subscription.path):
                return subscription


    @staticmethod
    def camel_to_snake(name):
        return re.sub(r'([a-z])([A-Z])', r'\1_\2', name).lower()

    async def subscribe_interface(self, bus_name: str, path: str, introspection: dbus_introspection.Node, interface: dbus_introspection.Interface, si: InterfaceConfig):

        proxy_object, bus_name_subscriptions = self.get_proxy_object_subscription(bus_name, path, introspection)
        obj_interface = proxy_object.get_interface(interface.name)

        interface_signals = dict((s.name, s) for s in interface.signals)

        logger.debug(f"subscribe: bus_name={bus_name}, path={path}, interface={interface.name}, proxy_interface: signals={list(interface_signals.keys())}")

        for signal in si.signals:
            interface_signal = interface_signals.get(signal.signal)
            if interface_signal:
                logger.info(f"subscribed on_signal: bus_name={bus_name}, path={path}, interface={interface.name}, signal={signal.signal}")

                on_signal_method_name = "on_" + self.camel_to_snake(signal.signal)
                obj_interface.__getattribute__(on_signal_method_name)(
                    lambda a, b, c:
                        asyncio.gather(
                            on_signal(bus_name_subscriptions, path, interface.name, signal, a, b, c)
                        )
                )

            else:
                logger.warning(f"Invalid signal: bus_name={bus_name}, path={path}, interface={interface.name}, signal={signal.signal}")


    async def process_interface(self, bus_name: str, path: str, introspection: dbus_introspection.Node, interface: dbus_introspection.Interface):

        # logger.debug(f"process_interface: {bus_name}, {path}, {interface}")
        subscription = self.get_subscription(bus_name, path)
        if subscription:
            logger.debug(f"subscription: {subscription.bus_name}, {subscription.path}")
            for subscription_interface in subscription.interfaces:
                if subscription_interface.interface == interface.name:
                    logger.debug(f"matching config found for bus_name={bus_name}, path={path}, interface={interface.name}")
                    await self.subscribe_interface(bus_name, path, introspection, interface, subscription_interface)

    async def visit_bus_name_path(self, bus_name: str, path: str):

        introspection = await self.bus.introspect(bus_name, path)

        if len(introspection.nodes) == 0:
            logger.info(f"leaf node: bus_name={bus_name}, path={path}, is_root={introspection.is_root}, interfaces={[i.name for i in introspection.interfaces]}")

        for interface in introspection.interfaces:
            await self.process_interface(bus_name, path, introspection, interface)

        for node in introspection.nodes:
            path_seperator = "" if path.endswith('/') else "/"
            await self.visit_bus_name_path(bus_name, f"{path}{path_seperator}{node.name}")

    async def handle_bus_name_added(self, bus_name: str):

        if not self.is_bus_name_configured(bus_name):
            return

        await self.visit_bus_name_path(bus_name, "/")

    async def handle_bus_name_removed(self, bus_name: str):

        proxy_object_state = self.subscriptions.get(bus_name)

        if proxy_object_state:
        #     # stop listening for events
        #     properties = obj.get_interface('org.freedesktop.DBus.Properties')
        #     properties.off_properties_changed(self.on_properties_changed)
            del self.subscriptions[bus_name]

    async def dbus_name_owner_changed_callback(self, name, old_owner, new_owner):

        logger.debug(f'NameOwnerChanged: name=q{name}, old_owner={old_owner}, new_owner={new_owner}')

        if new_owner and not old_owner:
            logger.debug(f'NameOwnerChanged-ADDED: name={name}')
            await self.handle_bus_name_added(name)
        if old_owner and not new_owner:
            logger.debug(f'NameOwnerChanged-REMOVED: name={name}')
            await self.handle_bus_name_removed(name)

    def _unwrap(self, obj):
        if isinstance(obj, dbus_signature.Variant):
            logger.warn("XXXXXX")
            return obj.value
        return obj

