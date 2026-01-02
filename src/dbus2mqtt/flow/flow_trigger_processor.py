import logging

from datetime import datetime
from typing import Any

from dbus2mqtt import AppContext
from dbus2mqtt.config import (
    FlowConfig,
    FlowTriggerConfig,
    SubscriptionConfig,
)
from dbus2mqtt.event_broker import FlowTriggerMessage

logger = logging.getLogger(__name__)


class FlowTriggerProcessor:
    def __init__(self, app_context: AppContext):
        self.config = app_context.config
        self.event_broker = app_context.event_broker

    async def trigger_all_flows(
        self,
        trigger_type: str,
        trigger_context: dict[str, Any],
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
                if trigger.type == trigger_type:
                    await self._execute_flow(flow, trigger, trigger_context)

    async def trigger_subscription_flows(
        self,
        subscription_config: SubscriptionConfig,
        trigger_type: str,
        trigger_context: dict[str, Any],
    ):
        """Trigger subscription specific flows that have a corresponding trigger_type defined.

        No filtering is done, if trigger.type matches, the flow is scheduled for execution.
        """
        for flow in subscription_config.flows:
            for trigger in flow.triggers:
                if trigger.type == trigger_type:
                    await self._execute_flow(flow, trigger, trigger_context)

    async def trigger_flow(
        self,
        flow: FlowConfig,
        trigger_config: FlowTriggerConfig,
        trigger_context: dict[str, Any],
    ):
        await self._execute_flow(flow, trigger_config, trigger_context)

    def trigger_flow_sync(
        self,
        flow: FlowConfig,
        trigger_config: FlowTriggerConfig,
        trigger_context: dict[str, Any],
    ):
        self._execute_flow_sync(flow, trigger_config, trigger_context)

    async def _execute_flow(
        self,
        flow: FlowConfig,
        trigger_config: FlowTriggerConfig,
        trigger_context: dict[str, Any],
    ):
        trigger = FlowTriggerMessage(flow, trigger_config, datetime.now(), trigger_context)
        await self.event_broker.flow_trigger_queue.async_q.put(trigger)

    def _execute_flow_sync(
        self,
        flow: FlowConfig,
        trigger_config: FlowTriggerConfig,
        trigger_context: dict[str, Any],
    ):
        trigger = FlowTriggerMessage(flow, trigger_config, datetime.now(), trigger_context)
        self.event_broker.flow_trigger_queue.sync_q.put(trigger)
