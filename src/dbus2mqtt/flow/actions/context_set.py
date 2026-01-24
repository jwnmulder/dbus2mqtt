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
            context_new = await self.templating.async_render_template(
                self.config.global_context, dict, aggregated_context
            )
            logger.debug(f"Update global_context with: {context_new}")
            context.update_global_context(context_new)

        if self.config.dbus_object_context is not None:
            if context._dbus_object_context is not None:
                context_new = await self.templating.async_render_template(
                    self.config.dbus_object_context, dict, aggregated_context
                )
                logger.debug(
                    f"Update dbus_object_context[{context._dbus_object_ref}] with: {context_new}"
                )
                context.update_dbus_object_context(context_new)
            else:
                logger.warning(
                    "Skipped updating dbus_object_context, not in a valid dbus_object_context"
                )

        if self.config.context:
            context_new = await self.templating.async_render_template(
                self.config.context, dict, aggregated_context
            )
            logger.debug(f"Update context with: {context_new}")
            context.update_context(context_new)
