import fnmatch
import uuid
import warnings

from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

from pydantic import Field, SecretStr

from dbus2mqtt.template.templating import TemplateEngine


@dataclass
class SignalConfig:
    signal: str
    filter: str | None = None

    def matches_filter(self, template_engine: TemplateEngine, *args) -> bool:
        if self.filter:
            return template_engine.render_template(self.filter, bool, { "args": args })
        return True

@dataclass
class MethodConfig:
    method: str

@dataclass
class PropertyConfig:
    property: str

@dataclass
class InterfaceConfig:
    interface: str
    mqtt_command_topic: str | None = None
    mqtt_response_topic: str | None = None
    signals: list[SignalConfig] = field(default_factory=list)
    methods: list[MethodConfig] = field(default_factory=list)
    properties: list[PropertyConfig] = field(default_factory=list)

    def render_mqtt_command_topic(self, template_engine: TemplateEngine, context: dict[str, Any]) -> Any:
        if self.mqtt_command_topic:
            return template_engine.render_template(self.mqtt_command_topic, str, context)
        return None

    def render_mqtt_response_topic(self, template_engine: TemplateEngine, context: dict[str, Any]) -> str | None:
        if self.mqtt_response_topic:
            return template_engine.render_template(self.mqtt_response_topic, str, context)
        return None

@dataclass
class FlowTriggerScheduleConfig:
    type: Literal["schedule"] = "schedule"
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    cron: dict[str, object] | None = None
    interval: dict[str, object] | None = None

@dataclass
class FlowTriggerDbusSignalConfig:
    interface: str
    signal: str
    type: Literal["dbus_signal"] = "dbus_signal"
    bus_name: str | None = None
    path: str | None = None
    # filter: str | None = None

@dataclass
class FlowTriggerBusNameAddedConfig:
    type: Literal["bus_name_added"] = "bus_name_added"

    def __post_init__(self):
        warnings.warn(f"{self.type} flow trigger may be removed in a future version.", DeprecationWarning, stacklevel=2)

@dataclass
class FlowTriggerBusNameRemovedConfig:
    type: Literal["bus_name_removed"] = "bus_name_removed"

    def __post_init__(self):
        warnings.warn(f"{self.type} flow trigger may be removed in a future version.", DeprecationWarning, stacklevel=2)

@dataclass
class FlowTriggerObjectAddedConfig:
    type: Literal["object_added"] = "object_added"
    # filter: str | None = None

@dataclass
class FlowTriggerObjectRemovedConfig:
    type: Literal["object_removed"] = "object_removed"
    # filter: str | None = None

@dataclass
class FlowTriggerMqttMessageConfig:
    topic: str
    type: Literal["mqtt_message"] = "mqtt_message"
    filter: str | None = None

    def matches_filter(self, template_engine: TemplateEngine, trigger_context: dict[str, Any]) -> bool:
        if self.filter:
            return template_engine.render_template(self.filter, bool, trigger_context)
        return True

FlowTriggerConfig = Annotated[
    FlowTriggerScheduleConfig | FlowTriggerDbusSignalConfig | FlowTriggerBusNameAddedConfig | FlowTriggerBusNameRemovedConfig | FlowTriggerObjectAddedConfig | FlowTriggerObjectRemovedConfig | FlowTriggerMqttMessageConfig,
    Field(discriminator="type")
]

@dataclass
class FlowActionContextSetConfig:
    type: Literal["context_set"] = "context_set"
    context: dict[str, object] | None = None
    """Per flow execution context"""
    global_context: dict[str, object] | None = None
    """Global context, shared between multiple flow executions, over all subscriptions"""

@dataclass
class FlowActionMqttPublishConfig:
    topic: str
    payload_template: str | dict[str, Any]
    type: Literal["mqtt_publish"] = "mqtt_publish"
    payload_type: Literal["json", "yaml", "text", "binary"] = "json"

@dataclass
class FlowActionLogConfig:
    msg: str
    type: Literal["log"] = "log"
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

FlowActionConfig = Annotated[
    FlowActionMqttPublishConfig | FlowActionContextSetConfig | FlowActionLogConfig,
    Field(discriminator="type")
]

@dataclass
class FlowConfig:
    triggers: list[FlowTriggerConfig]
    actions: list[FlowActionConfig]
    name: str | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

@dataclass
class SubscriptionConfig:
    bus_name: str
    """bus_name pattern supporting * wildcards"""
    path: str
    """path pattern supporting * wildcards"""
    interfaces: list[InterfaceConfig] = field(default_factory=list)
    flows: list[FlowConfig] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

@dataclass
class DbusConfig:
    subscriptions: list[SubscriptionConfig]
    bus_type: Literal["SESSION", "SYSTEM"] = "SESSION"

    def is_bus_name_configured(self, bus_name: str) -> bool:

        for subscription in self.subscriptions:
            if fnmatch.fnmatchcase(bus_name, subscription.bus_name):
                return True
        return False

    def get_subscription_configs(self, bus_name: str, path: str|None = None) -> list[SubscriptionConfig]:
        res: list[SubscriptionConfig] = []
        for subscription in self.subscriptions:
            if fnmatch.fnmatchcase(bus_name, subscription.bus_name):
                if not path or path == subscription.path:
                    res.append(subscription)
                elif fnmatch.fnmatchcase(path, subscription.path):
                    res.append(subscription)
        return res

@dataclass
class MqttConfig:
    host: str
    username: str
    password: SecretStr
    port: int = 1883
    subscription_topics: list[str] = field(default_factory=lambda: ['dbus2mqtt/#'])

@dataclass
class Config:
    mqtt: MqttConfig
    dbus: DbusConfig
    flows: list[FlowConfig] = field(default_factory=list)
