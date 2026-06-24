from datetime import datetime

import pytest

from dbus2mqtt.config import (
    FlowActionContextSetConfig,
    FlowActionMqttPublishConfig,
    FlowTriggerDbusObjectAddedConfig,
    FlowTriggerScheduleConfig,
)
from dbus2mqtt.flow.flow_processor import FlowTriggerMessage
from tests import mocked_app_context, mocked_flow_processor


@pytest.mark.asyncio
async def test_context():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerScheduleConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionContextSetConfig(context={"var1": "{{ subscription_bus_name }}"}),
            FlowActionMqttPublishConfig(
                topic="dbus2mqtt/test", payload_type="text", payload_template="{{ var1 }}"
            ),
        ],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), {})
    )

    mqtt_message = app_context.event_broker.mqtt_publish_queue.sync_q.get_nowait()

    assert mqtt_message is not None
    assert mqtt_message.payload == "test.bus_name.*"


@pytest.mark.asyncio
async def test_global_context():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerScheduleConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionContextSetConfig(global_context={"var1": "{{ subscription_bus_name }}"})
        ],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), {})
    )

    assert app_context.flow_state.global_context["var1"] == "test.bus_name.*"


@pytest.mark.asyncio
async def test_object_context():

    app_context = mocked_app_context()

    trigger_context = {"bus_name": "test_bus_name", "path": "/"}
    trigger_config = FlowTriggerDbusObjectAddedConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        triggers=[trigger_config],
        actions=[
            FlowActionContextSetConfig(object_context={"var1": "{{ subscription_bus_name }}"})
        ],
    )

    flow_trigger_message = FlowTriggerMessage(
        flow_config, trigger_config, datetime.now(), trigger_context
    )
    object_context_ref = processor._execution_object_context_ref(flow_config, flow_trigger_message)

    assert object_context_ref

    await processor._process_flow_trigger(flow_trigger_message)

    object_context = app_context.flow_state.object_contexts[object_context_ref]

    assert object_context["var1"] == "test.bus_name.*"
