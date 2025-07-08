import logging

from jinja2.exceptions import TemplateError

from dbus2mqtt import AppContext
from dbus2mqtt.config import FlowActionDbusCallConfig
from dbus2mqtt.flow import FlowAction, FlowExecutionContext
from dbus2mqtt.mqtt.mqtt_client import MqttMessage

logger = logging.getLogger(__name__)

class DbusCallAction(FlowAction):

    def __init__(self, config: FlowActionDbusCallConfig, app_context: AppContext):
        self.config = config
        self.templating = app_context.templating
        self.app_context = app_context

    async def execute(self, context: FlowExecutionContext):

        render_context = context.get_aggregated_context()

        action_params = {
            "bus_name": self.config.bus_name,
            "path": self.config.path,
            "interface": self.config.interface,
            "method": self.config.method,
            "args": self.config.args
        }

        try:
            action_params = self.templating.render_template(action_params, context=render_context, res_type=dict)

        except TemplateError as e:
            logger.warning(f"Error rendering jinja template, flow: '{context.name or ''}', msg={e}, action_params={action_params}, render_context={render_context}", exc_info=True)
            return

        self.app_context.event_broker.on_mqtt_receive(MqttMessage("dbus2mqtt/org.mpris.MediaPlayer2/command", action_params))
