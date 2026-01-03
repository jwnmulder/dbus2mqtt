import logging

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from dbus2mqtt import AppContext
from dbus2mqtt.config import (
    FlowConfig,
    FlowTriggerConfig,
    FlowTriggerDbusSignalConfig,
    FlowTriggerMqttMessageConfig,
    SubscriptionConfig,
)
from dbus2mqtt.event_broker import FlowTriggerMessage
from dbus2mqtt.template.templating import TemplateEngine

logger = logging.getLogger(__name__)


class FlowTriggerHandler(ABC):

    def __init__(self, trigger_type: str, trigger_context: dict[str, Any]):
        self.trigger_type = trigger_type
        self.context = trigger_context

    @abstractmethod
    def should_trigger_flow(
        self,
        trigger_config: FlowTriggerConfig,
        templating: TemplateEngine
    ) -> bool:
        ...

    def trigger_context(self, trigger_config: FlowTriggerConfig) ->dict[str, Any]:
        return self.context

class FlowTriggerAlwaysTrueHandler(FlowTriggerHandler):
    def should_trigger_flow(
        self,
        trigger_config: FlowTriggerConfig,
        templating: TemplateEngine
    ) -> bool:
        return True

class FlowTriggerDbusSignalHandler(FlowTriggerHandler):

    def __init__(self, trigger_context: dict[str, Any], signal: str, interface: str | None = None):
        super().__init__(FlowTriggerDbusSignalConfig.type, trigger_context)
        self.signal = signal
        self.interface = interface

    def should_trigger_flow(
        self,
        trigger_config: FlowTriggerConfig,
        templating: TemplateEngine
    ) -> bool:
        assert isinstance(trigger_config, FlowTriggerDbusSignalConfig)

        matches = self.signal == trigger_config.signal

        # dbus_signal triggers might have an interface configured
        if trigger_config.interface:
            matches &= self.interface == trigger_config.interface

        return matches

class FlowTriggerMqttMessageHandler(FlowTriggerHandler):

    def __init__(self, trigger_context: dict[str, Any], topic: str, payload: str, json_payload: Any):
        super().__init__(FlowTriggerMqttMessageConfig.type, trigger_context)
        self.topic = topic
        self.payload = payload
        self.json_payload = json_payload

    def should_trigger_flow(
        self,
        trigger_config: FlowTriggerMqttMessageConfig,
        templating: TemplateEngine
    ):
        assert isinstance(trigger_config, FlowTriggerMqttMessageConfig)

        matches = trigger_config.topic == self.topic

        # mqtt_message triggers might have a filter configured
        if trigger_config.filter is not None:
            matches &= trigger_config.matches_filter(templating, self.context)

        return matches

    def trigger_context(self, trigger_config: FlowTriggerMqttMessageConfig):

        assert isinstance(trigger_config, FlowTriggerMqttMessageConfig)

        # Use the correct payload type which is configured for the trigger
        trigger_context_payload: Any = self.payload
        if trigger_config.content_type == "json":
            trigger_context_payload = self.json_payload

        return super().trigger_context(trigger_config) | {
            "payload": trigger_context_payload
        }

class FlowTriggerProcessor:
    def __init__(self, app_context: AppContext):
        self.config = app_context.config
        self.event_broker = app_context.event_broker
        self.templating = app_context.templating

    async def trigger_all_flows(
        self,
        flow_trigger_handler: FlowTriggerHandler,
    ):
        """Trigger all flows that have a corresponding trigger defined.

        Global scope changes are triggered to all global and subscription specific flows
        """
        all_flows: list[FlowConfig] = []
        all_flows.extend(self.config.flows)
        for subscription in self.config.dbus.subscriptions:
            all_flows.extend(subscription.flows)

        for flow in all_flows:
            for trigger in flow.triggers:
                if trigger.type == flow_trigger_handler.trigger_type:
                    await self._execute_flow(flow, trigger, flow_trigger_handler)

    def trigger_all_flows_sync(
        self,
        flow_trigger_handler: FlowTriggerHandler,
    ) -> bool:
        """Trigger all flows that have a corresponding trigger defined.

        Global scope changes are triggered to all global and subscription specific flows
        """
        flow_triggered = True
        all_flows: list[FlowConfig] = []
        all_flows.extend(self.config.flows)
        for subscription in self.config.dbus.subscriptions:
            all_flows.extend(subscription.flows)

        for flow in all_flows:
            for trigger in flow.triggers:
                if trigger.type == flow_trigger_handler.trigger_type:
                    self._execute_flow_sync(flow, trigger, flow_trigger_handler)
                    flow_triggered = True

        return flow_triggered

    async def trigger_subscription_flows(
        self,
        subscription_config: SubscriptionConfig,
        flow_trigger_handler: FlowTriggerHandler,
    ):
        """Trigger subscription specific flows that have a corresponding trigger_type defined.

        No filtering is done, if trigger.type matches, the flow is scheduled for execution.
        """
        for flow in subscription_config.flows:
            for trigger in flow.triggers:
                if trigger.type == flow_trigger_handler.trigger_type:
                    await self._execute_flow(flow, trigger, flow_trigger_handler)

    async def trigger_flow(
        self,
        flow: FlowConfig,
        trigger_config: FlowTriggerConfig,
        flow_trigger_handler: FlowTriggerHandler,
    ):
        await self._execute_flow(flow, trigger_config, flow_trigger_handler)

    def trigger_flow_sync(
        self,
        flow: FlowConfig,
        trigger_config: FlowTriggerConfig,
        flow_trigger_handler: FlowTriggerHandler,
    ):
        self._execute_flow_sync(flow, trigger_config, flow_trigger_handler)

    async def _execute_flow(
        self,
        flow: FlowConfig,
        trigger_config: FlowTriggerConfig,
        flow_trigger_handler: FlowTriggerHandler,
    ):
        should_trigger_flow = flow_trigger_handler.should_trigger_flow(
            trigger_config,
            self.templating
        )
        if should_trigger_flow:
            trigger_context = flow_trigger_handler.trigger_context(trigger_config)
            trigger = FlowTriggerMessage(flow, trigger_config, datetime.now(), trigger_context)
            await self.event_broker.flow_trigger_queue.async_q.put(trigger)

    def _execute_flow_sync(
        self,
        flow: FlowConfig,
        trigger_config: FlowTriggerConfig,
        flow_trigger_handler: FlowTriggerHandler,
    ):
        should_trigger_flow = flow_trigger_handler.should_trigger_flow(
            trigger_config,
            self.templating
        )
        if should_trigger_flow:
            trigger_context = flow_trigger_handler.trigger_context(trigger_config)
            trigger = FlowTriggerMessage(flow, trigger_config, datetime.now(), trigger_context)
            self.event_broker.flow_trigger_queue.sync_q.put(trigger)
