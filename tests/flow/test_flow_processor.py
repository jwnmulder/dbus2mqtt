from datetime import datetime

import pytest

from dbus2mqtt.config import (
    FlowActionContextSetConfig,
    FlowTriggerBusNameAddedConfig,
    FlowTriggerBusNameRemovedConfig,
    FlowTriggerDbusSignalConfig,
    FlowTriggerObjectAddedConfig,
    FlowTriggerObjectRemovedConfig,
    FlowTriggerScheduleConfig,
)
from dbus2mqtt.flow.flow_processor import FlowTriggerMessage
from tests import mocked_app_context, mocked_flow_processor


@pytest.mark.asyncio
async def test_schedule_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerScheduleConfig()
    processor, flow_config = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionContextSetConfig(
            global_context={
                "res": "scheduler"
            }
        )
    ])

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now())
    )

    assert processor._global_context["res"] == "scheduler"

@pytest.mark.asyncio
async def test_bus_name_added_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerBusNameAddedConfig()
    processor, flow_config = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionContextSetConfig(
            global_context={
                "res": "added"
            }
        )
    ])

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now())
    )

    assert processor._global_context["res"] == "added"

@pytest.mark.asyncio
async def test_bus_name_removed_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerBusNameRemovedConfig()
    processor, flow_config = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionContextSetConfig(
            global_context={
                "res": "removed"
            }
        )
    ])

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now())
    )

    assert processor._global_context["res"] == "removed"

@pytest.mark.asyncio
async def test_object_added_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerObjectAddedConfig()
    processor, flow_config = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionContextSetConfig(
            global_context={
                "res": "added"
            }
        )
    ])

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now())
    )

    assert processor._global_context["res"] == "added"

@pytest.mark.asyncio
async def test_object_removed_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerObjectRemovedConfig()
    processor, flow_config = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionContextSetConfig(
            global_context={
                "res": "removed"
            }
        )
    ])

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now())
    )

    assert processor._global_context["res"] == "removed"

@pytest.mark.asyncio
async def test_dbus_signal_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerDbusSignalConfig(
        interface="org.freedesktop.DBus.Properties",
        signal="PropertiesChanged"
    )
    processor, flow_config = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionContextSetConfig(
            global_context={
                "res": {
                    "trigger": "dbus_signal",
                    "subscription_bus_name": "{{ subscription_bus_name }}",
                    "subscription_path": "{{ subscription_path }}",
                    "subscription_interfaces": "{{ subscription_interfaces }}"
                }
            }
        )
    ])

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now())
    )

    assert processor._global_context["res"] == {
        "trigger": "dbus_signal",
        "subscription_bus_name": "test.bus_name.*",
        "subscription_path": "/",
        "subscription_interfaces": ["test-interface-name"]
    }

# @pytest.mark.asyncio
# async def test_mqtt_trigger():

#     app_context = mocked_app_context()

#     trigger_config = FlowTriggerMqttConfig()
#     processor, flow_config = mocked_flow_processor(app_context, trigger_config, actions=[
#         FlowActionContextSetConfig(
#             global_context={
#                 "res": "mqtt"
#             }
#         )
#     ])

#     await processor._process_flow_trigger(
#         FlowTriggerMessage(flow_config, trigger_config, datetime.now())
#     )

#     assert processor._global_context["res"] == "mqtt"
