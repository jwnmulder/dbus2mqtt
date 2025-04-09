import json
import logging

from datetime import datetime

import dbus_next.aio as dbus_aio
import dbus_next.introspection as dbus_introspection

from dbus2mqtt import AppContext
from dbus2mqtt.config import InterfaceConfig, SubscriptionConfig
from dbus2mqtt.dbus.dbus_types import BusNameSubscriptions
from dbus2mqtt.dbus.dbus_util import camel_to_snake, unwrap_dbus_object
from dbus2mqtt.event_broker import DbusSignalWithState, MqttMessage
from dbus2mqtt.flow.flow_processor import FlowScheduler, FlowTriggerMessage

logger = logging.getLogger(__name__)


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
            dbus_interface.on_name_owner_changed(self._dbus_name_owner_changed_callback)

            # subscribe to existing registered bus_names we are interested in
            connected_bus_names = await dbus_interface.call_list_names()

            for bus_name in connected_bus_names:
                await self._handle_bus_name_added(bus_name)

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

    async def _subscribe_interface(self, bus_name: str, path: str, introspection: dbus_introspection.Node, interface: dbus_introspection.Interface, subscription_config: SubscriptionConfig, si: InterfaceConfig):

        proxy_object, bus_name_subscriptions = self._ensure_proxy_object_subscription(bus_name, path, introspection)
        obj_interface = proxy_object.get_interface(interface.name)

        interface_signals = dict((s.name, s) for s in interface.signals)

        logger.debug(f"subscribe: bus_name={bus_name}, path={path}, interface={interface.name}, proxy_interface: signals={list(interface_signals.keys())}")

        for signal_config in si.signals:
            interface_signal = interface_signals.get(signal_config.signal)
            if interface_signal:

                on_signal_method_name = "on_" + camel_to_snake(signal_config.signal)
                obj_interface.__getattribute__(on_signal_method_name)(
                    lambda a, b, c:
                        self.event_broker.on_dbus_signal(DbusSignalWithState(
                            bus_name_subscriptions, path,
                            interface.name,
                            subscription_config,
                            signal_config,
                            args=[a, b, c]
                        ))
                )
                logger.info(f"subscribed with signal_handler: signal={signal_config.signal}, bus_name={bus_name}, path={path}, interface={interface.name}")

            else:
                logger.warning(f"Invalid signal: signal={signal_config.signal}, bus_name={bus_name}, path={path}, interface={interface.name}")


    async def _process_interface(self, bus_name: str, path: str, introspection: dbus_introspection.Node, interface: dbus_introspection.Interface) -> list[tuple[InterfaceConfig, SubscriptionConfig]]:

        logger.debug(f"process_interface: {bus_name}, {path}, {interface.name}")
        subscription_configs = self.config.get_subscription_configs(bus_name, path)
        new_subscriptions: list[tuple[InterfaceConfig, SubscriptionConfig]] = []
        for subscription in subscription_configs:
            logger.debug(f"processing subscription config: {subscription.bus_name}, {subscription.path}")
            for subscription_interface in subscription.interfaces:
                if subscription_interface.interface == interface.name:
                    logger.debug(f"matching config found for bus_name={bus_name}, path={path}, interface={interface.name}")
                    await self._subscribe_interface(bus_name, path, introspection, interface, subscription, subscription_interface)

                    new_subscriptions.append((subscription_interface, subscription))

        return new_subscriptions

    async def _visit_bus_name_path(self, bus_name: str, path: str) -> list[tuple[InterfaceConfig, SubscriptionConfig]]:

        introspection = await self.bus.introspect(bus_name, path)
        new_subscriptions: list[tuple[InterfaceConfig, SubscriptionConfig]] = []

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

    async def _handle_bus_name_added(self, bus_name: str):

        if not self.config.is_bus_name_configured(bus_name):
            return

        # sanity checks
        for umh in self.bus._user_message_handlers:
            umh_bus_name = umh.__self__.bus_name
                # umh_bus_name = umh.__self__.bus_name
            if umh_bus_name == bus_name:
                logger.warning(f"handle_bus_name_added: {umh_bus_name} already added")

        new_subscriptions = await self._visit_bus_name_path(bus_name, "/")

        logger.info(f"new_subscriptions: {[s.bus_name for (i,s) in new_subscriptions]}")
        for interface_config, subscription_config in new_subscriptions:
            # With all subscriptions in place, we can now ensure schedulers are created
            # create a FlowProcessor per bus_name/path subscription?
            # One global or a per subscription FlowProcessor.flow_processor_task?
            # Start a new timer job, but leverage existing FlowScheduler
            # How does the FlowScheduler now it should invoke the local FlowPocessor?
            # Maybe use queues to communicate from here with the FlowProcessor?
            # e.g.: StartFlows, StopFlows,

            # Ensure all schedulers are started

            self.flow_scheduler.start_flow_set(subscription_config.flows)
            # bus_name = subscription.bus_name
            # path = subscription.path
            # for flow in subscription.flows:
            #     for trigger in flow.triggers:


    async def _handle_bus_name_removed(self, bus_name: str):

        bus_name_subscriptions = self.subscriptions.get(bus_name)

        if bus_name_subscriptions:
            for path, proxy_object in bus_name_subscriptions.path_objects.items():

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

                # stop any workflow triggers
                subscription_configs = self.config.get_subscription_configs(bus_name=bus_name, path=path)
                for subscription_config in subscription_configs:
                    self.flow_scheduler.stop_flow_set(subscription_config.flows)

            del self.subscriptions[bus_name]

    async def _dbus_name_owner_changed_callback(self, name, old_owner, new_owner):

        logger.debug(f'NameOwnerChanged: name=q{name}, old_owner={old_owner}, new_owner={new_owner}')

        if new_owner and not old_owner:
            logger.debug(f'NameOwnerChanged.new: name={name}')
            await self._handle_bus_name_added(name)
        if old_owner and not new_owner:
            logger.debug(f'NameOwnerChanged.old: name={name}')
            await self._handle_bus_name_removed(name)

    async def call_dbus_interface_method(self, interface: dbus_aio.proxy_object.ProxyInterface, method: str, method_args: list):

        call_method_name = "call_" + camel_to_snake(method)
        res = await interface.__getattribute__(call_method_name)(*method_args)

        if res:
            res = unwrap_dbus_object(res)

        logger.debug(f"call_dbus_interface_method: bus_name={interface.bus_name}, interface={interface.introspection.name}, method={method}, res={res}")

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

            for flow in signal.subscription_config.flows:
                for trigger in flow.triggers:
                    if trigger.type == "dbus_signal" and signal.signal_config.signal == trigger.signal:

                        try:

                            unwrapped_args = [unwrap_dbus_object(o) for o in signal.args]
                            matches_filter = signal.signal_config.matches_filter(self.app_context.templating, *unwrapped_args)

                            if matches_filter:
                                context = {
                                    "bus_name": signal.bus_name_subscriptions.bus_name,
                                    "path": signal.path,
                                    "interface": signal.interface_name,
                                    "args": unwrapped_args,
                                }
                                trigger_message = FlowTriggerMessage(flow, trigger, datetime.now(), context)
                                print("XXXXXXXXXXXXX")
                                # log_msg = f"on_signal: signal={signal_handler_config.signal}, bus_name={bus_name}, path={path}, interface={interface_name}"
                                # if logger.isEnabledFor(logging.DEBUG):
                                #     logger.debug(f"{log_msg}, payload={payload}")
                                # else:
                                #     logger.info(log_msg)

                                await self.event_broker.flow_trigger_queue.async_q.put(trigger_message)
                        except Exception as e:
                            logger.warning(f"dbus_signal_queue_processor_task: Exception {e}", exc_info=True)
                        finally:
                            self.event_broker.dbus_signal_queue.async_q.task_done()

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
