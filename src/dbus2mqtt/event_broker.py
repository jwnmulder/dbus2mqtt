import asyncio
import logging

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import janus

from dbus2mqtt.config import FlowConfig, FlowTriggerConfig

logger = logging.getLogger(__name__)


@dataclass
class MqttMessage:
    topic: str
    payload: Any
    payload_serialization_type: str = "json"

@dataclass
class MqttReceiveHints:
    log_unmatched_message: bool = True

@dataclass
class FlowTriggerMessage:
    flow_config: FlowConfig
    flow_trigger_config: FlowTriggerConfig
    timestamp: datetime
    trigger_context: dict[str, Any] | None = None

class EventBroker:
    def __init__(self):
        self.mqtt_receive_queue = janus.Queue[tuple[MqttMessage, MqttReceiveHints]]()
        self.mqtt_publish_queue = janus.Queue[MqttMessage]()
        self.flow_trigger_queue = janus.Queue[FlowTriggerMessage]()
        # self.dbus_send_queue: janus.Queue

    async def close(self):
        await asyncio.gather(
            self.mqtt_receive_queue.aclose(),
            self.mqtt_publish_queue.aclose(),
            self.flow_trigger_queue.aclose(),
            return_exceptions=True
        )

    def on_mqtt_receive(self, msg: MqttMessage, hints: MqttReceiveHints):
        # logger.debug("on_mqtt_receive")
        self.mqtt_receive_queue.sync_q.put((msg, hints))

    async def publish_to_mqtt(self, msg: MqttMessage):
        # logger.debug("publish_to_mqtt")
        await self.mqtt_publish_queue.async_q.put(msg)
