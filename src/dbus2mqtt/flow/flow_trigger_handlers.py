from typing import Any

from dbus2mqtt.config import (
    FlowTriggerConfig,
    FlowTriggerDbusSignalConfig,
    FlowTriggerMqttMessageConfig,
)
from dbus2mqtt.template.templating import TemplateEngine


class FlowTriggerHandler:
    """Basic flow trigger handler that unconditionally triggers flows."""

    def __init__(self, trigger_type: str, trigger_context: dict[str, Any]):
        self.trigger_type = trigger_type
        self.context = trigger_context

    def should_trigger_flow(
        self, trigger_config: FlowTriggerConfig, templating: TemplateEngine
    ) -> bool:

        # triggers might have a filter configured
        if trigger_config.filter is not None:
            trigger_context = self.final_trigger_context(trigger_config)
            res = self._matches_filter(trigger_config, templating, trigger_context)
            return res

        return True

    def final_trigger_context(self, trigger_config: FlowTriggerConfig) -> dict[str, Any]:
        return self.context

    def _matches_filter(
        self,
        trigger_config: FlowTriggerConfig,
        template_engine: TemplateEngine,
        trigger_context: dict[str, Any],
    ) -> bool:
        if trigger_config.filter:
            return template_engine.render_template(trigger_config.filter, bool, trigger_context)
        return True


class FlowTriggerDbusSignalHandler(FlowTriggerHandler):
    """Trigger flows only if signal and interface are matching."""

    def __init__(self, trigger_context: dict[str, Any], signal: str, interface: str | None = None):
        super().__init__(FlowTriggerDbusSignalConfig.type, trigger_context)
        self.signal = signal
        self.interface = interface

    def should_trigger_flow(
        self, trigger_config: FlowTriggerConfig, templating: TemplateEngine
    ) -> bool:
        assert isinstance(trigger_config, FlowTriggerDbusSignalConfig)

        if trigger_config.signal != self.signal:
            return False

        # dbus_signal triggers might have an interface configured
        if trigger_config.interface and trigger_config.interface != self.interface:
            return False

        return super().should_trigger_flow(trigger_config, templating)


class FlowTriggerMqttMessageHandler(FlowTriggerHandler):
    """Trigger flows only if topic and filter is matching."""

    def __init__(
        self,
        trigger_context: dict[str, Any],
        topic: str,
        payload: str,
        json_payload: Any,
    ):
        super().__init__(FlowTriggerMqttMessageConfig.type, trigger_context)
        self.topic = topic
        self.payload = payload
        self.json_payload = json_payload

    def should_trigger_flow(
        self, trigger_config: FlowTriggerMqttMessageConfig, templating: TemplateEngine
    ) -> bool:
        assert isinstance(trigger_config, FlowTriggerMqttMessageConfig)

        if trigger_config.topic != self.topic:
            return False

        return super().should_trigger_flow(trigger_config, templating)

    def final_trigger_context(self, trigger_config: FlowTriggerMqttMessageConfig) -> dict[str, Any]:
        assert isinstance(trigger_config, FlowTriggerMqttMessageConfig)

        # Use the correct payload type which is configured for the trigger
        trigger_context_payload: Any = self.payload
        if trigger_config.content_type == "json":
            trigger_context_payload = self.json_payload

        return super().final_trigger_context(trigger_config) | {"payload": trigger_context_payload}
