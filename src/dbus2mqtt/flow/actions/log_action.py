
import logging

from jinja2.exceptions import TemplateError

from dbus2mqtt import AppContext
from dbus2mqtt.config import FlowActionLogConfig
from dbus2mqtt.flow import FlowAction, FlowExecutionContext

logger = logging.getLogger(__name__)

class LogAction(FlowAction):

    def __init__(self, config: FlowActionLogConfig, app_context: AppContext):
        self.config = config
        self.templating = app_context.templating

    async def execute(self, context: FlowExecutionContext):

        render_context = context.get_aggregated_context()

        log_msg = self.config.msg
        log_level = logging._nameToLevel.get(self.config.level.upper(), logging.INFO)

        try:
            log_msg = await self.templating.async_render_template(
                templatable=self.config.msg,
                context=render_context,
                res_type=str
            )

        except TemplateError as e:
            logger.warning(f"Error rendering jinja template, flow: '{context.name or ''}', msg={e}, msg={self.config.msg}, render_context={render_context}", exc_info=True)
            return

        logger.log(level=log_level, msg=log_msg)
