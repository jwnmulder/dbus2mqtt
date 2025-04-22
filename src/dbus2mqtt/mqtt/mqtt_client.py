
import asyncio
import json
import logging

from typing import Any

import paho.mqtt.client as mqtt
import yaml

from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.subscribeoptions import SubscribeOptions

from dbus2mqtt import AppContext
from dbus2mqtt.event_broker import MqttMessage

logger = logging.getLogger(__name__)

class MqttClient:

    def __init__(self, app_context: AppContext):
        self.config = app_context.config.mqtt
        self.event_broker = app_context.event_broker

        self.client = mqtt.Client(
            protocol=mqtt.MQTTv5,
            callback_api_version=CallbackAPIVersion.VERSION2
        )

        self.client.username_pw_set(
            username=self.config.username,
            password=self.config.password.get_secret_value()
        )

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def connect(self):

        # mqtt_client.on_message = lambda client, userdata, message: asyncio.create_task(mqtt_on_message(client, userdata, message))
        self.client.connect_async(
            host=self.config.host,
            port=self.config.port
        )

    async def mqtt_publish_queue_processor_task(self):

        first_message = True

        """Continuously processes messages from the async queue."""
        while True:
            msg = await self.event_broker.mqtt_publish_queue.async_q.get()  # Wait for a message

            try:
                payload = msg.payload
                type = msg.payload_serialization_type
                if isinstance(msg.payload, dict):
                    if type == "json":
                        payload = json.dumps(msg.payload)
                    elif type == "yaml":
                        payload = yaml.dump(msg.payload)
                elif type == "text":
                    payload = str(payload)

                logger.debug(f"mqtt_publish_queue_processor_task: payload={payload}")
                self.client.publish(topic=msg.topic, payload=payload)

                if first_message:
                    logger.info(f"First message published: topic={msg.topic}, payload={payload}")
                    first_message = False

            except Exception as e:
                logger.warning(f"mqtt_publish_queue_processor_task: Exception {e}", exc_info=True)
            finally:
                self.event_broker.mqtt_publish_queue.async_q.task_done()


    async def run(self):
        """Runs the MQTT loop in a non-blocking way with asyncio."""
        self.client.loop_start()  # Runs Paho's loop in a background thread
        await asyncio.Event().wait()  # Keeps the coroutine alive

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client: mqtt.Client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.warning(f"on_connect: Failed to connect: {reason_code}. Will retry connection")
        else:
            logger.info(f"on_connect: Connected to {self.config.host}:{self.config.port}")
            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
            client.subscribe("dbus2mqtt/#", options=SubscribeOptions(noLocal=True))

    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):

        payload = msg.payload.decode()
        if msg.retain:
            logger.info(f"on_message: skipping msg with retain=True, topic={msg.topic}, payload={payload}")
            return

        try:
            json_payload = json.loads(payload)
            logger.debug(f"on_message: msg.topic={msg.topic}, msg.payload={json.dumps(json_payload)}")
            self.event_broker.on_mqtt_receive(MqttMessage(msg.topic, json_payload))
        except json.JSONDecodeError as e:
            logger.warning(f"on_message: Unexpected payload, expecting json, topic={msg.topic}, payload={payload}, error={e}")
