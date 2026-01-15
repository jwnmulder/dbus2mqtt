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
        return True

    def final_trigger_context(self, trigger_config: FlowTriggerConfig) -> dict[str, Any]:
        return self.context


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

        matches = self.signal == trigger_config.signal

        # dbus_signal triggers might have an interface configured
        if matches and trigger_config.interface:
            matches = self.interface == trigger_config.interface

        return matches


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

        matches = trigger_config.topic == self.topic

        # mqtt_message triggers might have a filter configured
        if matches and trigger_config.filter is not None:
            matches = trigger_config.matches_filter(templating, self.context)

        return matches

    def final_trigger_context(self, trigger_config: FlowTriggerMqttMessageConfig) -> dict[str, Any]:
        assert isinstance(trigger_config, FlowTriggerMqttMessageConfig)

        # Use the correct payload type which is configured for the trigger
        trigger_context_payload: Any = self.payload
        if trigger_config.content_type == "json":
            trigger_context_payload = self.json_payload

        return super().final_trigger_context(trigger_config) | {"payload": trigger_context_payload}
