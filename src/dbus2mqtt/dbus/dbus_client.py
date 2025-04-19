import json
import logging
import re

from datetime import datetime
from typing import Any

import dbus_next
import dbus_next.aio as dbus_aio
import dbus_next.introspection as dbus_introspection

from dbus2mqtt import AppContext
from dbus2mqtt.config import InterfaceConfig, SubscriptionConfig
from dbus2mqtt.dbus.dbus_types import BusNameSubscriptions, SubscribedInterface
from dbus2mqtt.dbus.dbus_util import (
    camel_to_snake,
    unwrap_dbus_object,
    unwrap_dbus_objects,
)
from dbus2mqtt.event_broker import DbusSignalWithState, MqttMessage
from dbus2mqtt.flow.flow_processor import FlowScheduler, FlowTriggerMessage

logger = logging.getLogger(__name__)

# dbus_next path to support https://docs.flatpak.org/en/latest/portal-api-reference.html
# Although not correct, flatpak exposes properties with names containing '-'
# This is failing assertions in dbus_next
# original: r'^[A-Za-z_][A-Za-z0-9_]*$'
# patched:  r'^[A-Za-z_][A-Za-z0-9_-]*$'
dbus_next.validators._element_re = re.compile(r'^[A-Za-z_][A-Za-z0-9_-]*$')

class DbusClient:

    def __init__(self, app_context: AppContext, bus: dbus_aio.message_bus.MessageBus, flow_scheduler: FlowScheduler):
        self.app_context = app_context
        self.config = app_context.config.dbus
        self.event_broker = app_context.event_broker
        self.templating = app_context.templating
        self.bus = bus
        self.flow_scheduler = flow_scheduler
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
            dbus_interface.__getattribute__("on_name_owner_changed")(self._dbus_name_owner_changed_callback)

            # subscribe to existing registered bus_names we are interested in
            connected_bus_names = await dbus_interface.__getattribute__("call_list_names")()

            new_subscriped_interfaces: list[SubscribedInterface] = []
            for bus_name in connected_bus_names:
                new_subscriped_interfaces.extend(await self._handle_bus_name_added(bus_name))

            logger.info(f"subscriptions on startup: {list(set([si.bus_name for si in new_subscriped_interfaces]))}")

    def get_proxy_object(self, bus_name: str, path: str) -> dbus_aio.proxy_object.ProxyObject | None:

        bus_name_subscriptions = self.subscriptions.get(bus_name)
        if bus_name_subscriptions:
            proxy_object = bus_name_subscriptions.path_objects.get(path)
            if proxy_object:
                return proxy_object

        return None

    def _ensure_proxy_object_subscription(self, bus_name: str, path: str, introspection: dbus_introspection.Node):

        bus_name_subscriptions = self.subscriptions.get(bus_name)
        if not bus_name_subscriptions:
            bus_name_subscriptions = BusNameSubscriptions(bus_name)
            self.subscriptions[bus_name] = bus_name_subscriptions

        proxy_object = bus_name_subscriptions.path_objects.get(path)
        if not proxy_object:
            proxy_object = self.bus.get_proxy_object(bus_name, path, introspection)
            bus_name_subscriptions.path_objects[path] = proxy_object

        return proxy_object, bus_name_subscriptions

    def _dbus_next_signal_publisher(self, dbus_signal_state: dict[str, Any], *args):
        unwrapped_args = unwrap_dbus_objects(args)
        self.event_broker.on_dbus_signal(
            DbusSignalWithState(**dbus_signal_state, args=unwrapped_args)
        )

    def _dbus_next_signal_handler(self, signal: dbus_introspection.Signal, state: dict[str, Any]) -> Any:
        expected_args = len(signal.args)

        if expected_args == 1:
            return lambda a: self._dbus_next_signal_publisher(state, a)
        elif expected_args == 2:
            return lambda a, b: self._dbus_next_signal_publisher(state, a, b)
        elif expected_args == 3:
            return lambda a, b, c: self._dbus_next_signal_publisher(state, a, b, c)
        elif expected_args == 4:
            return lambda a, b, c, d: self._dbus_next_signal_publisher(state, a, b, c, d)
        raise ValueError("Unsupported nr of arguments")

    async def _subscribe_interface(self, bus_name: str, path: str, introspection: dbus_introspection.Node, interface: dbus_introspection.Interface, subscription_config: SubscriptionConfig, si: InterfaceConfig) -> SubscribedInterface:

        proxy_object, bus_name_subscriptions = self._ensure_proxy_object_subscription(bus_name, path, introspection)
        obj_interface = proxy_object.get_interface(interface.name)

        interface_signals = dict((s.name, s) for s in interface.signals)

        logger.debug(f"subscribe: bus_name={bus_name}, path={path}, interface={interface.name}, proxy_interface: signals={list(interface_signals.keys())}")

        for signal_config in si.signals:
            interface_signal = interface_signals.get(signal_config.signal)
            if interface_signal:

                on_signal_method_name = "on_" + camel_to_snake(signal_config.signal)
                dbus_signal_state = {
                    "bus_name": bus_name,
                    "path": path,
                    "interface_name": interface.name,
                    "subscription_config": subscription_config,
                    "signal_config": signal_config,
                }

                handler = self._dbus_next_signal_handler(interface_signal, dbus_signal_state)
                obj_interface.__getattribute__(on_signal_method_name)(handler)
                logger.info(f"subscribed with signal_handler: signal={signal_config.signal}, bus_name={bus_name}, path={path}, interface={interface.name}")

            else:
                logger.warning(f"Invalid signal: signal={signal_config.signal}, bus_name={bus_name}, path={path}, interface={interface.name}")

        return SubscribedInterface(
            bus_name=bus_name,
            path=path,
            interface_name=interface.name,
            subscription_config=subscription_config,
            interface_config=si
        )

    async def _process_interface(self, bus_name: str, path: str, introspection: dbus_introspection.Node, interface: dbus_introspection.Interface) -> list[SubscribedInterface]:

        logger.debug(f"process_interface: {bus_name}, {path}, {interface.name}")
        subscription_configs = self.config.get_subscription_configs(bus_name, path)
        new_subscriptions: list[SubscribedInterface] = []
        for subscription in subscription_configs:
            logger.debug(f"processing subscription config: {subscription.bus_name}, {subscription.path}")
            for subscription_interface in subscription.interfaces:
                if subscription_interface.interface == interface.name:
                    logger.debug(f"matching config found for bus_name={bus_name}, path={path}, interface={interface.name}")
                    subscribed_iterface = await self._subscribe_interface(bus_name, path, introspection, interface, subscription, subscription_interface)

                    new_subscriptions.append(subscribed_iterface)

        return new_subscriptions

    async def _visit_bus_name_path(self, bus_name: str, path: str) -> list[SubscribedInterface]:

        new_subscriptions: list[SubscribedInterface] = []

        try:
            introspection = await self.bus.introspect(bus_name, path)
        except TypeError as e:
            logger.warning(f"bus.introspect failed, bus_name={bus_name}, path={path}: {e}")
            return new_subscriptions

        if len(introspection.nodes) == 0:
            logger.debug(f"leaf node: bus_name={bus_name}, path={path}, is_root={introspection.is_root}, interfaces={[i.name for i in introspection.interfaces]}")

        for interface in introspection.interfaces:
            new_subscriptions.extend(
                await self._process_interface(bus_name, path, introspection, interface)
            )

        for node in introspection.nodes:
            path_seperator = "" if path.endswith('/') else "/"
            new_subscriptions.extend(
                await self._visit_bus_name_path(bus_name, f"{path}{path_seperator}{node.name}")
            )

        return new_subscriptions

    async def _handle_bus_name_added(self, bus_name: str) -> list[SubscribedInterface]:

        if not self.config.is_bus_name_configured(bus_name):
            return []

        # sanity checks
        for umh in self.bus._user_message_handlers:
            umh_bus_name = umh.__self__.bus_name
            if umh_bus_name == bus_name:
                logger.warning(f"handle_bus_name_added: {umh_bus_name} already added")

        new_subscriped_interfaces = await self._visit_bus_name_path(bus_name, "/")

        logger.info(f"new_subscriptions: {list(set([si.bus_name for si in new_subscriped_interfaces]))}")

        # setup and process triggers for each flow in each subscription
        processed_new_subscriptions: set[str] = set()

        # With all subscriptions in place, we can now ensure schedulers are created
        # create a FlowProcessor per bus_name/path subscription?
        # One global or a per subscription FlowProcessor.flow_processor_task?
        # Start a new timer job, but leverage existing FlowScheduler
        # How does the FlowScheduler now it should invoke the local FlowPocessor?
        # Maybe use queues to communicate from here with the FlowProcessor?
        # e.g.: StartFlows, StopFlows,

        for subscribed_interface in new_subscriped_interfaces:

            subscription_config = subscribed_interface.subscription_config
            if subscription_config.id not in processed_new_subscriptions:

                # Ensure all schedulers are started
                self.flow_scheduler.start_flow_set(subscription_config.flows)

                # Trigger flows that have a bus_name_added trigger configured
                await self._trigger_bus_name_added(subscription_config, subscribed_interface.bus_name)

                processed_new_subscriptions.add(subscription_config.id)

        return new_subscriped_interfaces

    async def _trigger_bus_name_added(self, subscription_config: SubscriptionConfig, bus_name: str):

        for flow in subscription_config.flows:
            for trigger in flow.triggers:
                if trigger.type == "bus_name_added":
                    context = {
                        "bus_name": bus_name,
                    }
                    trigger_message = FlowTriggerMessage(flow, trigger, datetime.now(), context)
                    await self.event_broker.flow_trigger_queue.async_q.put(trigger_message)

    async def _handle_bus_name_removed(self, bus_name: str):

        bus_name_subscriptions = self.subscriptions.get(bus_name)

        if bus_name_subscriptions:
            for path, proxy_object in bus_name_subscriptions.path_objects.items():

                subscription_configs = self.config.get_subscription_configs(bus_name=bus_name, path=path)
                for subscription_config in subscription_configs:

                    # Trigger flows that have a bus_name_added trigger configured
                    await self._trigger_bus_name_removed(subscription_config, bus_name)

                    # Stop schedule triggers
                    self.flow_scheduler.stop_flow_set(subscription_config.flows)

                # Wait for completion
                await self.event_broker.flow_trigger_queue.async_q.join()

                # clean up all dbus matchrules
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

    async def _trigger_bus_name_removed(self, subscription_config: SubscriptionConfig, bus_name: str):

        # Trigger flows that have a bus_name_removed trigger configured
        for flow in subscription_config.flows:
            for trigger in flow.triggers:
                if trigger.type == "bus_name_removed":
                    context = {
                        "bus_name": bus_name,
                    }
                    trigger_message = FlowTriggerMessage(flow, trigger, datetime.now(), context)
                    await self.event_broker.flow_trigger_queue.async_q.put(trigger_message)

    async def _dbus_name_owner_changed_callback(self, name, old_owner, new_owner):

        logger.debug(f'NameOwnerChanged: name=q{name}, old_owner={old_owner}, new_owner={new_owner}')

        if new_owner and not old_owner:
            logger.debug(f'NameOwnerChanged.new: name={name}')
            await self._handle_bus_name_added(name)
        if old_owner and not new_owner:
            logger.debug(f'NameOwnerChanged.old: name={name}')
            await self._handle_bus_name_removed(name)

    async def call_dbus_interface_method(self, interface: dbus_aio.proxy_object.ProxyInterface, method: str, method_args: list[Any]):

        call_method_name = "call_" + camel_to_snake(method)
        res = await interface.__getattribute__(call_method_name)(*method_args)

        if res:
            res = unwrap_dbus_object(res)

        logger.debug(f"call_dbus_interface_method: bus_name={interface.bus_name}, interface={interface.introspection.name}, method={method}, res={res}")

        return res

    async def get_dbus_interface_property(self, interface: dbus_aio.proxy_object.ProxyInterface, property: str):

        call_method_name = "get_" + camel_to_snake(property)
        res = await interface.__getattribute__(call_method_name)()

        if res:
            res = unwrap_dbus_object(res)

        logger.debug(f"get_dbus_interface_property: bus_name={interface.bus_name}, interface={interface.introspection.name}, property={property}, res={res}")

        return res

    async def set_dbus_interface_property(self, interface: dbus_aio.proxy_object.ProxyInterface, property: str, value):

        call_method_name = "set_" + camel_to_snake(property)
        res = await interface.__getattribute__(call_method_name)(value)

        if res:
            res = unwrap_dbus_object(res)

        logger.info(f"set_dbus_interface_property: bus_name={interface.bus_name}, interface={interface.introspection.name}, property={property}, res={res}")

        return res

    async def mqtt_receive_queue_processor_task(self):
        """Continuously processes messages from the async queue."""
        while True:
            msg = await self.event_broker.mqtt_receive_queue.async_q.get()  # Wait for a message
            try:
                await self._on_mqtt_msg(msg)
            except Exception as e:
                logger.warning(f"mqtt_receive_queue_processor_task: Exception {e}", exc_info=True)
            finally:
                self.event_broker.mqtt_receive_queue.async_q.task_done()

    async def dbus_signal_queue_processor_task(self):
        """Continuously processes messages from the async queue."""
        while True:
            signal = await self.event_broker.dbus_signal_queue.async_q.get()  # Wait for a message
            await self._handle_on_dbus_signal(signal)
            self.event_broker.dbus_signal_queue.async_q.task_done()

    async def _handle_on_dbus_signal(self, signal: DbusSignalWithState):

        logger.debug(f"dbus_signal: signal={signal.signal_config.signal}, args={signal.args}, bus_name={signal.bus_name}, path={signal.path}, interface={signal.interface_name}")

        for flow in signal.subscription_config.flows:
            for trigger in flow.triggers:
                if trigger.type == "dbus_signal" and signal.signal_config.signal == trigger.signal:

                    try:

                        matches_filter = True
                        if signal.signal_config.filter is not None:
                            matches_filter = signal.signal_config.matches_filter(self.app_context.templating, *signal.args)

                        if matches_filter:
                            context = {
                                "bus_name": signal.bus_name,
                                "path": signal.path,
                                "interface": signal.interface_name,
                                "args": signal.args
                            }
                            trigger_message = FlowTriggerMessage(flow, trigger, datetime.now(), context)

                            await self.event_broker.flow_trigger_queue.async_q.put(trigger_message)
                    except Exception as e:
                        logger.warning(f"dbus_signal_queue_processor_task: Exception {e}", exc_info=True)

    async def _on_mqtt_msg(self, msg: MqttMessage):
        # self.queue.put({
        #     "topic": topic,
        #     "payload": payload
        # })

        found_matching_topic = False
        for subscription_configs in self.config.subscriptions:
            for interface_config in subscription_configs.interfaces:
                # TODO, performance improvement
                mqtt_topic = interface_config.render_mqtt_call_method_topic(self.templating, {})
                found_matching_topic |= mqtt_topic == msg.topic

        if not found_matching_topic:
            return

        logger.debug(f"on_mqtt_msg: topic={msg.topic}, payload={json.dumps(msg.payload)}")
        matched_method = False
        matched_property = False

        payload_method = msg.payload.get("method")
        payload_method_args = msg.payload.get("args") or []

        payload_property = msg.payload.get("property")
        payload_value = msg.payload.get("value")

        if payload_method is None and (payload_property is None or payload_value is None):
            logger.info(f"on_mqtt_msg: Unsupported payload, missing 'method' or 'property/value', got method={payload_method}, property={payload_property}, value={payload_value} from {msg.payload}")
            return

        for [bus_name, bus_name_subscription] in self.subscriptions.items():
            for [path, proxy_object] in bus_name_subscription.path_objects.items():
                for subscription_configs in self.config.get_subscription_configs(bus_name=bus_name, path=path):
                    for interface_config in subscription_configs.interfaces:

                        for method in interface_config.methods:

                            # filter configured method, configured topic, ...
                            if method.method == payload_method:
                                interface = proxy_object.get_interface(name=interface_config.interface)
                                matched_method = True

                                try:
                                    logger.info(f"on_mqtt_msg: method={method.method}, args={payload_method_args}, bus_name={bus_name}, path={path}, interface={interface_config.interface}")
                                    await self.call_dbus_interface_method(interface, method.method, payload_method_args)
                                except Exception as e:
                                    logger.warning(f"on_mqtt_msg: method={method.method}, args={payload_method_args}, bus_name={bus_name} failed, exception={e}")

                        for property in interface_config.properties:
                            # filter configured property, configured topic, ...
                            if property.property == payload_property:
                                interface = proxy_object.get_interface(name=interface_config.interface)
                                matched_property = True

                                try:
                                    logger.info(f"on_mqtt_msg: property={property.property}, value={payload_value}, bus_name={bus_name}, path={path}, interface={interface_config.interface}")
                                    await self.set_dbus_interface_property(interface, property.property, payload_value)
                                except Exception as e:
                                    logger.warning(f"on_mqtt_msg: property={property.property}, value={payload_value}, bus_name={bus_name} failed, exception={e}")

        if not matched_method and not matched_property:
            if payload_method:
                logger.info(f"No configured or active dbus subscriptions for topic={msg.topic}, method={payload_method}, active bus_names={list(self.subscriptions.keys())}")
            if payload_property:
                logger.info(f"No configured or active dbus subscriptions for topic={msg.topic}, property={payload_property}, active bus_names={list(self.subscriptions.keys())}")

        # raw mode, payload contains: bus_name (specific or wildcard), path, interface_name
        # topic: dbus2mqtt/raw (with allowlist check)

        # predefined mode with topic matching from configuration
        # topic: dbus2mqtt/MediaPlayer/command
