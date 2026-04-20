from datetime import datetime

import pytest

from dbus2mqtt.config import (
    FlowActionContextSetConfig,
    FlowTriggerContextChangedConfig,
    FlowTriggerScheduleConfig,
)
from dbus2mqtt.flow.flow_processor import FlowTriggerMessage
from tests import mocked_app_context, mocked_flow_processor


@pytest.mark.asyncio
async def test_context_changed():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerScheduleConfig()
    processor, flow_config = mocked_flow_processor(
        app_context,
        triggers=[trigger_config, FlowTriggerContextChangedConfig()],
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

    # Flow will be first triggered by the schedule trigger
    # Afterwards, we expect a context_changed trigger to be prepared for the same flow
    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now(), {})
    )

    # First execution should be triggered by schedule
    assert app_context.flow_state.global_context["res"] == {"trigger_type": "schedule"}

    # Global context changed, so a new trigger message must be on the event_broker
    context_changed_trigger = app_context.event_broker.flow_trigger_queue.sync_q.get_nowait()

    assert context_changed_trigger is not None
    assert context_changed_trigger.trigger_context == {"scope": "global"}
