import fnmatch
import json
import logging

from datetime import datetime
from typing import Any

import dbus_fast.aio as dbus_aio
import dbus_fast.constants as dbus_constants
import dbus_fast.introspection as dbus_introspection
import dbus_fast.message as dbus_message
import janus

from dbus_fast import SignatureTree

from dbus2mqtt import AppContext
from dbus2mqtt.config import SubscriptionConfig
from dbus2mqtt.dbus.dbus_types import (
    BusNameSubscriptions,
    DbusSignalWithState,
    SubscribedInterface,
)
from dbus2mqtt.dbus.dbus_util import (
    camel_to_snake,
    convert_mqtt_args_to_dbus,
    unwrap_dbus_object,
    unwrap_dbus_objects,
)
from dbus2mqtt.dbus.introspection_patches.mpris_playerctl import (
    mpris_introspection_playerctl,
)
from dbus2mqtt.dbus.introspection_patches.mpris_vlc import mpris_introspection_vlc
from dbus2mqtt.event_broker import MqttMessage, MqttReceiveHints
from dbus2mqtt.flow.flow_processor import FlowScheduler, FlowTriggerMessage

logger = logging.getLogger(__name__)

# TODO: Redo flow registration in _handle_bus_name_added, might want to move that to a separate file
# TODO: deregister signal watcher on shutdown

class DbusClient:

    def __init__(self, app_context: AppContext, bus: dbus_aio.message_bus.MessageBus, flow_scheduler: FlowScheduler):
        self.app_context = app_context
        self.config = app_context.config.dbus
        self.event_broker = app_context.event_broker
        self.templating = app_context.templating
        self.bus = bus
        self.flow_scheduler = flow_scheduler
        self.subscriptions: dict[str, BusNameSubscriptions] = {}

        self._dbus_signal_queue = janus.Queue[DbusSignalWithState]()
        self._dbus_object_lifecycle_signal_queue = janus.Queue[dbus_message.Message]()

        self._name_owner_match_rule = "sender='org.freedesktop.DBus',interface='org.freedesktop.DBus',path='/org/freedesktop/DBus',member='NameOwnerChanged'"
        self._interfaces_added_match_rule = "interface='org.freedesktop.DBus.ObjectManager',type='signal',member='InterfacesAdded'"
        self._interfaces_removed_match_rule = "interface='org.freedesktop.DBus.ObjectManager',type='signal',member='InterfacesRemoved'"

    async def connect(self):

        if not self.bus.connected:
            await self.bus.connect()

            if self.bus.connected:
                logger.info(f"Connected to {self.bus._bus_address}")
            else:
                logger.warning(f"Failed to connect to {self.bus._bus_address}")

            self.bus.add_message_handler(self.object_lifecycle_signal_handler)

            # Add dbus match rules to get notified of new bus_names or interfaces
            await self._add_match_rule(self._name_owner_match_rule)
            await self._add_match_rule(self._interfaces_added_match_rule)
            await self._add_match_rule(self._interfaces_removed_match_rule)

            introspection = await self.bus.introspect('org.freedesktop.DBus', '/org/freedesktop/DBus')
            obj = self.bus.get_proxy_object('org.freedesktop.DBus', '/org/freedesktop/DBus', introspection)
            dbus_interface = obj.get_interface('org.freedesktop.DBus')

            # subscribe to existing registered bus_names we are interested in
            connected_bus_names = await dbus_interface.__getattribute__("call_list_names")()

            new_subscribed_interfaces: list[SubscribedInterface] = []
            for bus_name in connected_bus_names:
                new_subscribed_interfaces.extend(await self._handle_bus_name_added(bus_name))

            logger.info(f"subscriptions on startup: {list(set([si.bus_name for si in new_subscribed_interfaces]))}")

    async def _add_match_rule(self, match_rule: str):
        reply = await self.bus.call(dbus_message.Message(
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            interface='org.freedesktop.DBus',
            member='AddMatch',
            signature='s',
            body=[(match_rule)]
        ))
        assert reply and reply.message_type == dbus_constants.MessageType.METHOD_RETURN

    async def _remove_match_rule(self, match_rule: str):
        reply = await self.bus.call(dbus_message.Message(
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            interface='org.freedesktop.DBus',
            member='RemoveMatch',
            signature='s',
            body=[(match_rule)]
        ))
        assert reply and reply.message_type == dbus_constants.MessageType.METHOD_RETURN

    def get_well_known_bus_name(self, unique_bus_name: str) -> str:

        for bns in self.subscriptions.values():
            if unique_bus_name == bns.unique_name:
                return bns.bus_name

        # # dbus_fast keeps track of well known bus_names for the high-level API.
        # # We can use this to find the bus_name for the sender.
        # for k, v in self.bus._name_owners.items():
        #     if v == unique_bus_name:
        #         return v

        return unique_bus_name

    async def get_unique_name(self, name) -> str | None:

        if name.startswith(":"):
            return name

        introspect = await self.bus.introspect("org.freedesktop.DBus", "/org/freedesktop/DBus")
        proxy = self.bus.get_proxy_object("org.freedesktop.DBus", "/org/freedesktop/DBus", introspect)
        dbus_interface = proxy.get_interface("org.freedesktop.DBus")

        return await dbus_interface.call_get_name_owner(name) # type: ignore

    def object_lifecycle_signal_handler(self, message: dbus_message.Message) -> None:

        if not message.message_type == dbus_constants.MessageType.SIGNAL:
            return

        logger.debug(f'object_lifecycle_signal_handler: interface={message.interface}, member={message.member}, body={message.body}')

        if message.interface in ['org.freedesktop.DBus', 'org.freedesktop.DBus.ObjectManager']:
            self._dbus_object_lifecycle_signal_queue.sync_q.put(message)

    def get_bus_name_subscriptions(self, bus_name: str) -> BusNameSubscriptions | None:

        return self.subscriptions.get(bus_name)

    def get_subscribed_proxy_object(self, bus_name: str, path: str) -> dbus_aio.proxy_object.ProxyObject | None:

        bus_name_subscriptions = self.get_bus_name_subscriptions(bus_name)
        if bus_name_subscriptions:
            proxy_object = bus_name_subscriptions.path_objects.get(path)
            if proxy_object:
                return proxy_object

    async def get_subscribed_or_new_proxy_object(self, bus_name: str, path: str) -> dbus_aio.proxy_object.ProxyObject | None:

        proxy_object = self.get_subscribed_proxy_object(bus_name, path)
        if proxy_object:
            return proxy_object

        # No existing subscription that contains the requested proxy_object
        logger.warning(f"Returning temporary proxy_object with an additional introspection call, bus_name={bus_name}, path={path}")
        introspection = await self.bus.introspect(bus_name=bus_name, path=path)
        proxy_object = self.bus.get_proxy_object(bus_name, path, introspection)
        if proxy_object:
            return proxy_object

        return None

    async def _create_proxy_object_subscription(self, bus_name: str, path: str, introspection: dbus_introspection.Node):

        bus_name_subscriptions = self.get_bus_name_subscriptions(bus_name)
        if not bus_name_subscriptions:

            if bus_name.startswith(":"):
                unique_name = bus_name
            else:
                # make sure we have both the well known and unique bus_name
                unique_name = await self.get_unique_name(bus_name)

            assert unique_name is not None

            bus_name_subscriptions = BusNameSubscriptions(bus_name, unique_name)
            self.subscriptions[bus_name] = bus_name_subscriptions

        proxy_object = bus_name_subscriptions.path_objects.get(path)
        if not proxy_object:
            proxy_object = self.bus.get_proxy_object(bus_name, path, introspection)
            bus_name_subscriptions.path_objects[path] = proxy_object

        return proxy_object, bus_name_subscriptions

    def _dbus_fast_signal_publisher(self, dbus_signal_state: dict[str, Any], *args):
        """publish a dbus signal to the event broker, one for each subscription_config"""

        unwrapped_args = unwrap_dbus_objects(args)

        signal_subscriptions = dbus_signal_state["signal_subscriptions"]
        for signal_subscription in signal_subscriptions:
            subscription_config = signal_subscription["subscription_config"]
            signal_config = signal_subscription["signal_config"]

            self._dbus_signal_queue.sync_q.put(
                DbusSignalWithState(
                    bus_name=dbus_signal_state["bus_name"],
                    path=dbus_signal_state["path"],
                    interface_name=dbus_signal_state["interface_name"],
                    subscription_config=subscription_config,
                    signal_config=signal_config,
                    args=unwrapped_args
                )
            )

    def _dbus_fast_signal_handler(self, signal: dbus_introspection.Signal, state: dict[str, Any]) -> Any:
        expected_args = len(signal.args)

        if expected_args == 1:
            return lambda a: self._dbus_fast_signal_publisher(state, a)
        elif expected_args == 2:
            return lambda a, b: self._dbus_fast_signal_publisher(state, a, b)
        elif expected_args == 3:
            return lambda a, b, c: self._dbus_fast_signal_publisher(state, a, b, c)
        elif expected_args == 4:
            return lambda a, b, c, d: self._dbus_fast_signal_publisher(state, a, b, c, d)
        raise ValueError("Unsupported nr of arguments")

    async def _subscribe_interface_signals(self, bus_name: str, path: str, interface: dbus_introspection.Interface, configured_signals: dict[str, list[dict]]) -> int:

        proxy_object = self.get_subscribed_proxy_object(bus_name, path)
        assert proxy_object is not None

        obj_interface = proxy_object.get_interface(interface.name)

        interface_signals = dict((s.name, s) for s in interface.signals)

        logger.debug(f"subscribe: bus_name={bus_name}, path={path}, interface={interface.name}, proxy_interface: signals={list(interface_signals.keys())}")
        signal_subscription_count = 0

        for signal, signal_subscriptions in configured_signals.items():
            interface_signal = interface_signals.get(signal)
            if interface_signal:

                on_signal_method_name = "on_" + camel_to_snake(signal)
                dbus_signal_state = {
                    "bus_name": bus_name,
                    "path": path,
                    "interface_name": interface.name,
                    "signal_subscriptions": signal_subscriptions
                }

                handler = self._dbus_fast_signal_handler(interface_signal, dbus_signal_state)
                obj_interface.__getattribute__(on_signal_method_name)(handler)
                logger.info(f"subscribed with signal_handler: signal={signal}, bus_name={bus_name}, path={path}, interface={interface.name}")

                signal_subscription_count += 1

            else:
                logger.warning(f"Invalid signal: signal={signal}, bus_name={bus_name}, path={path}, interface={interface.name}")

        return signal_subscription_count

    async def _process_interface(self, bus_name: str, path: str, introspection: dbus_introspection.Node, interface: dbus_introspection.Interface) -> list[SubscribedInterface]:

        logger.debug(f"process_interface: {bus_name}, {path}, {interface.name}")

        new_subscriptions: list[SubscribedInterface] = []
        configured_signals: dict[str, list[dict[str, Any]]] = {}

        subscription_configs = self.config.get_subscription_configs(bus_name, path)
        for subscription in subscription_configs:
            logger.debug(f"processing subscription config: {subscription.bus_name}, {subscription.path}")
            for subscription_interface in subscription.interfaces:
                if subscription_interface.interface == interface.name:
                    logger.debug(f"matching config found for bus_name={bus_name}, path={path}, interface={interface.name}")

                    # Determine signals we need to subscribe to
                    for signal_config in subscription_interface.signals:
                        signal_subscriptions = configured_signals.get(signal_config.signal, [])
                        signal_subscriptions.append({
                            "signal_config": signal_config,
                            "subscription_config": subscription
                        })
                        configured_signals[signal_config.signal] = signal_subscriptions

                    if subscription_interface.signals:
                        new_subscriptions.append(SubscribedInterface(
                            bus_name=bus_name,
                            path=path,
                            interface_name=interface.name,
                            subscription_config=subscription
                        ))

        if len(configured_signals) > 0:

            signal_subscription_count = await self._subscribe_interface_signals(
                bus_name, path, interface, configured_signals
            )
            if signal_subscription_count > 0:
                return new_subscriptions

        return []

    async def _introspect(self, bus_name: str, path: str) -> dbus_introspection.Node:

        if path == "/org/mpris/MediaPlayer2" and bus_name.startswith("org.mpris.MediaPlayer2.vlc"):
            # vlc 3.x branch contains an incomplete dbus introspection
            # https://github.com/videolan/vlc/commit/48e593f164d2bf09b0ca096d88c86d78ec1a2ca0
            # Until vlc 4.x is out we use the official specification instead
            introspection = mpris_introspection_vlc
        else:
            introspection = await self.bus.introspect(bus_name, path)

        # MPRIS: If no introspection data is available, load a default
        if path == "/org/mpris/MediaPlayer2" and bus_name.startswith("org.mpris.MediaPlayer2.") and len(introspection.interfaces) == 0:
            introspection = mpris_introspection_playerctl

        return introspection

    async def _list_bus_name_paths(self, bus_name: str, path: str) -> list[str]:
        """list all nested paths. Only paths that have interfaces are returned"""

        paths: list[str] = []

        try:
            introspection = await self._introspect(bus_name, path)
        except TypeError as e:
            logger.warning(f"bus.introspect failed, bus_name={bus_name}, path={path}: {e}")
            return paths

        if len(introspection.nodes) == 0:
            logger.debug(f"leaf node: bus_name={bus_name}, path={path}, is_root={introspection.is_root}, interfaces={[i.name for i in introspection.interfaces]}")

        if len(introspection.interfaces) > 0:
            paths.append(path)

        for node in introspection.nodes:
            path_seperator = "" if path.endswith('/') else "/"
            paths.extend(
                await self._list_bus_name_paths(bus_name, f"{path}{path_seperator}{node.name}")
            )

        return paths

    async def _subscribe_dbus_object(self, bus_name: str, path: str) -> list[SubscribedInterface]:
        """Subscribes to a dbus object at the given bus_name and path.
        For each matching subscription config, subscribe to all configured interfaces,
        start listening to signals and start/register flows if configured.
        """
        if not self.config.is_bus_name_configured(bus_name):
            return []

        new_subscriptions: list[SubscribedInterface] = []

        try:
            introspection = await self._introspect(bus_name, path)
        except TypeError as e:
            logger.warning(f"bus.introspect failed, bus_name={bus_name}, path={path}: {e}")
            return new_subscriptions

        if len(introspection.interfaces) == 0:
            logger.warning(f"Skipping dbus_object subscription, no interfaces found for bus_name={bus_name}, path={path}")
            return new_subscriptions

        interfaces_names = [i.name for i in introspection.interfaces]
        logger.info(f"subscribe_dbus_object: bus_name={bus_name}, path={path}, interfaces={interfaces_names}")

        await self._create_proxy_object_subscription(bus_name, path, introspection)

        for interface in introspection.interfaces:
            new_subscriptions.extend(
                await self._process_interface(bus_name, path, introspection, interface)
            )

        return new_subscriptions

    async def _handle_bus_name_added(self, bus_name: str) -> list[SubscribedInterface]:

        logger.debug(f"_handle_bus_name_added: bus_name={bus_name}")

        if not self.config.is_bus_name_configured(bus_name):
            return []

        object_paths = []
        subscription_configs = self.config.get_subscription_configs(bus_name=bus_name)
        for subscription_config in subscription_configs:

            # if configured path is not a wildcard, use it
            if "*" not in subscription_config.path:
                object_paths.append(subscription_config.path)
            else:
                # if configured path is a wildcard, use introspection to find all paths
                # and filter by subscription_config.path
                introspected_paths = await self._list_bus_name_paths(bus_name, "/")
                logger.debug(f"introspected paths for bus_name: {bus_name}, paths: {introspected_paths}")
                for path in introspected_paths:
                    if fnmatch.fnmatchcase(path, subscription_config.path):
                        object_paths.append(path)

        # dedupe
        object_paths = list(set(object_paths))

        new_subscribed_interfaces = []

        # for each object path, call _subscribe_dbus_object
        for object_path in object_paths:
            subscribed_object_interfaces = await self._subscribe_dbus_object(bus_name, object_path)
            new_subscribed_interfaces.extend(subscribed_object_interfaces)

        # start all flows for the new subscriptions
        if len(new_subscribed_interfaces) > 0:
            await self._start_subscription_flows(bus_name, new_subscribed_interfaces)

        return new_subscribed_interfaces

    async def _handle_bus_name_removed(self, bus_name: str):

        logger.debug(f"_handle_bus_name_removed: bus_name={bus_name}")

        bus_name_subscriptions = self.get_bus_name_subscriptions(bus_name)

        if bus_name_subscriptions:
            for path, proxy_object in bus_name_subscriptions.path_objects.items():

                subscription_configs = self.config.get_subscription_configs(bus_name=bus_name, path=path)
                for subscription_config in subscription_configs:

                    # Stop schedule triggers. Only done once per subscription_config
                    # TODO: Dont stop when other bus_names are using the same flowset
                    self.flow_scheduler.stop_flow_set(subscription_config.flows)

                    # Trigger flows that have a bus_name_removed trigger configured
                    await self._trigger_bus_name_removed(subscription_config, bus_name, path)

                    # Trigger flows that have an object_removed trigger configured
                    await self._trigger_object_removed(subscription_config, bus_name, path)


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

    async def _handle_interfaces_added(self, bus_name: str, path: str) -> None:
        """
        Handles the addition of new D-Bus interfaces for a given bus name and object path.

        This method checks if there are subscription configurations for the specified bus name and path.
        If so, it subscribes to the D-Bus object and starts the necessary subscription flows for any new interfaces.

        Args:
            bus_name (str): The well-known name of the D-Bus service where the interface was added.
            path (str): The object path on the D-Bus where the interface was added.
        """

        logger.debug(f"_handle_interfaces_added: bus_name={bus_name}, path={path}")

        if not self.config.get_subscription_configs(bus_name=bus_name, path=path):
            return

        new_subscribed_interfaces = await self._subscribe_dbus_object(bus_name, path)

        # start all flows for the new subscriptions
        if len(new_subscribed_interfaces) > 0:
            await self._start_subscription_flows(bus_name, new_subscribed_interfaces)

    async def _handle_interfaces_removed(self, bus_name: str, path: str) -> None:

        logger.debug(f"_handle_interfaces_removed: bus_name={bus_name}, path={path}")

        subscription_configs = self.config.get_subscription_configs(bus_name=bus_name, path=path)
        for subscription_config in subscription_configs:

            # Stop schedule triggers. Only done once per subscription_config and not per path
            # TODO, only stop if this subscription is not used for any other objects / paths
            self.flow_scheduler.stop_flow_set(subscription_config.flows)

            # Trigger flows that have an object_removed trigger configured
            await self._trigger_object_removed(subscription_config, bus_name, path)

        proxy_object = self.get_subscribed_proxy_object(bus_name, path)
        if proxy_object is not None:

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

            # For now that InterfacesRemoved signal means the entire object is removed from D-Bus
            del self.subscriptions[bus_name].path_objects[path]

        # cleanup the entire BusNameSubscriptions if no more objects are subscribed
        bus_name_subscriptions = self.get_bus_name_subscriptions(bus_name)
        if bus_name_subscriptions and len(bus_name_subscriptions.path_objects) == 0:
            del self.subscriptions[bus_name]

    async def _start_subscription_flows(self, bus_name: str, subscribed_interfaces: list[SubscribedInterface]):
        """Start all flows for the new subscriptions.
        For each matching bus_name-path subscription_config, the following is done:
        1. Ensure the scheduler is started, at most one scheduler will be active for a subscription_config
        2. Trigger flows that have a bus_name_added trigger configured (only once per bus_name)
        3. Trigger flows that have a interfaces_added trigger configured (once for each bus_name-path pair)
        """

        bus_name_object_paths = {}
        bus_name_object_path_interfaces = {}
        for si in subscribed_interfaces:
            bus_name_object_paths.setdefault(si.bus_name, [])
            bus_name_object_path_interfaces.setdefault(si.bus_name, {}).setdefault(si.path, [])

            if si.path not in bus_name_object_paths[si.bus_name]:
                bus_name_object_paths[si.bus_name].append(si.path)

            bus_name_object_path_interfaces[si.bus_name][si.path].append(si.interface_name)


        # new_subscribed_bus_names = list(set([si.bus_name for si in subscribed_interfaces]))
        # new_subscribed_bus_names_paths = {
        #     bus_name: list(set([si.path for si in subscribed_interfaces if si.bus_name == bus_name]))
        #     for bus_name in new_subscribed_bus_names
        # }

        logger.debug(f"_start_subscription_flows: ew_subscriptions: {list(bus_name_object_paths.keys())}")
        logger.debug(f"_start_subscription_flows: new_bus_name_object_paths: {bus_name_object_paths}")

        # setup and process triggers for each flow in each subscription
        # just once per subscription_config
        processed_new_subscriptions: set[str] = set()

        # With all subscriptions in place, we can now ensure schedulers are created
        # create a FlowProcessor per bus_name/path subscription?
        # One global or a per subscription FlowProcessor.flow_processor_task?
        # Start a new timer job, but leverage existing FlowScheduler
        # How does the FlowScheduler now it should invoke the local FlowPocessor?
        # Maybe use queues to communicate from here with the FlowProcessor?
        # e.g.: StartFlows, StopFlows,

        # for each bus_name
        for bus_name, path_interfaces_map in bus_name_object_path_interfaces.items():

            paths = list(path_interfaces_map.keys())

            # for each path in the bus_name
            for object_path in paths:

                object_interfaces = path_interfaces_map[object_path]

                # For each subscription_config that matches the bus_name and object_path
                subscription_configs = self.config.get_subscription_configs(bus_name, object_path)
                for subscription_config in subscription_configs:

                    # Only process subscription_config once, no matter how many paths it matches
                    if subscription_config.id not in processed_new_subscriptions:

                        # Ensure all schedulers are started
                        # If a scheduler is already active for this subscription flow, it will be reused
                        self.flow_scheduler.start_flow_set(subscription_config.flows)

                        # Trigger flows that have a bus_name_added trigger configured

                        # TODO: path arg doesn't make sense here, it did work for mpris however where there is only one path
                        # leaving it now for backwards compatibility
                        await self._trigger_bus_name_added(subscription_config, bus_name, object_path)

                        processed_new_subscriptions.add(subscription_config.id)

                    # Trigger flows that have a object_added trigger configured
                    await self._trigger_object_added(subscription_config, bus_name, object_path, object_interfaces)

    async def _trigger_flows(self, subscription_config: SubscriptionConfig, type: str, context: dict):

        for flow in subscription_config.flows:
            for trigger in flow.triggers:
                if trigger.type == type:
                    trigger_message = FlowTriggerMessage(flow, trigger, datetime.now(), context)
                    await self.event_broker.flow_trigger_queue.async_q.put(trigger_message)

    async def _trigger_bus_name_added(self, subscription_config: SubscriptionConfig, bus_name: str, path: str):

        # Trigger flows that have a bus_name_added trigger configured
        await self._trigger_flows(subscription_config, "bus_name_added", {
            "bus_name": bus_name,
            "path": path
        })

    async def _trigger_bus_name_removed(self, subscription_config: SubscriptionConfig, bus_name: str, path: str):

        # Trigger flows that have a bus_name_removed trigger configured
        await self._trigger_flows(subscription_config, "bus_name_removed", {
            "bus_name": bus_name,
            "path": path
        })

    async def _trigger_object_added(self, subscription_config: SubscriptionConfig, bus_name: str, object_path: str, object_interfaces: list[str]):

        # Trigger flows that have a object_added trigger configured
        await self._trigger_flows(subscription_config, "object_added", {
            "bus_name": bus_name,
            "path": object_path
            # "interfaces": object_interfaces
        })

    async def _trigger_object_removed(self, subscription_config: SubscriptionConfig, bus_name: str, path: str):

        # Trigger flows that have a object_removed trigger configured
        await self._trigger_flows(subscription_config, "object_removed", {
            "bus_name": bus_name,
            "path": path
        })

    async def call_dbus_interface_method(self, interface: dbus_aio.proxy_object.ProxyInterface, method: str, method_args: list[Any]):

        converted_args = convert_mqtt_args_to_dbus(method_args)
        call_method_name = "call_" + camel_to_snake(method)

        # In case of a payload that doesn't match the dbus signature type, this prints a better error message
        interface_method = next((m for m in interface.introspection.methods if m.name == method), None)
        if interface_method:
            in_signature_tree = SignatureTree(interface_method.in_signature)
            in_signature_tree.verify(converted_args)

        try:
            res = await interface.__getattribute__(call_method_name)(*converted_args)
        except Exception as e:
            logger.debug(f"Error while calling dbus object, bus_name={interface.bus_name}, interface={interface.introspection.name}, method={method}, converted_args={converted_args}", exc_info=True)
            raise e

        if res:
            res = unwrap_dbus_object(res)

        logger.debug(f"call_dbus_interface_method: bus_name={interface.bus_name}, interface={interface.introspection.name}, method={method}, res={res}")

        return res

    async def get_dbus_interface_property(self, interface: dbus_aio.proxy_object.ProxyInterface, property: str) -> Any:

        call_method_name = "get_" + camel_to_snake(property)
        res = await interface.__getattribute__(call_method_name)()

        if res:
            res = unwrap_dbus_object(res)

        logger.debug(f"get_dbus_interface_property: bus_name={interface.bus_name}, interface={interface.introspection.name}, property={property}, res={res}")

        return res

    async def set_dbus_interface_property(self, interface: dbus_aio.proxy_object.ProxyInterface, property: str, value: Any) -> None:

        call_method_name = "set_" + camel_to_snake(property)
        await interface.__getattribute__(call_method_name)(value)

        logger.info(f"set_dbus_interface_property: bus_name={interface.bus_name}, interface={interface.introspection.name}, property={property}, value={value}")

    async def mqtt_receive_queue_processor_task(self):
        """Continuously processes messages from the async queue."""
        while True:
            msg, hints = await self.event_broker.mqtt_receive_queue.async_q.get()  # Wait for a message
            try:
                await self._on_mqtt_msg(msg, hints)
            except Exception as e:
                logger.warning(f"mqtt_receive_queue_processor_task: Exception {e}", exc_info=True)
            finally:
                self.event_broker.mqtt_receive_queue.async_q.task_done()

    async def dbus_signal_queue_processor_task(self):
        """Continuously processes messages from the async queue."""
        while True:
            signal = await self._dbus_signal_queue.async_q.get()
            await self._handle_on_dbus_signal(signal)
            self._dbus_signal_queue.async_q.task_done()

    async def dbus_object_lifecycle_signal_processor_task(self):
        """Continuously processes messages from the async queue."""
        while True:
            message = await self._dbus_object_lifecycle_signal_queue.async_q.get()
            await self._handle_dbus_object_lifecycle_signal(message)
            self._dbus_object_lifecycle_signal_queue.async_q.task_done()

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
                            trigger_context = {
                                "bus_name": signal.bus_name,
                                "path": signal.path,
                                "interface": signal.interface_name,
                                "signal": signal.signal_config.signal,
                                "args": signal.args
                            }
                            trigger_message = FlowTriggerMessage(
                                flow,
                                trigger,
                                datetime.now(),
                                trigger_context=trigger_context
                            )

                            await self.event_broker.flow_trigger_queue.async_q.put(trigger_message)
                    except Exception as e:
                        logger.warning(f"dbus_signal_queue_processor_task: Exception {e}", exc_info=True)

    async def _handle_dbus_object_lifecycle_signal(self, message: dbus_message.Message):

        if message.member == 'NameOwnerChanged':
            name, old_owner, new_owner = message.body
            if new_owner != '' and old_owner == '':
                await self._handle_bus_name_added(name)
            if old_owner != '' and new_owner == '':
                await self._handle_bus_name_removed(name)

        if message.interface == 'org.freedesktop.DBus.ObjectManager':
            bus_name = self.get_well_known_bus_name(message.sender)
            if message.member == 'InterfacesAdded':
                path = message.body[0]
                await self._handle_interfaces_added(bus_name, path)
            elif message.member == 'InterfacesRemoved':
                path = message.body[0]
                await self._handle_interfaces_removed(bus_name, path)

    async def _on_mqtt_msg(self, msg: MqttMessage, hints: MqttReceiveHints):
        """Executes dbus method calls or property updates on objects when messages have
        1. a matching subscription configured
        2. a matching method
        3. a matching bus_name (if provided)
        4. a matching path (if provided)
        """

        found_matching_topic = False
        for subscription_configs in self.config.subscriptions:
            for interface_config in subscription_configs.interfaces:
                mqtt_topic = interface_config.render_mqtt_command_topic(self.templating, {})
                found_matching_topic |= mqtt_topic == msg.topic

        if not found_matching_topic:
            return

        logger.debug(f"on_mqtt_msg: topic={msg.topic}, payload={json.dumps(msg.payload)}")
        matched_method = False
        matched_property = False

        payload_bus_name = msg.payload.get("bus_name") or "*"
        payload_path = msg.payload.get("path") or "*"

        payload_method = msg.payload.get("method")
        payload_method_args = msg.payload.get("args") or []

        payload_property = msg.payload.get("property")
        payload_value = msg.payload.get("value")

        if payload_method is None and (payload_property is None or payload_value is None):
            if msg.payload and hints.log_unmatched_message:
                logger.info(f"on_mqtt_msg: Unsupported payload, missing 'method' or 'property/value', got method={payload_method}, property={payload_property}, value={payload_value} from {msg.payload}")
            return

        for [bus_name, bus_name_subscription] in self.subscriptions.items():
            if fnmatch.fnmatchcase(bus_name, payload_bus_name):
                for [path, proxy_object] in bus_name_subscription.path_objects.items():
                    if fnmatch.fnmatchcase(path, payload_path):
                        for subscription_configs in self.config.get_subscription_configs(bus_name=bus_name, path=path):
                            for interface_config in subscription_configs.interfaces:

                                for method in interface_config.methods:
                                    # filter configured method, configured topic, ...
                                    if method.method == payload_method:
                                        interface = proxy_object.get_interface(name=interface_config.interface)
                                        matched_method = True

                                        result = None
                                        error = None
                                        try:
                                            logger.info(f"on_mqtt_msg: method={method.method}, args={payload_method_args}, bus_name={bus_name}, path={path}, interface={interface_config.interface}")
                                            result = await self.call_dbus_interface_method(interface, method.method, payload_method_args)

                                            # Send response if configured
                                            await self._send_mqtt_response(
                                                interface_config, result, None, bus_name, path,
                                                method=method.method, args=payload_method_args
                                            )

                                        except Exception as e:
                                            error = e
                                            logger.warning(f"on_mqtt_msg: Failed calling method={method.method}, args={payload_method_args}, bus_name={bus_name}, exception={e}")

                                            # Send error response if configured
                                            await self._send_mqtt_response(
                                                interface_config, None, error, bus_name, path,
                                                method=method.method, args=payload_method_args
                                            )

                                for property in interface_config.properties:
                                    # filter configured property, configured topic, ...
                                    if property.property == payload_property:
                                        interface = proxy_object.get_interface(name=interface_config.interface)
                                        matched_property = True

                                        try:
                                            logger.info(f"on_mqtt_msg: property={property.property}, value={payload_value}, bus_name={bus_name}, path={path}, interface={interface_config.interface}")
                                            await self.set_dbus_interface_property(interface, property.property, payload_value)

                                            # Send property set response if configured
                                            await self._send_mqtt_response(
                                                interface_config, payload_value, None, bus_name, path,
                                                property=property.property, value=[payload_value]
                                            )

                                        except Exception as e:
                                            logger.warning(f"on_mqtt_msg: property={property.property}, value={payload_value}, bus_name={bus_name} failed, exception={e}")

                                            # Send property set error response if configured
                                            await self._send_mqtt_response(
                                                interface_config, None, e, bus_name, path,
                                                property=property.property, value=[payload_value],
                                            )

        if not matched_method and not matched_property and hints.log_unmatched_message:
            if payload_method:
                logger.info(f"No configured or active dbus subscriptions for topic={msg.topic}, method={payload_method}, bus_name={payload_bus_name}, path={payload_path}, active bus_names={list(self.subscriptions.keys())}")
            if payload_property:
                logger.info(f"No configured or active dbus subscriptions for topic={msg.topic}, property={payload_property}, bus_name={payload_bus_name}, path={payload_path}, active bus_names={list(self.subscriptions.keys())}")

    async def _send_mqtt_response(self, interface_config, result: Any, error: Exception | None, bus_name: str, path: str, *args, **kwargs):
        """Send MQTT response for a method call if response topic is configured

        Args:
            method (str, optional): The method to execute
            args (list, optional): Arguments for the method
            property (str, optional): The property to set
            value (any, optional): The value to set for the property
        """

        if not interface_config.mqtt_response_topic:
            return

        try:
            # Build response context
            response_context = {
                "bus_name": bus_name,
                "path": path,
                "interface": interface_config.interface,
                "timestamp": datetime.now().isoformat()
            }

            # Check if 'method' and 'args' are provided
            if 'method' in kwargs and 'args' in kwargs:
                method = kwargs['method']
                args = kwargs['args']
                response_context.update({
                    "method": method,
                    "args": args,
                })
            # Check if 'property' and 'value' are provided
            elif 'property' in kwargs and 'value' in kwargs:
                property = kwargs['property']
                value = kwargs['value']
                response_context.update({
                    "property": property,
                    "value": value,
                })
            else:
                return "Invalid arguments: Please provide either 'method' and 'args' or 'property' and 'value'"

            # Add result or error to context
            if error:
                response_context.update({
                    "success": False,
                    "error": str(error),
                    "error_type": error.__class__.__name__
                })
            else:
                response_context.update({
                    "success": True,
                    "result": result
                })

            # Render response topic
            response_topic = interface_config.render_mqtt_response_topic(
                self.templating, response_context
            )

            if response_topic:
                # Send response via MQTT
                response_msg = MqttMessage(
                    topic=response_topic,
                    payload=response_context,
                    payload_serialization_type="json"
                )
                await self.event_broker.publish_to_mqtt(response_msg)

                logger.debug(f"Sent MQTT response: topic={response_topic}, success={response_context['success']}")

        except Exception as e:
            logger.warning(f"Failed to send MQTT response: {e}")
