
import dbus_next.aio as dbus_aio
import pytest

from dbus2mqtt import AppContext
from dbus2mqtt.config import (
    FlowActionContextSetConfig,
    FlowTriggerBusNameAddedConfig,
    FlowTriggerBusNameRemovedConfig,
    FlowTriggerDbusSignalConfig,
    SignalConfig,
)
from dbus2mqtt.dbus.dbus_client import DbusClient
from dbus2mqtt.event_broker import DbusSignalWithState
from dbus2mqtt.flow.flow_processor import FlowScheduler
from tests import mocked_app_context, mocked_flow_processor


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

    dbus_client = _mocked_dbus_client(app_context)

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

    dbus_client = _mocked_dbus_client(app_context)

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

    dbus_client = _mocked_dbus_client(app_context)

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

class MockedMessageBus(dbus_aio.message_bus.MessageBus):
    def _setup_socket(self):
        self._stream = ""
        self._sock = ""
        self._fd = ""

def _mocked_dbus_client(app_context: AppContext):

    bus = MockedMessageBus(bus_address="unix:path=/run/user/1000/bus")
    flow_scheduler = FlowScheduler(app_context)

    dbus_client = DbusClient(app_context, bus, flow_scheduler)
    return dbus_client
