import asyncio
import logging

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import janus

from dbus2mqtt.config import (
    FlowConfig,
    FlowTriggerConfig,
    SignalConfig,
    SubscriptionConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class MqttMessage:
    topic: str
    payload: Any
    payload_serialization_type: str = "json"

@dataclass
class DbusSignalWithState:
    bus_name: str
    path: str
    interface_name: str
    subscription_config: SubscriptionConfig
    signal_config: SignalConfig
    args: list[Any]

@dataclass
class FlowTriggerMessage:
    flow_config: FlowConfig
    flow_trigger_config: FlowTriggerConfig
    timestamp: datetime
    context: dict[str, Any] | None = None

class EventBroker:
    def __init__(self):
        self.mqtt_receive_queue = janus.Queue[MqttMessage]()
        self.mqtt_publish_queue = janus.Queue[MqttMessage]()
        self.dbus_signal_queue = janus.Queue[DbusSignalWithState]()
        self.flow_trigger_queue = janus.Queue[FlowTriggerMessage]()
        # self.dbus_send_queue: janus.Queue

    async def close(self):
        await asyncio.gather(
            self.mqtt_receive_queue.aclose(),
            self.mqtt_publish_queue.aclose(),
            self.dbus_signal_queue.aclose(),
            self.flow_trigger_queue.aclose(),
            return_exceptions=True
        )

    def on_mqtt_receive(self, msg: MqttMessage):
        # logger.debug("on_mqtt_receive")
        self.mqtt_receive_queue.sync_q.put(msg)

    async def publish_to_mqtt(self, msg: MqttMessage):
        # logger.debug("publish_to_mqtt")
        await self.mqtt_publish_queue.async_q.put(msg)

    def on_dbus_signal(self, signal: DbusSignalWithState):
        # logger.debug("on_dbus_signal")
        self.dbus_signal_queue.sync_q.put(signal)
