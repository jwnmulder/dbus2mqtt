import logging

from datetime import datetime

from dbus2mqtt import AppContext
from dbus2mqtt.config import (
    FlowActionContextSetConfig,
    FlowConfig,
    FlowTriggerContextChangedConfig,
)
from dbus2mqtt.event_broker import FlowTriggerMessage
from dbus2mqtt.flow import FlowAction, FlowExecutionContext

logger = logging.getLogger(__name__)

class ContextSetAction(FlowAction):

    def __init__(self, config: FlowActionContextSetConfig, app_context: AppContext):
        self.config = config
        self.app_context = app_context
        self.event_broker = app_context.event_broker
        self.templating = app_context.templating

    async def execute(self, context: FlowExecutionContext):

        aggregated_context = context.get_aggregated_context()

        if self.config.global_context:
            context_new = await self.templating.async_render_template(self.config.global_context, dict, aggregated_context)
            logger.debug(f"Update global_context with: {context_new}")
            context.global_flows_context.update(context_new)

            await self._trigger_context_changed(context, {"scope": "global"})

        if self.config.context:

            context_new = await self.templating.async_render_template(self.config.context, dict, aggregated_context)
            logger.debug(f"Update context with: {context_new}")
            context.context.update(context_new)

    async def _trigger_context_changed(self, context: FlowExecutionContext, trigger_context: dict):
        """Trigger all flows that have a context_changed defined."""
        # TODO: Trigger at end of flow processing
        flow_trigger_messages = []

        all_flows: list[FlowConfig] = []
        all_flows.extend(self.app_context.config.flows)
        for subscription in self.app_context.config.dbus.subscriptions:
            all_flows.extend(subscription.flows)

        for flow in all_flows:
            for trigger in flow.triggers:
                if trigger.type == FlowTriggerContextChangedConfig.type:
                    trigger_message = FlowTriggerMessage(
                        flow,
                        trigger,
                        datetime.now(),
                        trigger_context=trigger_context,
                    )

                    flow_trigger_messages.append(trigger_message)
                    self.event_broker.flow_trigger_queue.sync_q.put(trigger_message)

        return flow_trigger_messages
