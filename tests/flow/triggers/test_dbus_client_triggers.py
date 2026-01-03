from unittest.mock import MagicMock

import pytest

from dbus2mqtt.config import (
    FlowActionContextSetConfig,
    FlowTriggerBusNameAddedConfig,
    FlowTriggerBusNameRemovedConfig,
    FlowTriggerDbusObjectAddedConfig,
    FlowTriggerDbusObjectRemovedConfig,
    FlowTriggerDbusSignalConfig,
    SignalConfig,
)
from dbus2mqtt.dbus.dbus_client import DbusClient
from dbus2mqtt.dbus.dbus_types import BusNameSubscriptions, DbusSignalWithState, SubscribedInterface
from tests import mocked_app_context, mocked_dbus_client, mocked_flow_processor


@pytest.mark.asyncio
async def test_bus_name_added_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerBusNameAddedConfig()
    processor, _ = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionContextSetConfig(
                global_context={
                    "res": {
                        "trigger_type": "{{ trigger_type }}",
                        "bus_name": "{{ bus_name }}",
                        "path": "{{ path }}",
                    }
                }
            )
        ],
    )

    object_bus_name = "test.bus_name.testapp"
    object_path = "/"

    dbus_client = _mocked_dbus_client_with_dbus_object(app_context, object_bus_name, object_path)

    # trigger dbus_client and capture the triggered message
    subscribed_interfaces = [
        SubscribedInterface(
            bus_name=object_bus_name,
            path=object_path,
            interface_name="test",
            subscription_config=app_context.config.dbus.subscriptions[0],
        )
    ]
    await dbus_client._start_subscription_flows(object_bus_name, subscribed_interfaces, True)

    trigger = app_context.event_broker.flow_trigger_queue.sync_q.get_nowait()

    # execute all flow actions
    await processor._process_flow_trigger(trigger)

    # expected context from _trigger_bus_name_added
    assert processor._global_context["res"] == {
        "trigger_type": "bus_name_added",
        "bus_name": object_bus_name,
        "path": object_path,
    }


@pytest.mark.asyncio
async def test_bus_name_removed_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerBusNameRemovedConfig()
    processor, _ = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionContextSetConfig(
                global_context={
                    "res": {
                        "trigger_type": "{{ trigger_type }}",
                        "bus_name": "{{ bus_name }}",
                        "path": "{{ path }}",
                    }
                }
            )
        ],
    )

    object_bus_name = "test.bus_name.testapp"
    object_path = "/"

    dbus_client = _mocked_dbus_client_with_dbus_object(app_context, object_bus_name, object_path)

    # trigger dbus_client and capture the triggered message
    await dbus_client._handle_bus_name_removed(object_bus_name)
    trigger = app_context.event_broker.flow_trigger_queue.sync_q.get_nowait()

    # execute all flow actions
    await processor._process_flow_trigger(trigger)

    # expected context from _trigger_bus_name_removed
    assert processor._global_context["res"] == {
        "trigger_type": "bus_name_removed",
        "bus_name": object_bus_name,
        "path": object_path,
    }


@pytest.mark.asyncio
async def test_object_added_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerDbusObjectAddedConfig()
    processor, _ = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionContextSetConfig(
                global_context={
                    "res": {
                        "trigger_type": "{{ trigger_type }}",
                        "bus_name": "{{ bus_name }}",
                        "path": "{{ path }}",
                    }
                }
            )
        ],
    )

    object_bus_name = "org.mpris.MediaPlayer2.vlc"
    object_path = "/org/mpris/MediaPlayer2"

    subscription = app_context.config.dbus.subscriptions[0]
    subscription.bus_name = object_bus_name
    subscription.path = object_path

    dbus_client = _mocked_dbus_client_with_dbus_object(app_context, object_bus_name, object_path)

    # trigger dbus_client and capture the triggered message
    subscribed_interfaces = [
        SubscribedInterface(
            bus_name=object_bus_name,
            path=object_path,
            interface_name="test",
            subscription_config=app_context.config.dbus.subscriptions[0],
        )
    ]
    await dbus_client._start_subscription_flows(object_bus_name, subscribed_interfaces, True)

    trigger = app_context.event_broker.flow_trigger_queue.sync_q.get_nowait()

    # execute all flow actions
    await processor._process_flow_trigger(trigger)

    # expected context from _trigger_object_added
    assert processor._global_context["res"] == {
        "trigger_type": "dbus_object_added",
        "bus_name": object_bus_name,
        "path": object_path,
    }


@pytest.mark.asyncio
async def test_object_removed_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerDbusObjectRemovedConfig()
    processor, _ = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionContextSetConfig(
                global_context={
                    "res": {
                        "trigger_type": "{{ trigger_type }}",
                        "bus_name": "{{ bus_name }}",
                        "path": "{{ path }}",
                    }
                }
            )
        ],
    )

    object_bus_name = "test.bus_name.testapp"
    object_path = "/"

    dbus_client = _mocked_dbus_client_with_dbus_object(app_context, object_bus_name, object_path)

    # trigger dbus_client and capture the triggered message
    await dbus_client._handle_interfaces_removed(object_bus_name, object_path)

    trigger = app_context.event_broker.flow_trigger_queue.sync_q.get_nowait()

    # execute all flow actions
    await processor._process_flow_trigger(trigger)

    # expected context from _trigger_object_removed
    assert processor._global_context["res"] == {
        "trigger_type": "dbus_object_removed",
        "bus_name": object_bus_name,
        "path": object_path,
    }


@pytest.mark.asyncio
async def test_dbus_signal_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerDbusSignalConfig(
        interface="test-interface-name", signal="TestSignal"
    )
    processor, _ = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionContextSetConfig(
                global_context={
                    "res": {
                        "trigger_type": "{{ trigger_type }}",
                        "bus_name": "{{ bus_name }}",
                        "path": "{{ path }}",
                        "interface": "{{ interface }}",
                        "signal": "{{ signal }}",
                        "args": "{{ args }}",
                    }
                }
            )
        ],
    )

    subscription_config = app_context.config.dbus.subscriptions[0]

    object_bus_name = "test.bus_name.testapp"
    object_path = "/"

    dbus_client = _mocked_dbus_client_with_dbus_object(app_context, object_bus_name, object_path)

    signal = DbusSignalWithState(
        bus_name=object_bus_name,
        path=object_path,
        interface_name=subscription_config.interfaces[0].interface,
        subscription_config=subscription_config,
        signal_config=SignalConfig(signal="TestSignal"),
        args=["first-arg", "second-arg"],
    )

    # trigger dbus_client and capture the triggered message
    await dbus_client._handle_on_dbus_signal(signal)
    trigger = app_context.event_broker.flow_trigger_queue.sync_q.get_nowait()

    # execute all flow actions
    await processor._process_flow_trigger(trigger)

    # validate results
    assert processor._global_context["res"] == {
        "trigger_type": "dbus_signal",
        "bus_name": object_bus_name,
        "path": "/",
        "interface": "test-interface-name",
        "signal": "TestSignal",
        "args": ["first-arg", "second-arg"],
    }


@pytest.mark.asyncio
async def test_dbus_signal_interface_matcher():

    app_context = mocked_app_context()

    _, _ = mocked_flow_processor(
        app_context,
        triggers=[
            FlowTriggerDbusSignalConfig(signal="TestSignal", interface="test-wrong-interface")
        ],
        actions=[
            FlowActionContextSetConfig(
                global_context={
                    "res": {
                        "trigger_type": "{{ trigger_type }}",
                    }
                }
            )
        ],
    )

    subscription_config = app_context.config.dbus.subscriptions[0]
    dbus_client = mocked_dbus_client(app_context)

    bus_name = "test.bus_name.testapp"
    dbus_client._subscriptions[bus_name] = BusNameSubscriptions(bus_name, ":1.1")

    signal = DbusSignalWithState(
        bus_name=bus_name,
        path="/",
        interface_name=subscription_config.interfaces[0].interface,
        subscription_config=subscription_config,
        signal_config=SignalConfig(signal="TestSignal"),
        args=[],
    )

    # trigger dbus_client and capture the triggered message
    await dbus_client._handle_on_dbus_signal(signal)

    # no flow trigger messages must exist on the queue as the interface filter did not match
    assert app_context.event_broker.flow_trigger_queue.sync_q.qsize() == 0


@pytest.mark.asyncio
async def test_dbus_signal_filter():

    app_context = mocked_app_context()

    _, _ = mocked_flow_processor(
        app_context,
        triggers=[FlowTriggerDbusSignalConfig(signal="TestSignal")],
        actions=[
            FlowActionContextSetConfig(
                global_context={
                    "res": {
                        "trigger_type": "{{ trigger_type }}",
                    }
                }
            )
        ],
    )

    # this is the filter want to test
    subscription_signal_config = SignalConfig(signal="TestSignal", filter="{{ False }}")

    subscription_config = app_context.config.dbus.subscriptions[0]
    dbus_client = mocked_dbus_client(app_context)

    bus_name = "test.bus_name.testapp"
    dbus_client._subscriptions[bus_name] = BusNameSubscriptions(bus_name, ":1.1")

    signal = DbusSignalWithState(
        bus_name=bus_name,
        path="/",
        interface_name=subscription_config.interfaces[0].interface,
        subscription_config=subscription_config,
        signal_config=subscription_signal_config,
        args=[],
    )

    # trigger dbus_client and capture the triggered message
    await dbus_client._handle_on_dbus_signal(signal)

    # no flow trigger messages must exist on the queue as the interface filter did not match
    assert app_context.event_broker.flow_trigger_queue.sync_q.qsize() == 0


def _mocked_dbus_client_with_dbus_object(app_context, bus_name: str, path: str) -> DbusClient:

    dbus_client = mocked_dbus_client(app_context)

    dbus_client._subscriptions[bus_name] = BusNameSubscriptions(bus_name, ":1.1")
    mocked_proxy_object = MagicMock()
    mocked_proxy_object.get_interface.return_value = MagicMock()

    dbus_client._subscriptions[bus_name].path_objects[path] = mocked_proxy_object

    return dbus_client
