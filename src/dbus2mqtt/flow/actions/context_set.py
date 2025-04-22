import logging

from dbus2mqtt import AppContext
from dbus2mqtt.config import FlowActionContextSetConfig
from dbus2mqtt.flow import FlowAction, FlowExecutionContext

logger = logging.getLogger(__name__)

class ContextSetAction(FlowAction):

    def __init__(self, config: FlowActionContextSetConfig, app_context: AppContext):
        self.config = config
        self.templating = app_context.templating

    async def execute(self, context: FlowExecutionContext):

        aggregated_context = context.get_aggregated_context()

        if self.config.global_context:
            context_new = await self.templating.async_render_template(self.config.global_context, dict, aggregated_context)
            logger.debug(f"Update global_context with: {context_new}")
            context.global_flows_context.update(context_new)

        if self.config.context:

            context_new = await self.templating.async_render_template(self.config.context, dict, aggregated_context)
            logger.debug(f"Update context with: {context_new}")
            context.context.update(context_new)
