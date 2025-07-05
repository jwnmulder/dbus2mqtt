
import logging

from urllib.parse import urlparse

from jinja2.exceptions import TemplateError

from dbus2mqtt import AppContext
from dbus2mqtt.config import FlowActionMqttPublishConfig
from dbus2mqtt.flow import FlowAction, FlowExecutionContext
from dbus2mqtt.mqtt.mqtt_client import MqttMessage

logger = logging.getLogger(__name__)

class MqttPublishAction(FlowAction):

    def __init__(self, config: FlowActionMqttPublishConfig, app_context: AppContext):
        self.config = config
        self.event_broker = app_context.event_broker
        self.templating = app_context.templating

    async def execute(self, context: FlowExecutionContext):

        render_context = context.get_aggregated_context()

        try:
            mqtt_topic = await self.templating.async_render_template(self.config.topic, str, render_context)

            if self.config.payload_type == "text":
                res_type = str
            elif self.config.payload_type == "binary":
                res_type = str
            else:
                res_type = dict

            payload = await self.templating.async_render_template(self.config.payload_template, res_type, render_context)

            # for binary payloads, payload contains the file to read binary data from
            if isinstance(payload, str) and self.config.payload_type == "binary":
                uri = payload
                payload = urlparse(uri)
                if not payload.scheme == "file":
                    raise ValueError(f"Expected readable file, got: '{uri}'")


        except TemplateError as e:
            logger.warning(f"Error rendering jinja template, flow: '{context.name or ''}', msg={e}, payload_template={self.config.payload_template}, render_context={render_context}", exc_info=True)
            return
        except Exception as e:
            # Dont log full exception info to avoid log spamming on dbus errors
            # due to clients disconnecting
            logger.warning(f"Error rendering jinja template, flow: '{context.name or ''}', msg={e} payload_template={self.config.payload_template}, render_context={render_context}")
            return

        logger.debug(f"public_mqtt: flow={context.name}, payload={payload}")

        await self.event_broker.publish_to_mqtt(MqttMessage(mqtt_topic, payload, payload_serialization_type=self.config.payload_type))
