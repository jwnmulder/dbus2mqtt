import pytest

from dbus2mqtt.config import (
    FlowActionContextSetConfig,
    FlowTriggerContextChangedConfig,
)
from dbus2mqtt.flow.actions.context_set import ContextSetAction, FlowExecutionContext
from tests import mocked_app_context, mocked_flow_processor


@pytest.mark.asyncio
async def test_context_changed():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerContextChangedConfig()
    processor, _ = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionContextSetConfig(
            global_context={
                "res": {
                    "trigger_type": "{{ trigger_type }}",
                    "scope": "{{ scope }}",
                }
            }
        )
    ])

    context_set_config = FlowActionContextSetConfig(
        global_context={
            "some_key": "some_value"
        }
    )
    action = ContextSetAction(context_set_config, app_context)

    # call actions which should trigger the flow
    context = FlowExecutionContext(None, {}, {})
    await action.execute(context)

    trigger = app_context.event_broker.flow_trigger_queue.sync_q.get_nowait()

    # execute all flow actions
    await processor._process_flow_trigger(trigger)

    # expected context from _trigger_bus_name_added
    assert processor._global_context["res"] == {
        "trigger_type": "context_changed",
        "scope": "global",
    }
