from datetime import datetime

import pytest

from dbus2mqtt.config import (
    FlowActionContextSetConfig,
    FlowTriggerBusNameAddedConfig,
    FlowTriggerBusNameRemovedConfig,
    FlowTriggerContextChangedConfig,
    FlowTriggerDbusObjectAddedConfig,
    FlowTriggerDbusObjectRemovedConfig,
    FlowTriggerDbusSignalConfig,
    FlowTriggerScheduleConfig,
)
from dbus2mqtt.flow.flow_processor import FlowTriggerMessage
from tests import mocked_app_context, mocked_flow_processor


@pytest.mark.asyncio
async def test_schedule_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerScheduleConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[FlowActionContextSetConfig(global_context={"res": "scheduler"})],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), {})
    )

    assert app_context.flow_state.global_context["res"] == "scheduler"


@pytest.mark.asyncio
async def test_bus_name_added_trigger():

    app_context = mocked_app_context()

    trigger_context = {"bus_name": "test_bus_name", "path": "/"}
    trigger_config = FlowTriggerBusNameAddedConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[FlowActionContextSetConfig(global_context={"res": "added"})],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), trigger_context)
    )

    assert app_context.flow_state.global_context["res"] == "added"


@pytest.mark.asyncio
async def test_bus_name_removed_trigger():

    app_context = mocked_app_context()

    trigger_context = {"bus_name": "test_bus_name", "path": "/"}
    trigger_config = FlowTriggerBusNameRemovedConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[FlowActionContextSetConfig(global_context={"res": "removed"})],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), trigger_context)
    )

    assert app_context.flow_state.global_context["res"] == "removed"


@pytest.mark.asyncio
async def test_object_added_trigger():

    app_context = mocked_app_context()

    trigger_context = {"bus_name": "test_bus_name", "path": "/"}
    trigger_config = FlowTriggerDbusObjectAddedConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[FlowActionContextSetConfig(global_context={"res": "added"})],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), trigger_context)
    )

    assert app_context.flow_state.global_context["res"] == "added"


@pytest.mark.asyncio
async def test_object_removed_trigger():

    app_context = mocked_app_context()

    trigger_context = {"bus_name": "test_bus_name", "path": "/"}
    trigger_config = FlowTriggerDbusObjectRemovedConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[FlowActionContextSetConfig(global_context={"res": "removed"})],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), trigger_context)
    )

    assert app_context.flow_state.global_context["res"] == "removed"


@pytest.mark.asyncio
async def test_dbus_signal_trigger():

    app_context = mocked_app_context()

    trigger_context = {"bus_name": "test_bus_name", "path": "/"}
    trigger_config = FlowTriggerDbusSignalConfig(
        interface="org.freedesktop.DBus.Properties", signal="PropertiesChanged"
    )
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionContextSetConfig(
                global_context={
                    "res": {
                        "trigger": "dbus_signal",
                        "subscription_bus_name": "{{ subscription_bus_name }}",
                        "subscription_path": "{{ subscription_path }}",
                        "subscription_interfaces": "{{ subscription_interfaces }}",
                    }
                }
            )
        ],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), trigger_context)
    )

    assert app_context.flow_state.global_context["res"] == {
        "trigger": "dbus_signal",
        "subscription_bus_name": "test.bus_name.*",
        "subscription_path": "/",
        "subscription_interfaces": ["test-interface-name"],
    }


@pytest.mark.asyncio
async def test_context_changed_trigger():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerContextChangedConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionContextSetConfig(global_context={"res": "triggered_by_context_changed"})
        ],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), {})
    )

    assert app_context.flow_state.global_context["res"] == "triggered_by_context_changed"


@pytest.mark.asyncio
async def test_flow_conditions_should_execute():

    app_context = mocked_app_context()

    trigger_context = {"bus_name": "test_bus_name", "path": "/"}
    trigger_config = FlowTriggerDbusObjectAddedConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionContextSetConfig(global_context={"res": "triggered_by_context_changed"})
        ],
        conditions=["{{ True }}"],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), trigger_context)
    )

    assert "res" in app_context.flow_state.global_context


@pytest.mark.asyncio
async def test_flow_conditions_should_not_execute():

    app_context = mocked_app_context()

    trigger_context = {"bus_name": "test_bus_name", "path": "/"}
    trigger_config = FlowTriggerDbusObjectAddedConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionContextSetConfig(global_context={"res": "triggered_by_context_changed"})
        ],
        conditions=["{{ False }}"],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), trigger_context)
    )

    assert "res" not in app_context.flow_state.global_context


@pytest.mark.asyncio
async def test_cleanup_object_context():
    """Test handling of object_removed_trigger and context cleanup."""
    app_context = mocked_app_context()

    trigger_context = {"bus_name": "test_bus_name", "path": "/"}
    trigger_config = FlowTriggerDbusObjectRemovedConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[],
    )

    flow_trigger_messsage = FlowTriggerMessage(
        flow_config, trigger_config, datetime.now(), trigger_context
    )
    object_context_ref = processor._object_context_ref_from_trigger(flow_trigger_messsage)

    assert object_context_ref

    app_context.flow_state.object_contexts[object_context_ref] = {"existing_var": "val"}
    await processor._process_flow_trigger(flow_trigger_messsage)

    assert object_context_ref not in app_context.flow_state.object_contexts
