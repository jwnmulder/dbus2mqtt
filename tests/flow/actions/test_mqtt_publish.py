from datetime import datetime

import pytest

from dbus2mqtt.config import FlowActionMqttPublishConfig, FlowTriggerScheduleConfig
from dbus2mqtt.flow.flow_processor import FlowTriggerMessage
from tests import mocked_app_context, mocked_flow_processor


@pytest.mark.asyncio
async def test_mqtt_publish_action():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerScheduleConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        [trigger_config],
        actions=[
            FlowActionMqttPublishConfig(
                topic="dbus2mqtt/test", payload_template='{"test-key": "test-value"}'
            )
        ],
    )

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now())
    )

    mqtt_message = app_context.event_broker.mqtt_publish_queue.sync_q.get_nowait()

    assert mqtt_message is not None
    assert mqtt_message.payload_serialization_type == "json"

    payload: dict = mqtt_message.payload
    assert payload["test-key"] == "test-value"
