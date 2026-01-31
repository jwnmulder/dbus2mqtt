import logging

from typing import Any

from dbus2mqtt import AppContext
from dbus2mqtt.config import (
    FlowActionContextSetConfig,
    FlowActionLogConfig,
    FlowActionMqttPublishConfig,
    FlowConfig,
    FlowTriggerContextChangedConfig,
    FlowTriggerDbusObjectAddedConfig,
    FlowTriggerDbusObjectRemovedConfig,
    FlowTriggerDbusSignalConfig,
    FlowTriggerScheduleConfig,
)
from dbus2mqtt.event_broker import FlowTriggerMessage
from dbus2mqtt.flow import FlowAction, FlowExecutionContext
from dbus2mqtt.flow.actions.context_set import ContextSetAction
from dbus2mqtt.flow.actions.log_action import LogAction
from dbus2mqtt.flow.actions.mqtt_publish import MqttPublishAction
from dbus2mqtt.flow.flow_trigger_handlers import FlowTriggerHandler
from dbus2mqtt.flow.flow_trigger_processor import FlowTriggerProcessor
from dbus2mqtt.template.templating import TemplateEngine

logger = logging.getLogger(__name__)


class _FlowActionContext:
    def __init__(
        self,
        app_context: AppContext,
        flow_config: FlowConfig,
        global_flows_context: dict[str, Any],
        flow_context: dict[str, Any],
    ):

        self.app_context = app_context
        self.global_flows_context = global_flows_context
        self.flow_context = flow_context
        self.flow_config = flow_config

        self.flow_conditions: list[str] = []
        if isinstance(flow_config.conditions, str):
            self.flow_conditions.append(flow_config.conditions)
        elif isinstance(flow_config.conditions, list):
            self.flow_conditions.extend(flow_config.conditions)

        self.flow_actions = self._setup_flow_actions()

    def _setup_flow_actions(self) -> list[FlowAction]:

        res = []
        for action_config in self.flow_config.actions:
            action = None
            if action_config.type == FlowActionContextSetConfig.type:
                action = ContextSetAction(action_config, self.app_context)
            elif action_config.type == FlowActionMqttPublishConfig.type:
                action = MqttPublishAction(action_config, self.app_context)
            elif action_config.type == FlowActionLogConfig.type:
                action = LogAction(action_config, self.app_context)

            if action:
                res.append(action)

        return res

    async def execute_actions(self, flow_execution_context: FlowExecutionContext):

        for action in self.flow_actions:
            await action.execute(flow_execution_context)


class FlowProcessor:
    def __init__(self, app_context: AppContext):
        self.app_context = app_context
        self.event_broker = app_context.event_broker

        self._global_context: dict[str, Any] = {}
        self._object_contexts: dict[str, dict[str, Any]] = {}

        self._trigger_processor = FlowTriggerProcessor(app_context)

        self._flows: dict[str, _FlowActionContext] = {}

        # register global flows
        self.register_flows(app_context.config.flows)

        # register dbus subscription flows
        for subscription in app_context.config.dbus.subscriptions:
            flow_context = {
                "subscription_bus_name": subscription.bus_name,
                "subscription_path": subscription.path,
                "subscription_interfaces": [i.interface for i in subscription.interfaces],
            }
            self.register_flows(subscription.flows, flow_context)

    def register_flows(self, flows: list[FlowConfig], flow_context: dict[str, Any] = {}):
        """Register flows with the flow processor."""
        for flow_config in flows:
            flow_action_context = _FlowActionContext(
                self.app_context, flow_config, self._global_context, flow_context
            )
            self._flows[flow_config.id] = flow_action_context

    async def flow_processor_task(self):
        """Continuously processes messages from the async queue."""
        # logger.info(f"flow_processor_task: configuring flows={[f.name for f in self.app_context.config.flows]}")

        while True:
            flow_trigger_message = await self.event_broker.flow_trigger_queue.async_q.get()

            try:
                await self._process_flow_trigger(flow_trigger_message)

            except Exception as e:
                # exc_info is only set when running in verbose mode to avoid lots of stack traces being printed
                # while flows are still running and the DBus object was just removed. Some examples:

                log_level = logging.WARN

                # 1: error during context_set
                # WARNING:dbus2mqtt.flow.flow_processor:flow_processor_task: Exception The name org.mpris.MediaPlayer2.firefox.instance_1_672 was not provided by any .service files
                if "was not provided by any .service files" in str(e):
                    log_level = logging.DEBUG

                logger.log(
                    log_level,
                    f"flow_processor_task: Exception during flow execution triggered by '{flow_trigger_message.flow_trigger_config.type}': {type(e).__name__}: {e}",
                    exc_info=logger.isEnabledFor(logging.DEBUG),
                )
            finally:
                self.event_broker.flow_trigger_queue.async_q.task_done()

    def _object_context_ref_from_trigger(
        self, flow_trigger_message: FlowTriggerMessage
    ) -> str | None:
        # TODO: Check for flow_trigger_massage.flow_trigger_config.type to assert on
        # existence of bus_name and path
        trigger_context = flow_trigger_message.trigger_context
        if "bus_name" in trigger_context and "path" in trigger_context:
            return f"{trigger_context['bus_name']}:{trigger_context['path']}"

        return None

    def _trigger_config_to_str(self, msg: FlowTriggerMessage) -> str:
        config = msg.flow_trigger_config
        if isinstance(config, FlowTriggerDbusSignalConfig):
            return f"{config.type}({config.signal})"
        elif isinstance(
            config, (FlowTriggerDbusObjectAddedConfig, FlowTriggerDbusObjectRemovedConfig)
        ):
            path = msg.trigger_context.get("path") if msg.trigger_context else None
            if path:
                return f"{config.type}({path})"
        elif isinstance(config, FlowTriggerContextChangedConfig):
            scope = msg.trigger_context.get("scope") if msg.trigger_context else None
            if scope:
                return f"{config.type}({scope})"
        return config.type

    async def _process_flow_trigger(self, flow_trigger_message: FlowTriggerMessage):

        trigger_type = flow_trigger_message.flow_trigger_config.type
        trigger_str = self._trigger_config_to_str(flow_trigger_message)
        flow_str = flow_trigger_message.flow_config.name or flow_trigger_message.flow_config.id

        flow_id = flow_trigger_message.flow_config.id

        flow = self._flows[flow_id]

        object_context_ref = self._object_context_ref_from_trigger(flow_trigger_message)
        clear_object_context_after_flow = (
            object_context_ref
            and flow_trigger_message.flow_trigger_config.type
            == FlowTriggerDbusObjectRemovedConfig.type
        )

        try:
            # Each flow executed gets its own execution context
            flow_execution_context = self._flow_execution_context(
                flow, flow_trigger_message, object_context_ref
            )

            # Check if any actions should run based on flow conditions
            should_execute_actions = self._evaluate_flow_conditions(
                flow, flow_execution_context, self.app_context.templating
            )

            log_message = f"on_trigger: {trigger_str}, flow={flow_str}, time={flow_trigger_message.timestamp.isoformat()}"
            if not should_execute_actions:
                log_message = f"{log_message} - conditions not met, skipping actions"

            if should_execute_actions and trigger_type != FlowTriggerScheduleConfig.type:
                logger.info(log_message)
            else:
                logger.debug(log_message)

            if should_execute_actions:
                await flow.execute_actions(flow_execution_context)
        finally:
            if object_context_ref and clear_object_context_after_flow:
                del self._object_contexts[object_context_ref]

        # Check if global context was updated during flow execution to trigger context_changed flows
        if flow_execution_context.global_context_updated:
            # Check if this flow was not triggered by a context_changed trigger to avoid looping
            if trigger_type == FlowTriggerContextChangedConfig.type:
                logger.debug("Skip firing context_change trigger to avoid looping")
            else:
                trigger_context = {"scope": "global"}
                await self._trigger_processor.trigger_all_flows(
                    FlowTriggerHandler(FlowTriggerContextChangedConfig.type, trigger_context)
                )

    def _flow_execution_context(
        self,
        flow: _FlowActionContext,
        flow_trigger_message: FlowTriggerMessage,
        object_context_ref: str | None,
    ) -> FlowExecutionContext:
        """Per flow execution context allows for updates during flow execution without affecting other executions.

        Initialized with global and flow context
        """
        # Each dbus_object gets it's own object context
        object_context = None
        if object_context_ref:
            object_context = self._object_contexts.get(object_context_ref)
            if not object_context:
                object_context = {}
                self._object_contexts[object_context_ref] = object_context

        flow_execution_context = FlowExecutionContext(
            flow.flow_config.name,
            global_flows_context=flow.global_flows_context,
            flow_context=flow.flow_context,
            object_context_ref=object_context_ref,
            object_context=object_context,
        )

        trigger_type = flow_trigger_message.flow_trigger_config.type
        flow_execution_context.update_context({"trigger_type": trigger_type})

        if flow_trigger_message.trigger_context:
            flow_execution_context.update_context(flow_trigger_message.trigger_context)

        return flow_execution_context

    def _evaluate_flow_conditions(
        self,
        flow: _FlowActionContext,
        context: FlowExecutionContext,
        template_engine: TemplateEngine,
    ) -> bool:

        if len(flow.flow_conditions) == 0:
            return True

        render_context = context.get_aggregated_context()

        for condition in flow.flow_conditions:
            res = template_engine.render_template(condition, bool, render_context)
            if not res:
                return False

        return True
