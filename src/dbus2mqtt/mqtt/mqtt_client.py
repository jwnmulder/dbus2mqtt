
import asyncio
import json
import logging
import random
import string

from datetime import datetime
from typing import Any
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
from dbus2mqtt.event_broker import FlowTriggerMessage, MqttMessage, MqttReceiveHints

logger = logging.getLogger(__name__)

class MqttClient:

    def __init__(self, app_context: AppContext, loop):
        self.app_context = app_context
        self.config = app_context.config.mqtt
        self.event_broker = app_context.event_broker

        unique_client_id_postfix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.client_id_prefix = "dbus2mqtt-"
        self.client_id = f"{self.client_id_prefix}{unique_client_id_postfix}"

        self.client = mqtt.Client(
            client_id=self.client_id,
            protocol=mqtt.MQTTv5,
            callback_api_version=CallbackAPIVersion.VERSION2
        )

        self.client.username_pw_set(
            username=self.config.username,
            password=self.config.password.get_secret_value()
        )

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.loop = loop
        self.connected_event = asyncio.Event()

    def connect(self):

        self.client.connect_async(
            host=self.config.host,
            port=self.config.port,
            clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY
        )

    async def mqtt_publish_queue_processor_task(self):

        first_message = True

        """Continuously processes messages from the async queue."""
        while True:
            msg = await self.event_broker.mqtt_publish_queue.async_q.get()  # Wait for a message

            try:
                payload: str | bytes | None = msg.payload
                type = msg.payload_serialization_type
                if type == "text":
                    payload = str(msg.payload)
                if isinstance(msg.payload, dict) and type == "json":
                    payload = json.dumps(msg.payload)
                elif isinstance(msg.payload, dict) and type == "yaml":
                    payload = yaml.dump(msg.payload)
                elif isinstance(msg.payload, ParseResult) and type == "binary":
                    try:
                        with urlopen(msg.payload.geturl()) as response:
                            payload = response.read()
                    except Exception as e:
                        # In case failing uri reads, we still publish an empty msg to avoid stale data
                        payload = None
                        logger.warning(f"mqtt_publish_queue_processor_task: Exception {e}", exc_info=logger.isEnabledFor(logging.DEBUG))

                payload_log_msg = payload if isinstance(payload, str) else msg.payload
                logger.debug(f"mqtt_publish_queue_processor_task: topic={msg.topic}, type={payload.__class__}, payload={payload_log_msg}")

                if first_message:
                    await asyncio.wait_for(self.connected_event.wait(), timeout=5)

                publish_properties = Properties(PacketTypes.PUBLISH)
                publish_properties.UserProperty = ("client_id", self.client_id)

                publish_info = self.client.publish(
                    topic=msg.topic,
                    payload=payload or "",
                    properties=publish_properties
                )
                publish_info.wait_for_publish(timeout=1000)

                if first_message:
                    logger.info(f"First message published: topic={msg.topic}, payload={payload_log_msg}")
                    first_message = False

            except Exception as e:
                logger.warning(f"mqtt_publish_queue_processor_task: Exception {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
            finally:
                self.event_broker.mqtt_publish_queue.async_q.task_done()

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client: mqtt.Client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.warning(f"on_connect: Failed to connect: {reason_code}. Will retry connection")
        else:
            logger.info(f"on_connect: Connected to {self.config.host}:{self.config.port}")

            subscriptions = [(t, SubscribeOptions(noLocal=True)) for t in self.config.subscription_topics]
            client.subscribe(subscriptions)

            self.loop.call_soon_threadsafe(self.connected_event.set)

    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):

        # Skip messages being sent by other dbus2mqtt clients
        if msg.properties:
            user_properties: list[tuple[str, object]] = getattr(msg.properties, "UserProperty", [])
            client_id = next((str(v) for k, v in user_properties if k == "client_id"), None)
            if client_id and client_id != self.client_id:
                logger.debug(f"on_message: skipping msg from another dbus2mqtt client, topic={msg.topic}, client_id={client_id}")
            if client_id and client_id.startswith(self.client_id_prefix):
                return

        # Skip retained messages
        payload = msg.payload.decode()
        if msg.retain:
            logger.info(f"on_message: skipping msg with retain=True, topic={msg.topic}, payload={payload}")
            return

        try:
            json_payload = json.loads(payload) if payload else {}
            logger.debug(f"on_message: msg.topic={msg.topic}, msg.payload={json.dumps(json_payload)}")

            # publish to flow trigger queue for any configured mqtt_message triggers
            flow_trigger_messages = self._trigger_flows(msg.topic, {
                "topic": msg.topic,
                "payload": json_payload
            })

            # publish on a queue that is being processed by dbus_client
            self.event_broker.on_mqtt_receive(
                MqttMessage(msg.topic, json_payload),
                MqttReceiveHints(
                    log_unmatched_message=len(flow_trigger_messages) == 0
                )
            )

        except json.JSONDecodeError as e:
            logger.warning(f"on_message: Unexpected payload, expecting json, topic={msg.topic}, payload={payload}, error={e}")

    def _trigger_flows(self, topic: str, trigger_context: dict) -> list[FlowTriggerMessage]:
        """Triggers all flows that have a mqtt_trigger defined that matches the given topic
           and configured filters."""

        flow_trigger_messages = []

        all_flows: list[FlowConfig] = []
        all_flows.extend(self.app_context.config.flows)
        for subscription in self.app_context.config.dbus.subscriptions:
            all_flows.extend(subscription.flows)

        for flow in all_flows:
            for trigger in flow.triggers:
                if trigger.type == FlowTriggerMqttMessageConfig.type:
                    matches_filter = trigger.topic == topic
                    if matches_filter and trigger.filter is not None:
                        matches_filter = trigger.matches_filter(self.app_context.templating, trigger_context)

                    if matches_filter:
                        trigger_message = FlowTriggerMessage(
                            flow,
                            trigger,
                            datetime.now(),
                            trigger_context=trigger_context,
                        )

                        flow_trigger_messages.append(trigger_message)
                        self.event_broker.flow_trigger_queue.sync_q.put(trigger_message)

        return flow_trigger_messages
