import asyncio
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

from dbus_fast import BusType, SignatureTree
from dbus_fast.aio import MessageBus

from dbus2mqtt import AppContext
from dbus2mqtt.config import (
    FlowTriggerBusNameAddedConfig,
    FlowTriggerBusNameRemovedConfig,
    FlowTriggerDbusObjectAddedConfig,
    FlowTriggerDbusObjectRemovedConfig,
    InterfaceConfig,
    MethodConfig,
    PropertyConfig,
)
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
from dbus2mqtt.flow.flow_processor import FlowScheduler
from dbus2mqtt.flow.flow_trigger_handlers import (
    FlowTriggerDbusSignalHandler,
    FlowTriggerHandler,
)
from dbus2mqtt.flow.flow_trigger_processor import (
    FlowTriggerProcessor,
)

logger = logging.getLogger(__name__)

@staticmethod
def _init_bus(app_context: AppContext):
    bus_type = BusType.SYSTEM if app_context.config.dbus.bus_type == "SYSTEM" else BusType.SESSION
    bus = dbus_aio.message_bus.MessageBus(bus_type=bus_type)
    return bus

class DbusClient:

    def __init__(self, app_context: AppContext, flow_scheduler: FlowScheduler, bus: MessageBus | None = None):
        self.app_context = app_context
        self.config = app_context.config.dbus
        self.event_broker = app_context.event_broker
        self.templating = app_context.templating
        self.flow_scheduler = flow_scheduler

        self._bus: MessageBus = bus or _init_bus(app_context)
        self._dbus_signal_queue = janus.Queue[DbusSignalWithState]()
        self._dbus_object_lifecycle_signal_queue = janus.Queue[dbus_message.Message]()
        self._subscriptions: dict[str, BusNameSubscriptions] = {}
        self._trigger_processor = FlowTriggerProcessor(app_context)

        self._bus_init_lock = asyncio.Lock()

        self._name_owner_match_rule = "sender='org.freedesktop.DBus',interface='org.freedesktop.DBus',path='/org/freedesktop/DBus',member='NameOwnerChanged'"
        self._interfaces_added_match_rule = "interface='org.freedesktop.DBus.ObjectManager',type='signal',member='InterfacesAdded'"
        self._interfaces_removed_match_rule = "interface='org.freedesktop.DBus.ObjectManager',type='signal',member='InterfacesRemoved'"

    async def _reconnect(self):
        """Initializes a new MessageBus, clears all subscriptions and re-connects to DBus."""
        async with self._bus_init_lock:
            self._bus = _init_bus(self.app_context)
            self._subscriptions = {}
            await self.connect(reconnect=True)

    async def dbus_connection_monitor(self):

        assert self._bus.connected

        reconnect_counter = 0

        while True:
            disconnect_err = "DBus disconnected"
            try:
                await self._bus.wait_for_disconnect()
            except Exception as e:
                disconnect_err = f"DBus disconnected, connection terminated unexpectedly: {type(e)}"

            logger.warning(f"wait_for_disconnect: {disconnect_err}, reconnecting...")

            # Calculate reconnect delay
            reconnect_counter += 1
            delay = max(1, min(reconnect_counter * 5, 60))
            try:
                await self._reconnect()
                delay = 0
                reconnect_counter = 0
            except Exception as e:
                logger.warning(f"Error reconnecting due to {e}, sleeping {delay} seconds", exc_info=True)

            await asyncio.sleep(delay)

    async def connect(self, reconnect: bool = False):
        """Authententicates and connects to DBus.

        On successful connection:
        1. Add match rules for ObjectManager signals
        2. Subscribes to configured dbus_objects
        3. For each subscribed dbus_object, trigger object_added for configured flows
        """
        if self._bus.connected:
            return

        await self._bus.connect()

        if self._bus.connected:
            logger.info(f"Connected to {self._bus._bus_address} (reconnected={reconnect})")
        else:
            logger.warning(f"Failed connecting to {self._bus._bus_address}")
            return

        # Setup signal handler and match rules
        try:
            self._bus.add_message_handler(self.object_lifecycle_signal_handler)
            await self._add_match_rule(self._name_owner_match_rule)
            await self._add_match_rule(self._interfaces_added_match_rule)
            await self._add_match_rule(self._interfaces_removed_match_rule)
        except Exception as e:
            # Disconnect if setup of listeners didn't succeed
            self._bus.disconnect()
            raise e

        await self._subscribe_on_connect(reconnect)

    async def _subscribe_on_connect(self, reconnect: bool):
        """Subscribe to existing registered bus_names that are matching any of the configured subscriptions."""
        introspection = await self._bus.introspect('org.freedesktop.DBus', '/org/freedesktop/DBus')
        obj = self._bus.get_proxy_object('org.freedesktop.DBus', '/org/freedesktop/DBus', introspection)
        dbus_interface = obj.get_interface('org.freedesktop.DBus')

        connected_bus_names = await self._dbus_interface_call(dbus_interface, "call_list_names")

        new_subscribed_interfaces: list[SubscribedInterface] = []

        # Triggering flows is only done at startup and must not
        # be done after a reconnect
        trigger_flows = not reconnect
        for bus_name in connected_bus_names:
            new_subscribed_interfaces.extend(await self._handle_bus_name_added(bus_name, trigger_flows))

        if not reconnect:
            logger.info(f"subscriptions on startup: {list(set([si.bus_name for si in new_subscribed_interfaces]))}")

    async def _dbus_interface_call(self, interface: dbus_aio.proxy_object.ProxyInterface, call_method: str, *call_args) -> Any:

        if not self._bus.connected:
            raise RuntimeError(f"Unable to invoke dbus object, not connected to dbus, bus_name={interface.bus_name}, interface={interface.introspection.name}, method={call_method}, converted_args={call_args}")

        try:
            method_fn = interface.__getattribute__(call_method)
            res = await method_fn(*call_args)
            return res
        except Exception as e:
            raise e

    async def _add_match_rule(self, match_rule: str):
        reply = await self._bus.call(dbus_message.Message(
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            interface='org.freedesktop.DBus',
            member='AddMatch',
            signature='s',
            body=[(match_rule)]
        ))
        assert reply and reply.message_type == dbus_constants.MessageType.METHOD_RETURN

    async def _remove_match_rule(self, match_rule: str):
        reply = await self._bus.call(dbus_message.Message(
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            interface='org.freedesktop.DBus',
            member='RemoveMatch',
            signature='s',
            body=[(match_rule)]
        ))
        assert reply and reply.message_type == dbus_constants.MessageType.METHOD_RETURN

    def get_well_known_bus_name(self, unique_bus_name: str) -> str:

        for bns in self._subscriptions.values():
            if unique_bus_name == bns.unique_name:
                return bns.bus_name

        return unique_bus_name

    async def get_unique_name(self, name) -> str | None:

        if name.startswith(":"):
            return name

        introspect = await self._bus.introspect("org.freedesktop.DBus", "/org/freedesktop/DBus")
        proxy = self._bus.get_proxy_object("org.freedesktop.DBus", "/org/freedesktop/DBus", introspect)
        dbus_interface = proxy.get_interface("org.freedesktop.DBus")

        return await dbus_interface.call_get_name_owner(name) # type: ignore

    def object_lifecycle_signal_handler(self, message: dbus_message.Message) -> None:

        if not message.message_type == dbus_constants.MessageType.SIGNAL:
            return

        logger.debug(f'object_lifecycle_signal_handler: interface={message.interface}, member={message.member}, body={message.body}')

        if message.interface in ['org.freedesktop.DBus', 'org.freedesktop.DBus.ObjectManager']:
            self._dbus_object_lifecycle_signal_queue.sync_q.put(message)

    def get_subscribed_bus_names(self) -> list[str]:
        return list(self._subscriptions.keys())

    def get_subscribed_dbus_objects(self) -> list[tuple[str, str]]:
        """Return a list of all subscribed (bus_name, path) tuples."""
        res: list[tuple[str, str]] = []
        for bus_name_subscriptions in self._subscriptions.values():
            for path in bus_name_subscriptions.path_objects.keys():
                res.append((bus_name_subscriptions.bus_name, path))
        return res

    def get_bus_name_subscriptions(self, bus_name: str) -> BusNameSubscriptions | None:

        return self._subscriptions.get(bus_name)

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
        introspection = await self._bus.introspect(bus_name=bus_name, path=path)
        proxy_object = self._bus.get_proxy_object(bus_name, path, introspection)
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
            self._subscriptions[bus_name] = bus_name_subscriptions

        proxy_object = bus_name_subscriptions.path_objects.get(path)
        if not proxy_object:
            proxy_object = self._bus.get_proxy_object(bus_name, path, introspection)
            bus_name_subscriptions.path_objects[path] = proxy_object

        return proxy_object, bus_name_subscriptions

    def _dbus_fast_signal_publisher(self, dbus_signal_state: dict[str, Any], *args):
        """Publish a dbus signal to the event broker, one for each subscription_config."""
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

    async def _process_interface(self, bus_name: str, path: str, interface: dbus_introspection.Interface) -> list[SubscribedInterface]:

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
            introspection = await self._bus.introspect(bus_name, path)

        # MPRIS: If no introspection data is available, load a default
        if path == "/org/mpris/MediaPlayer2" and bus_name.startswith("org.mpris.MediaPlayer2.") and len(introspection.interfaces) == 0:
            introspection = mpris_introspection_playerctl

        return introspection

    async def _list_bus_name_paths(self, bus_name: str, path: str) -> list[str]:
        """List all nested paths. Only paths that have interfaces are returned."""
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
                await self._process_interface(bus_name, path, interface)
            )

        return new_subscriptions

    async def _handle_bus_name_added(self, bus_name: str, trigger_flows: bool = True) -> list[SubscribedInterface]:

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
            await self._start_subscription_flows(bus_name, new_subscribed_interfaces, trigger_flows)

        return new_subscribed_interfaces

    def _stop_flow_set_if_needed(self, bus_name: str, path: str | None) -> None:
        """Stop flow sets for subscription_configs that are no longer in use.

        If path is None, all subscription_configs for the given bus_name are considered.
        This method should be called before removing any subscriptions for the given bus_name and path.
        """
        # Check which flow sets are in scope for the given dbus object
        subscription_configs = self.config.get_subscription_configs(bus_name=bus_name, path=path)

        # For each subscription_config, check if there are other subscriptions still active,
        # meaning all dbus objects not matching this functions bus_name and path arguments
        subscription_config_in_use_count: dict[str, int] = {}

        # Count all active subscriptions for the subscription_configs
        for subscribed_bus_name, subscribed_path in self.get_subscribed_dbus_objects():
            for subscription_config in subscription_configs:
                count = subscription_config_in_use_count.get(subscription_config.id, 0)
                if subscription_config.matches_dbus_object(subscribed_bus_name, subscribed_path):
                    subscription_config_in_use_count[subscription_config.id] = count + 1

        logger.debug(f"subscription_config_in_use_count: {subscription_config_in_use_count}")

        for subscription_config in subscription_configs:
            count = subscription_config_in_use_count.get(subscription_config.id, 0)
            if count <= 1:
                self.flow_scheduler.stop_flow_set(subscription_config.flows)


    async def _handle_bus_name_removed(self, bus_name: str):

        logger.debug(f"_handle_bus_name_removed: bus_name={bus_name}")

        bus_name_subscriptions = self.get_bus_name_subscriptions(bus_name)
        if bus_name_subscriptions:

            # Stop flow set if needed
            self._stop_flow_set_if_needed(bus_name, None)

            # Wait for completion of any pending / in-progress triggers
            await self.event_broker.flow_trigger_queue.async_q.join()

            # Cleanup dbus_fast message handlers and matchrules
            for path, proxy_object in bus_name_subscriptions.path_objects.items():

                # clean up all dbus matchrules
                for interface in proxy_object._interfaces.values():
                    proxy_interface: dbus_aio.proxy_object.ProxyInterface = interface

                    # officially you should do 'off_...' but the below is easier
                    # proxy_interface.off_properties_changed(self.on_properties_changed)

                    # clean lingering interface matchrule from bus
                    if proxy_interface._signal_match_rule in self._bus._match_rules.keys():
                        self._bus._remove_match_rule(proxy_interface._signal_match_rule)

                    # clean lingering interface messgage handler from bus
                    self._bus.remove_message_handler(proxy_interface._message_handler)

            # Cleanup all dbus2mqtt subscriptions for this bus_name
            del self._subscriptions[bus_name]

            # Fire object_removed triggers for all flows
            for path in bus_name_subscriptions.path_objects.keys():
                subscription_configs = self.config.get_subscription_configs(bus_name=bus_name, path=path)
                for subscription_config in subscription_configs:

                    trigger_context = {
                        "bus_name": bus_name,
                        "path": path
                    }

                    # Trigger flows that have a bus_name_removed trigger configured
                    await self._trigger_processor.trigger_subscription_flows(
                        subscription_config,
                        FlowTriggerHandler(FlowTriggerBusNameRemovedConfig.type, trigger_context)
                    )

                    # Trigger flows that have an object_removed trigger configured
                    await self._trigger_processor.trigger_subscription_flows(
                        subscription_config,
                        FlowTriggerHandler(FlowTriggerDbusObjectRemovedConfig.type, trigger_context)
                    )

    async def _handle_interfaces_added(self, bus_name: str, path: str) -> None:
        """Handles the addition of new D-Bus interfaces for a given bus name and object path.

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

        # Stop flow set if needed
        self._stop_flow_set_if_needed(bus_name, path)

        # Wait for completion of any pending / in-progress triggers
        await self.event_broker.flow_trigger_queue.async_q.join()

        # Cleanup dbus_fast message handlers and matchrules
        proxy_object = self.get_subscribed_proxy_object(bus_name, path)
        if proxy_object is not None:

            # clean up all dbus matchrules
            for interface in proxy_object._interfaces.values():
                proxy_interface: dbus_aio.proxy_object.ProxyInterface = interface

                # officially you should do 'off_...' but the below is easier
                # proxy_interface.off_properties_changed(self.on_properties_changed)

                # clean lingering interface matchrule from bus
                if proxy_interface._signal_match_rule in self._bus._match_rules.keys():
                    self._bus._remove_match_rule(proxy_interface._signal_match_rule)

                # clean lingering interface messgage handler from bus
                self._bus.remove_message_handler(proxy_interface._message_handler)

            # For now that InterfacesRemoved signal means the entire object is removed from D-Bus
            del self._subscriptions[bus_name].path_objects[path]

        # Cleanup the entire BusNameSubscriptions if no more objects are subscribed
        bus_name_subscriptions = self.get_bus_name_subscriptions(bus_name)
        if bus_name_subscriptions and len(bus_name_subscriptions.path_objects) == 0:
            del self._subscriptions[bus_name]

        # Trigger flows that have an object_removed trigger configured
        subscription_configs = self.config.get_subscription_configs(bus_name=bus_name, path=path)
        for subscription_config in subscription_configs:
            trigger_context = {"bus_name": bus_name, "path": path}
            await self._trigger_processor.trigger_subscription_flows(
                subscription_config,
                FlowTriggerHandler(FlowTriggerDbusObjectRemovedConfig.type, trigger_context)
            )

    async def _start_subscription_flows(self, bus_name: str, subscribed_interfaces: list[SubscribedInterface], trigger_flows: bool = True):
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

        logger.debug(f"_start_subscription_flows: new_subscriptions: {list(bus_name_object_paths.keys())}")
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

                # For each subscription_config that matches the bus_name and object_path
                subscription_configs = self.config.get_subscription_configs(bus_name, object_path)
                for subscription_config in subscription_configs:
                    trigger_context = {
                        "bus_name": bus_name,
                        "path": object_path
                    }

                    # Only process subscription_config once, no matter how many paths it matches
                    if subscription_config.id not in processed_new_subscriptions:

                        # Ensure all schedulers are started
                        # If a scheduler is already active for this subscription flow, it will be reused
                        self.flow_scheduler.start_flow_set(subscription_config.flows)

                        # Trigger flows that have a bus_name_added trigger configured
                        if trigger_flows:
                            # TODO: path arg doesn't make sense here, it did work for mpris however where there is only one path
                            # leaving it now for backwards compatibility
                            await self._trigger_processor.trigger_subscription_flows(
                                subscription_config,
                                FlowTriggerHandler(FlowTriggerBusNameAddedConfig.type, trigger_context)
                            )

                        processed_new_subscriptions.add(subscription_config.id)

                    if trigger_flows:
                        # Trigger flows that have a object_added trigger configured
                        await self._trigger_processor.trigger_subscription_flows(
                            subscription_config,
                            FlowTriggerHandler(FlowTriggerDbusObjectAddedConfig.type, trigger_context)
                        )

    async def call_dbus_interface_method(self, interface: dbus_aio.proxy_object.ProxyInterface, method: str, method_args: list[Any]) -> object:

        converted_args = convert_mqtt_args_to_dbus(method_args)
        call_method_name = "call_" + camel_to_snake(method)

        # In case of a payload that doesn't match the dbus signature type, this prints a better error message
        interface_method = next((m for m in interface.introspection.methods if m.name == method), None)
        if interface_method:
            in_signature_tree = SignatureTree(interface_method.in_signature)
            in_signature_tree.verify(converted_args)

        try:
            res = await self._dbus_interface_call(interface, call_method_name, *converted_args)
        except Exception as e:
            logger.debug(f"Error while calling dbus object, bus_name={interface.bus_name}, interface={interface.introspection.name}, method={method}, converted_args={converted_args}", exc_info=True)
            raise e

        if res:
            res = unwrap_dbus_object(res)

        logger.debug(f"call_dbus_interface_method: bus_name={interface.bus_name}, interface={interface.introspection.name}, method={method}, res={res}")

        return res

    async def get_dbus_interface_property(self, interface: dbus_aio.proxy_object.ProxyInterface, property: str) -> Any:

        call_method_name = "get_" + camel_to_snake(property)
        res = await self._dbus_interface_call(interface, call_method_name)
        if res:
            res = unwrap_dbus_object(res)

        logger.debug(f"get_dbus_interface_property: bus_name={interface.bus_name}, interface={interface.introspection.name}, property={property}, res={res}")

        return res

    async def set_dbus_interface_property(self, interface: dbus_aio.proxy_object.ProxyInterface, property: str, value: Any) -> None:

        call_method_name = "set_" + camel_to_snake(property)
        await self._dbus_interface_call(interface, call_method_name, value)

        logger.info(f"set_dbus_interface_property: bus_name={interface.bus_name}, interface={interface.introspection.name}, property={property}, value={value}")

    async def mqtt_receive_queue_processor_task(self):
        """Continuously processes messages from the async queue."""
        while True:
            msg, hints = await self.event_broker.mqtt_receive_queue.async_q.get()
            try:
                await self._on_mqtt_msg(msg, hints)
            except Exception as e:
                logger.warning(f"mqtt_receive_queue_processor_task: Exception: {e}", exc_info=True)
            finally:
                self.event_broker.mqtt_receive_queue.async_q.task_done()

    async def dbus_signal_queue_processor_task(self):
        """Continuously processes messages from the async queue."""
        while True:
            signal = await self._dbus_signal_queue.async_q.get()
            try:
                await self._handle_on_dbus_signal(signal)
            except Exception as e:
                logger.warning(f"dbus_signal_queue_processor_task: Exception: {e}", exc_info=True)
            finally:
                self._dbus_signal_queue.async_q.task_done()

    async def dbus_object_lifecycle_signal_processor_task(self):
        """Continuously processes messages from the async queue."""
        while True:
            message = await self._dbus_object_lifecycle_signal_queue.async_q.get()
            await self._handle_dbus_object_lifecycle_signal(message)
            self._dbus_object_lifecycle_signal_queue.async_q.task_done()

    async def _handle_on_dbus_signal(self, signal_state: DbusSignalWithState):

        signal_config = signal_state.signal_config
        signal = signal_state.signal_config.signal
        logger.debug(f"dbus_signal: signal={signal}, args={signal_state.args}, bus_name={signal_state.bus_name}, path={signal_state.path}, interface={signal_state.interface_name}")

        accept_signal = True

        # dbus signal subscriptions might have a filter configured
        if signal_config.filter is not None:
            accept_signal = signal_config.matches_filter(self.templating, *signal_state.args)

        if accept_signal:
            trigger_context = {
                "bus_name": signal_state.bus_name,
                "path": signal_state.path,
                "interface": signal_state.interface_name,
                "signal": signal_config.signal,
                "args": signal_state.args
            }
            flow_trigger_handler = FlowTriggerDbusSignalHandler(
                trigger_context=trigger_context,
                signal=signal_config.signal,
                interface=signal_state.interface_name
            )

            await self._trigger_processor.trigger_subscription_flows(
                signal_state.subscription_config,
                flow_trigger_handler,
            )

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

    def _has_subscription_configs_for_topic(self, topic: str):
        for subscription_configs in self.config.subscriptions:
            for interface_config in subscription_configs.interfaces:
                mqtt_topic = interface_config.render_mqtt_command_topic(self.templating, {})
                if mqtt_topic == topic:
                    return True
        return False

    def _get_matching_subscribed_interfaces(self, topic: str, bus_name_pattern: str, path_pattern: str):
        result: list[tuple[InterfaceConfig, dbus_aio.ProxyObject]] = []

        for bus_name_subscription in self._subscriptions.values():
            bus_name_matches = fnmatch.fnmatchcase(bus_name_subscription.bus_name, bus_name_pattern)
            if not bus_name_matches:
                continue

            for path, proxy_object in bus_name_subscription.path_objects.items():
                path_matches = fnmatch.fnmatchcase(path, path_pattern)
                if not path_matches:
                    continue

                subscription_configs = self.config.get_subscription_configs(bus_name=bus_name_subscription.bus_name, path=path)
                for subscription_configs in subscription_configs:
                    for interface_config in subscription_configs.interfaces:
                        mqtt_topic = interface_config.render_mqtt_command_topic(self.templating, {})
                        topic_matches = mqtt_topic == topic

                        if topic_matches:
                            result.append((interface_config, proxy_object))
        return result

    async def _on_mqtt_msg(self, msg: MqttMessage, hints: MqttReceiveHints):
        """Executes dbus method calls or property updates on objects.

        Only for messages which have:
          1. a matching subscription configured
          2. a matching method or property in the msg payload
          3. a matching bus_name (if provided)
          4. a matching path (if provided)
        """
        # Don't proceed or log any message if no matching configuration is found
        # where mqtt_command_topic matches the MQTT message topic. The MQTT msg is not intended for here
        if not self._has_subscription_configs_for_topic(msg.topic):
            return

        logger.debug(f"on_mqtt_msg: topic={msg.topic}, payload={json.dumps(msg.payload)}")

        payload_bus_name = msg.payload.get("bus_name") or "*"
        payload_path = msg.payload.get("path") or "*"

        payload_method = msg.payload.get("method")
        payload_method_args = msg.payload.get("args") or []

        payload_property = msg.payload.get("property")
        payload_value = msg.payload.get("value")

        # Must have either method or property/value in payload
        # If missing, it's likely a user error that should be logged
        if payload_method is None and (payload_property is None or payload_value is None):
            if msg.payload and hints.log_unmatched_message:
                logger.info(f"on_mqtt_msg: Unsupported payload, missing 'method' or 'property/value', got method={payload_method}, property={payload_property}, value={payload_value} from {msg.payload}")
            return

        matched_methods: list[tuple[dbus_aio.ProxyInterface, InterfaceConfig, MethodConfig]] = []
        matched_properties: list[tuple[dbus_aio.ProxyInterface, InterfaceConfig, PropertyConfig]] = []

        matching_interfaces = self._get_matching_subscribed_interfaces(msg.topic, payload_bus_name, payload_path)
        for interface_config, proxy_object in matching_interfaces:
            for method in interface_config.methods:
                # filter configured method, configured topic, ...
                if method.method == payload_method:
                    interface = proxy_object.get_interface(name=interface_config.interface)
                    matched_methods.append((interface, interface_config, method))

            for property in interface_config.properties:
                # filter configured property, configured topic, ...
                if property.property == payload_property:
                    interface = proxy_object.get_interface(name=interface_config.interface)
                    matched_properties.append((interface, interface_config, property))

        # Log if no method or property matched on any of the targeted interfaces
        if not matched_methods and not matched_properties and hints.log_unmatched_message:
            if payload_method:
                logger.info(f"No configured or active dbus subscriptions for topic={msg.topic}, method={payload_method}, bus_name={payload_bus_name}, path={payload_path}, active bus_names={list(self._subscriptions.keys())}")
            if payload_property:
                logger.info(f"No configured or active dbus subscriptions for topic={msg.topic}, property={payload_property}, bus_name={payload_bus_name}, path={payload_path}, active bus_names={list(self._subscriptions.keys())}")
            return

        # Call the requested method on each matched D-Bus interface and publish responses if configured
        for interface, interface_config, method in matched_methods:

            logger.info(f"on_mqtt_msg: method={method.method}, args={payload_method_args}, bus_name={interface.bus_name}, path={interface.path}, interface={interface_config.interface}")

            result = None
            error = None

            try:
                result = await self.call_dbus_interface_method(interface, method.method, payload_method_args)
            except Exception as e:
                error = e
                logger.warning(f"on_mqtt_msg: Failed calling method={method.method}, args={payload_method_args}, bus_name={interface.bus_name}, exception={e}")

            # Send success (or error) response if configured
            await self._send_mqtt_response(
                interface_config, result, error, interface.bus_name, interface.path,
                method=method.method, args=payload_method_args
            )

        # Set property values on each matched D-Bus interface and publish responses if configured
        for interface, interface_config, property in matched_properties:

            logger.info(f"on_mqtt_msg: property={property.property}, value={payload_value}, bus_name={interface.bus_name}, path={interface.path}, interface={interface_config.interface}")

            error = None

            try:
                await self.set_dbus_interface_property(interface, property.property, payload_value)
            except Exception as e:
                error = e
                logger.warning(f"on_mqtt_msg: property={property.property}, value={payload_value}, bus_name={interface.bus_name} failed, exception={e}")

            # Send success (or error) response if configured
            await self._send_mqtt_response(
                interface_config, payload_value, error, interface.bus_name, interface.path,
                property=property.property, value=[payload_value]
            )

    async def _send_mqtt_response(self, interface_config, result: Any, error: Exception | None, bus_name: str, path: str, *args, **kwargs):
        """Send MQTT response for a method call if response topic is configured.

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
