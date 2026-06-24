import logging

from datetime import datetime

from dbus2mqtt import AppContext
from dbus2mqtt.config import FlowConfig, FlowTriggerConfig, SubscriptionConfig
from dbus2mqtt.event_broker import FlowTriggerMessage
from dbus2mqtt.flow.flow_trigger_handlers import FlowTriggerHandler

logger = logging.getLogger(__name__)


class FlowTriggerProcessor:
    def __init__(self, app_context: AppContext):
        self.config = app_context.config
        self.event_broker = app_context.event_broker
        self.templating = app_context.templating

    async def trigger_all_flows(self, flow_trigger_handler: FlowTriggerHandler):
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

    def trigger_all_flows_sync(self, flow_trigger_handler: FlowTriggerHandler) -> bool:
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
        self, subscription_config: SubscriptionConfig, flow_trigger_handler: FlowTriggerHandler
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
            trigger_config, self.templating
        )
        if should_trigger_flow:
            trigger_context = flow_trigger_handler.final_trigger_context(trigger_config)
            trigger = FlowTriggerMessage(flow, trigger_config, datetime.now(), trigger_context)
            await self.event_broker.flow_trigger_queue.async_q.put(trigger)

    def _execute_flow_sync(
        self,
        flow: FlowConfig,
        trigger_config: FlowTriggerConfig,
        flow_trigger_handler: FlowTriggerHandler,
    ):
        should_trigger_flow = flow_trigger_handler.should_trigger_flow(
            trigger_config, self.templating
        )
        if should_trigger_flow:
            trigger_context = flow_trigger_handler.final_trigger_context(trigger_config)
            trigger = FlowTriggerMessage(flow, trigger_config, datetime.now(), trigger_context)
            self.event_broker.flow_trigger_queue.sync_q.put(trigger)
