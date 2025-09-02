import pytest

from dbus2mqtt import AppContext
from dbus2mqtt.config import FlowActionContextSetConfig, FlowTriggerMqttMessageConfig
from dbus2mqtt.flow.flow_processor import FlowProcessor
from tests import mocked_app_context, mocked_flow_processor, mocked_mqtt_client


@pytest.mark.asyncio
async def test_mqtt_message_trigger():

    test_topic = "dbus2mqtt/test-topic"
    test_payload = {
        "action": "test-action",
    }
    trigger_config = FlowTriggerMqttMessageConfig(
        topic=test_topic,
        filter="{{ true }}"
    )

    app_context = mocked_app_context()
    processor =_mocked_flow_processor(app_context, trigger_config)
    mqtt_client = mocked_mqtt_client(app_context)

    mqtt_client._trigger_flows(topic=test_topic, trigger_context={
        "topic": test_topic,
        "payload": test_payload
    })

    trigger = app_context.event_broker.flow_trigger_queue.sync_q.get_nowait()

    # execute all flow actions
    await processor._process_flow_trigger(trigger)

    # expected context from _trigger_bus_name_added
    assert processor._global_context["res"] == {
        "trigger_type": "mqtt_message",
        "topic": test_topic,
        "payload": test_payload
    }

@pytest.mark.asyncio
async def test_mqtt_message_trigger_filter_true():

    test_topic = "dbus2mqtt/test-topic"
    test_payload = {
        "action": "test-action",
    }
    trigger_config = FlowTriggerMqttMessageConfig(
        topic=test_topic,
        filter="{{ true }}"
    )

    app_context = mocked_app_context()
    _ = _mocked_flow_processor(app_context, trigger_config)
    mqtt_client = mocked_mqtt_client(app_context)

    mqtt_client._trigger_flows(topic=test_topic, trigger_context={
        "topic": test_topic,
        "payload": test_payload
    })

    assert app_context.event_broker.flow_trigger_queue.sync_q.qsize() == 1

@pytest.mark.asyncio
async def test_mqtt_message_trigger_filter_false():

    test_topic = "dbus2mqtt/test-topic"
    test_payload = {
        "action": "test-action",
    }
    trigger_config = FlowTriggerMqttMessageConfig(
        topic=test_topic,
        filter="{{ false }}"
    )

    app_context = mocked_app_context()
    _ =_mocked_flow_processor(app_context, trigger_config)
    mqtt_client = mocked_mqtt_client(app_context)

    mqtt_client._trigger_flows(topic=test_topic, trigger_context={
        "topic": test_topic,
        "payload": test_payload
    })

    assert app_context.event_broker.flow_trigger_queue.sync_q.qsize() == 0

def _mocked_flow_processor(app_context: AppContext, trigger_config: FlowTriggerMqttMessageConfig) -> FlowProcessor:
    processor, _ = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionContextSetConfig(
            global_context={
                "res": {
                    "trigger_type": "{{ trigger_type }}",
                    "topic": "{{ topic }}",
                    "payload": "{{ payload }}"
                }
            }
        )
    ])

    return processor
