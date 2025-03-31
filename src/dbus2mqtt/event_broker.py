import asyncio
import logging

from dataclasses import dataclass
from typing import Any

import janus

from dbus2mqtt.config import SignalHandlerConfig
from dbus2mqtt.dbus_types import BusNameSubscriptions

logger = logging.getLogger(__name__)


@dataclass
class MqttMessage:
    topic: str
    payload: Any

@dataclass
class DbusSignalWithState:
    bus_name_subscriptions: BusNameSubscriptions
    path: str
    interface_name: str
    signal_handler_configs: list[SignalHandlerConfig]
    args: list[Any]

class EventBroker:
    def __init__(self):
        self.mqtt_receive_queue = janus.Queue[MqttMessage]()
        self.mqtt_publish_queue = janus.Queue[MqttMessage]()
        self.dbus_signal_queue = janus.Queue[DbusSignalWithState]()
        # self.dbus_send_queue: janus.Queue

    async def close(self):
        await asyncio.gather(
            self.mqtt_receive_queue.aclose(),
            self.mqtt_publish_queue.aclose(),
            self.dbus_signal_queue.aclose()
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
