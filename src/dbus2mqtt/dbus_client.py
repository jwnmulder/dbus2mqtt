import asyncio
import json
import logging

from queue import Empty

import dbus_next.aio as dbus_aio
import dbus_next.introspection as dbus_introspection

from dbus2mqtt.config import (
    DbusConfig,
    InterfaceConfig,
)
from dbus2mqtt.dbus_signal_processor import on_signal
from dbus2mqtt.dbus_types import BusNameSubscriptions
from dbus2mqtt.dbus_util import camel_to_snake, unwrap_dbus_object
from dbus2mqtt.event_broker import DbusSignalWithState, EventBroker, MqttMessage

logger = logging.getLogger(__name__)


class DbusClient:

    def __init__(self, config: DbusConfig, bus: dbus_aio.message_bus.MessageBus, event_broker: EventBroker):
        self.config = config
        self.bus = bus
        self.event_broker = event_broker
        self.subscriptions: dict[str, BusNameSubscriptions] = {}

    async def connect(self):

        if not self.bus.connected:
            await self.bus.connect()

            if self.bus.connected:
                logger.info(f"Connected to {self.bus._bus_address}")
            else:
                logger.warning(f"Failed to connect to {self.bus._bus_address}")

            introspection = await self.bus.introspect('org.freedesktop.DBus', '/org/freedesktop/DBus')
            obj = self.bus.get_proxy_object('org.freedesktop.DBus', '/org/freedesktop/DBus', introspection)
            dbus_interface = obj.get_interface('org.freedesktop.DBus')

            # subscribe to NameOwnerChanged which allows us to detect new bus_names
            dbus_interface.on_name_owner_changed(self.dbus_name_owner_changed_callback)

            # subscribe to existing registered bus_names we are interested in
            connected_bus_names = await dbus_interface.call_list_names()

            for bus_name in connected_bus_names:
                await self.handle_bus_name_added(bus_name)

    def get_proxy_object_subscription(self, bus_name: str, path: str, introspection: dbus_introspection.Node):

        bus_name_subscriptions = self.subscriptions.get(bus_name)
        if not bus_name_subscriptions:
            bus_name_subscriptions = BusNameSubscriptions(bus_name)
            self.subscriptions[bus_name] = bus_name_subscriptions

        proxy_object = bus_name_subscriptions.path_objects.get(path)
        if not proxy_object:
            proxy_object = self.bus.get_proxy_object(bus_name, path, introspection)
            bus_name_subscriptions.path_objects[path] = proxy_object

        return proxy_object, bus_name_subscriptions

    async def subscribe_interface(self, bus_name: str, path: str, introspection: dbus_introspection.Node, interface: dbus_introspection.Interface, si: InterfaceConfig):

        proxy_object, bus_name_subscriptions = self.get_proxy_object_subscription(bus_name, path, introspection)
        obj_interface = proxy_object.get_interface(interface.name)

        interface_signals = dict((s.name, s) for s in interface.signals)

        logger.debug(f"subscribe: bus_name={bus_name}, path={path}, interface={interface.name}, proxy_interface: signals={list(interface_signals.keys())}")

        for [signal_name, signal_handler_configs] in si.signal_handlers_by_signal().items():
            interface_signal = interface_signals.get(signal_name)
            if interface_signal:

                on_signal_method_name = "on_" + camel_to_snake(signal_name)
                obj_interface.__getattribute__(on_signal_method_name)(
                    lambda a, b, c:
                        self.event_broker.on_dbus_signal(DbusSignalWithState(
                            bus_name_subscriptions, path, interface.name, signal_handler_configs, args=[a, b, c]
                        ))
                )
                logger.info(f"subscribed with signal_handler: signal={signal_name}, bus_name={bus_name}, path={path}, interface={interface.name}")

            else:
                logger.warning(f"Invalid signal: signal={signal_name}, bus_name={bus_name}, path={path}, interface={interface.name}")


    async def process_interface(self, bus_name: str, path: str, introspection: dbus_introspection.Node, interface: dbus_introspection.Interface):

        logger.debug(f"process_interface: {bus_name}, {path}, {interface.name}")
        subscription_configs = self.config.get_subscription_configs(bus_name, path)
        for subscription in subscription_configs:
            logger.debug(f"processing subscription config: {subscription.bus_name}, {subscription.path}")
            for subscription_interface in subscription.interfaces:
                if subscription_interface.interface == interface.name:
                    logger.debug(f"matching config found for bus_name={bus_name}, path={path}, interface={interface.name}")
                    await self.subscribe_interface(bus_name, path, introspection, interface, subscription_interface)

    async def visit_bus_name_path(self, bus_name: str, path: str):

        introspection = await self.bus.introspect(bus_name, path)

        if len(introspection.nodes) == 0:
            logger.debug(f"leaf node: bus_name={bus_name}, path={path}, is_root={introspection.is_root}, interfaces={[i.name for i in introspection.interfaces]}")

        for interface in introspection.interfaces:
            await self.process_interface(bus_name, path, introspection, interface)

        for node in introspection.nodes:
            path_seperator = "" if path.endswith('/') else "/"
            await self.visit_bus_name_path(bus_name, f"{path}{path_seperator}{node.name}")

    async def handle_bus_name_added(self, bus_name: str):

        if not self.config.is_bus_name_configured(bus_name):
            return

        # sanity checks
        for umh in self.bus._user_message_handlers:
            umh_bus_name = umh.__self__.bus_name
                # umh_bus_name = umh.__self__.bus_name
            if umh_bus_name == bus_name:
                logger.warning(f"handle_bus_name_added: {umh_bus_name} already added")

        await self.visit_bus_name_path(bus_name, "/")

    async def handle_bus_name_removed(self, bus_name: str):

        bus_name_subscriptions = self.subscriptions.get(bus_name)

        if bus_name_subscriptions:
            for proxy_object in bus_name_subscriptions.path_objects.values():
                for interface in proxy_object._interfaces.values():
                    proxy_interface: dbus_aio.proxy_object.ProxyInterface = interface

                    # officially you should do 'off_...' but the below is easier
                    # proxy_interface.off_properties_changed(self.on_properties_changed)

                    # clean lingering interface matchrule from bus
                    if proxy_interface._signal_match_rule in self.bus._match_rules.keys():
                        self.bus._remove_match_rule(proxy_interface._signal_match_rule)

                    # clean lingering interface messgage handler from bus
                    self.bus.remove_message_handler(proxy_interface._message_handler)

            del self.subscriptions[bus_name]

    async def dbus_name_owner_changed_callback(self, name, old_owner, new_owner):

        logger.debug(f'NameOwnerChanged: name=q{name}, old_owner={old_owner}, new_owner={new_owner}')

        if new_owner and not old_owner:
            logger.debug(f'NameOwnerChanged.new: name={name}')
            await self.handle_bus_name_added(name)
        if old_owner and not new_owner:
            logger.debug(f'NameOwnerChanged.old: name={name}')
            await self.handle_bus_name_removed(name)

    async def call_dbus_interface_method(self, interface: dbus_aio.proxy_object.ProxyInterface, method: str, method_args: list):

        call_method_name = "call_" + camel_to_snake(method)
        res = await interface.__getattribute__(call_method_name)(*method_args)

        if res:
            res = unwrap_dbus_object(res)

        logger.info(f"call_dbus_interface_method: bus_name={interface.bus_name}, interface={interface.introspection.name}, method={method}, res={res}")

        return res

    async def mqtt_receive_queue_processor_task(self):
        """Continuously processes messages from the async queue."""
        while True:
            msg = await self.event_broker.mqtt_receive_queue.async_q.get()  # Wait for a message
            try:
                await self.on_mqtt_msg(msg)
            except Exception as e:
                logger.warning(f"mqtt_receive_queue_processor_task: Exception {e}", exc_info=True)
            finally:
                self.event_broker.mqtt_receive_queue.async_q.task_done()

    async def dbus_signal_queue_processor_task(self):
        """Continuously processes messages from the async queue."""
        while True:
            signal = await self.event_broker.dbus_signal_queue.async_q.get()  # Wait for a message
            try:
                await on_signal(
                    self.event_broker,
                    signal.bus_name_subscriptions,
                    signal.path,
                    signal.interface_name,
                    signal.signal_handler_configs,
                    signal.args
                )
            except Exception as e:
                logger.warning(f"dbus_signal_queue_processor_task: Exception {e}", exc_info=True)
            finally:
                self.event_broker.dbus_signal_queue.async_q.task_done()


    async def on_mqtt_msg(self, msg: MqttMessage):
        # self.queue.put({
        #     "topic": topic,
        #     "payload": payload
        # })

        found_matching_topic = False
        for subscription_configs in self.config.subscriptions:
            for interface_config in subscription_configs.interfaces:
                # TODO, performance improvement
                mqtt_topic = interface_config.render_mqtt_call_method_topic({})
                found_matching_topic |= mqtt_topic == msg.topic

        if not found_matching_topic:
            return

        logger.debug(f"on_mqtt_msg: topic={msg.topic}, payload={json.dumps(msg.payload)}")
        calls_done: list[str] = []

        payload_method = msg.payload["method"]
        payload_method_args = msg.payload.get("args") or []

        for [bus_name, bus_name_subscription] in self.subscriptions.items():
            for [path, proxy_object] in bus_name_subscription.path_objects.items():
                for subscription_configs in self.config.get_subscription_configs(bus_name=bus_name, path=path):
                    for interface_config in subscription_configs.interfaces:

                        for method in interface_config.methods:

                            # filter configured method, configured topic, ...
                            if method.method == payload_method:
                                interface = proxy_object.get_interface(name=interface_config.interface)

                                await self.call_dbus_interface_method(interface, method.method, payload_method_args)
                                calls_done.append(method.method)

        if len(calls_done) == 0:
            logger.info(f"No configured or active dbus subscriptions for topic={msg.topic}, method={payload_method}, active bus_names={list(self.subscriptions.keys())}")

        # raw mode, payload contains: bus_name (specific or wildcard), path, interface_name
        # topic: dbus2mqtt/raw (with allowlist check)

        # predefined mode with topic matching from configuration
        # topic: dbus2mqtt/MediaPlayer/command

    async def consume_mqtt_messages(self):
        self.log.info("Starting consumer for OpenHAB MQTT messages ...")
        while not self.stopped:
            try:
                (client, userdata, message) = self.queue.get(block=False)
                await self.async_handle_openhab_mqtt_message(client, userdata, message)
            except Empty:
                await asyncio.sleep(1)
                continue
