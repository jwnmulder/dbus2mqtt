import asyncio
import json
import logging
import random
import string

from typing import Any, Literal
from urllib.parse import ParseResult
from urllib.request import urlopen

import paho.mqtt.client as mqtt
import yaml

from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
from paho.mqtt.subscribeoptions import SubscribeOptions

from dbus2mqtt import AppContext
from dbus2mqtt.config import FlowConfig, FlowTriggerMqttMessageConfig
from dbus2mqtt.event_broker import MqttMessage, MqttReceiveHints
from dbus2mqtt.flow.flow_trigger_handlers import FlowTriggerMqttMessageHandler
from dbus2mqtt.flow.flow_trigger_processor import FlowTriggerProcessor

logger = logging.getLogger(__name__)


class MqttClient:
    def __init__(self, app_context: AppContext, loop):
        self.app_context = app_context
        self.config = app_context.config.mqtt
        self.event_broker = app_context.event_broker

        self._trigger_processor = FlowTriggerProcessor(app_context)

        unique_client_id_postfix = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        )
        self.client_id_prefix = "dbus2mqtt-"
        self.client_id = f"{self.client_id_prefix}{unique_client_id_postfix}"

        self.client = mqtt.Client(
            client_id=self.client_id,
            protocol=mqtt.MQTTv5,
            callback_api_version=CallbackAPIVersion.VERSION2,
        )

        self.client.username_pw_set(
            username=self.config.username, password=self.config.password.get_secret_value()
        )

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message_safe

        self.loop = loop
        self.connected_event = asyncio.Event()

        self.topic_content_types: dict[str, Literal["json", "text"]] = (
            self._init_topic_content_types(app_context)
        )

    def connect(self):

        self.client.connect_async(
            host=self.config.host,
            port=self.config.port,
            clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY,
        )

    def _init_topic_content_types(
        self, app_context: AppContext
    ) -> dict[str, Literal["json", "text"]]:

        topic_content_types: dict[str, Literal["json", "text"]] = {}

        # First we check the expected content types from all configured mqtt_message triggers
        all_flows: list[FlowConfig] = []
        all_flows.extend(self.app_context.config.flows)
        for subscription in self.app_context.config.dbus.subscriptions:
            all_flows.extend(subscription.flows)

        for flow in all_flows:
            for trigger in flow.triggers:
                if trigger.type == FlowTriggerMqttMessageConfig.type:
                    topic_content_types[trigger.topic] = trigger.content_type

        # Next we check all command topics, these are always json
        for subscription in app_context.config.dbus.subscriptions:
            for interface in subscription.interfaces:
                topic = interface.render_mqtt_command_topic(app_context.templating, {})
                if topic:
                    topic_content_types[topic] = "json"

        return topic_content_types

    async def mqtt_publish_queue_processor_task(self):

        first_message = True

        """Continuously processes messages from the async queue."""
        while True:
            msg = await self.event_broker.mqtt_publish_queue.async_q.get()  # Wait for a message

            try:
                payload: str | bytes | None = msg.payload
                payload_type = msg.payload_serialization_type
                if payload_type == "text":
                    payload = str(msg.payload)
                if isinstance(msg.payload, dict) and payload_type == "json":
                    payload = json.dumps(msg.payload)
                elif isinstance(msg.payload, dict) and payload_type == "yaml":
                    payload = yaml.dump(msg.payload)
                elif isinstance(msg.payload, ParseResult) and payload_type == "binary":
                    try:
                        with urlopen(msg.payload.geturl()) as response:
                            payload = response.read()
                    except Exception as e:
                        # In case failing uri reads, we still publish an empty msg to avoid stale data
                        payload = None
                        logger.warning(
                            f"mqtt_publish_queue_processor_task: Exception: {e}",
                            exc_info=logger.isEnabledFor(logging.DEBUG),
                        )

                payload_log_msg = payload if isinstance(payload, str) else msg.payload
                logger.debug(
                    f"mqtt_publish_queue_processor_task: topic={msg.topic}, type={payload.__class__}, payload={payload_log_msg}"
                )

                if first_message:
                    await asyncio.wait_for(self.connected_event.wait(), timeout=5)

                publish_properties = Properties(PacketTypes.PUBLISH)
                publish_properties.UserProperty = ("client_id", self.client_id)

                publish_info = self.client.publish(
                    topic=msg.topic, payload=payload or "", properties=publish_properties
                )
                publish_info.wait_for_publish(timeout=1000)

                if first_message:
                    logger.info(
                        f"First message published: topic={msg.topic}, payload={payload_log_msg}"
                    )
                    first_message = False

            except Exception as e:
                logger.warning(
                    f"mqtt_publish_queue_processor_task: Exception: {e}",
                    exc_info=logger.isEnabledFor(logging.DEBUG),
                )
            finally:
                self.event_broker.mqtt_publish_queue.async_q.task_done()

    # The callback for when the client receives a CONNACK response from the server.
    def _on_connect(self, client: mqtt.Client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.warning(f"on_connect: Failed to connect: {reason_code}. Will retry connection")
        else:
            logger.info(f"on_connect: Connected to {self.config.host}:{self.config.port}")

            subscriptions = [
                (t, SubscribeOptions(noLocal=True)) for t in self.config.subscription_topics
            ]
            client.subscribe(subscriptions)

            self.loop.call_soon_threadsafe(self.connected_event.set)

    def _on_message_safe(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        try:
            return self._on_message(msg)
        except Exception:
            # Catch all uncaught exceptions to avoid mqtt_client processing anything at all
            # after the first exception occurred
            logger.exception("on_message: Uncaught exception while handling MQTT msg")

    def _on_message(self, msg: mqtt.MQTTMessage) -> None:

        # Skip messages being sent by other dbus2mqtt clients
        if msg.properties:
            user_properties: list[tuple[str, object]] = getattr(msg.properties, "UserProperty", [])
            client_id = next((str(v) for k, v in user_properties if k == "client_id"), None)
            if client_id and client_id != self.client_id:
                logger.debug(
                    f"on_message: skipping msg from another dbus2mqtt client, topic={msg.topic}, client_id={client_id}"
                )
            if client_id and client_id.startswith(self.client_id_prefix):
                return

        payload = msg.payload.decode()

        # Skip retained messages
        if msg.retain:
            logger.info(
                f"on_message: skipping msg with retain=True, topic={msg.topic}, payload={payload}"
            )
            return

        json_payload: Any = None
        log_payload = payload
        if self.topic_content_types.get(msg.topic) == "json":
            try:
                json_payload = json.loads(payload) if payload else {}
                log_payload = json.dumps(json_payload)
            except json.JSONDecodeError as e:
                logger.warning(
                    f"on_message: Unexpected payload, expecting json, topic={msg.topic}, payload={payload}, properties={msg.properties}, error={e}"
                )
                return

        logger.debug(f"on_message: msg.topic={msg.topic}, msg.payload={log_payload}")

        # Publish to flow trigger queue for any configured mqtt_message triggers
        flow_triggered = self._trigger_flows(msg.topic, payload, json_payload)

        # Publish on a queue that is being processed by dbus_client
        # Messages on the mqtt_receive_queue are all expected to have json payloads
        # as these messages are picked up by dbus_client for command handling
        if json_payload:
            self.event_broker.on_mqtt_receive(
                MqttMessage(msg.topic, json_payload),
                MqttReceiveHints(log_unmatched_message=flow_triggered),
            )

    def _trigger_flows(self, topic: str, payload: str, json_payload: Any) -> bool:
        """Triggers all flows that have a mqtt_trigger defined that matches the given topic and configured filters."""
        trigger_context: dict[str, Any] = {
            "topic": topic,
        }
        flow_trigger_handler = FlowTriggerMqttMessageHandler(
            trigger_context, topic, payload, json_payload
        )

        flow_triggered = False
        try:
            flow_triggered = self._trigger_processor.trigger_all_flows_sync(flow_trigger_handler)
        except Exception as e:
            logger.warning(
                f"_trigger_flows: Error while triggering flow, topic={topic}, payload={payload}, error={e}"
            )
            return False

        return flow_triggered
