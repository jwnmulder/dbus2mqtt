from datetime import datetime

import pytest

from dbus2mqtt.config import (
    FlowActionLogConfig,
    FlowTriggerScheduleConfig,
)
from dbus2mqtt.flow.flow_processor import FlowTriggerMessage
from tests import mocked_app_context, mocked_flow_processor


@pytest.mark.asyncio
async def test_context():

    app_context = mocked_app_context()

    trigger_config = FlowTriggerScheduleConfig()
    processor, flow_config = mocked_flow_processor(app_context, trigger_config, actions=[
        FlowActionLogConfig(
            msg="{{ 'templated-test-str' }}",
            level="INFO"
        )
    ])

    await processor._process_flow_trigger(
        FlowTriggerMessage(flow_config, trigger_config, datetime.now())
    )
