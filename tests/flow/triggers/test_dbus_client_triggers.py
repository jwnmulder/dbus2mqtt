import pytest

from dbus2mqtt.config import (
    FlowActionContextSetConfig,
    FlowTriggerBusNameAddedConfig,
    FlowTriggerBusNameRemovedConfig,
    FlowTriggerDbusSignalConfig,
    SignalConfig,
)
from dbus2mqtt.event_broker import DbusSignalWithState
from tests import mocked_app_context, mocked_dbus_client, mocked_flow_processor


@pytest.mark.asyncio
async def test_bus_name_added_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerBusNameAddedConfig()
    processor, _ = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionContextSetConfig(
            global_context={
                "res": {
                    "bus_name": "{{ bus_name }}"
                }
            }
        )
    ])

    dbus_client = mocked_dbus_client(app_context)

    subscription_config = app_context.config.dbus.subscriptions[0]

    # trigger dbus_client and capture the triggered message
    await dbus_client._trigger_bus_name_added(subscription_config, "test-bus-name")
    trigger = app_context.event_broker.flow_trigger_queue.sync_q.get_nowait()

    # execute all flow actions
    await processor._process_flow_trigger(trigger)

    # expected context from _trigger_bus_name_added
    assert processor._global_context["res"] == {
        "bus_name": "test-bus-name",
    }

@pytest.mark.asyncio
async def test_bus_name_removed_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerBusNameRemovedConfig()
    processor, _ = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionContextSetConfig(
            global_context={
                "res": {
                    "bus_name": "{{ bus_name }}"
                }
            }
        )
    ])

    dbus_client = mocked_dbus_client(app_context)

    subscription_config = app_context.config.dbus.subscriptions[0]

    # trigger dbus_client and capture the triggered message
    await dbus_client._trigger_bus_name_removed(subscription_config, "test-bus-name")
    trigger = app_context.event_broker.flow_trigger_queue.sync_q.get_nowait()

    # execute all flow actions
    await processor._process_flow_trigger(trigger)

    # expected context from _trigger_bus_name_added
    assert processor._global_context["res"] == {
        "bus_name": "test-bus-name",
    }

@pytest.mark.asyncio
async def test_dbus_signal_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerDbusSignalConfig(
        interface="test-interface-name",
        signal="TestSignal"
    )
    processor, _ = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionContextSetConfig(
            global_context={
                "res": {
                    "bus_name": "{{ bus_name }}",
                    "path": "{{ path }}",
                    "interface": "{{ interface }}",
                    "args": "{{ args }}"
                }
            }
        )
    ])

    subscription_config = app_context.config.dbus.subscriptions[0]

    dbus_client = mocked_dbus_client(app_context)

    signal = DbusSignalWithState(
        bus_name="test-bus-name",
        path="/",
        interface_name=subscription_config.interfaces[0].interface,
        subscription_config=subscription_config,
        signal_config=SignalConfig(signal="TestSignal"),
        args=[
            "first-arg",
            "second-arg"
        ]
    )

    # trigger dbus_client and capture the triggered message
    await dbus_client._handle_on_dbus_signal(signal)
    trigger = app_context.event_broker.flow_trigger_queue.sync_q.get_nowait()

    # execute all flow actions
    await processor._process_flow_trigger(trigger)

    # validate results
    assert processor._global_context["res"] == {
        "bus_name": "test-bus-name",
        "path": "/",
        "interface": "test-interface-name",
        "args": ["first-arg", "second-arg"]
    }
