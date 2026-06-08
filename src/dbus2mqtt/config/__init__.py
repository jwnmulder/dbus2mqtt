import fnmatch
import uuid
import warnings

from dataclasses import dataclass, field
from typing import Any, Literal

from jsonargparse.typing import SecretStr

from dbus2mqtt.template.templating import TemplateEngine


@dataclass
class SignalConfig:
    signal: str
    filter: str | None = None  # Deprecate this?, see #280

    def matches_filter(self, template_engine: TemplateEngine, *args) -> bool:
        if self.filter:
            return template_engine.render_template(self.filter, bool, {"args": args})
        return True


@dataclass
class MethodConfig:
    method: str


@dataclass
class PropertyConfig:
    property: str


@dataclass
class InterfaceConfig:
    """Subscription Interface config.

    Attributes:
        interface: The D-Bus interface that defines the set of methods, signals, and properties available.
        mqtt_command_topic: MQTT topic where dbus2mqtt listens for JSON commands. For example 'dbus2mqtt/mpris/command'. Value can be a string or templated string.
        mqtt_response_topic: MQTT topic where dbus2mqtt published responses on. For example 'dbus2mqtt/mpris/response'. Value can be a string or templated string.
        signals: List of D-Bus signals to subscribe to.
        methods: List of methods to expose over MQTT.
        properties: List of properties to expose over MQTT.
    """

    interface: str
    mqtt_command_topic: str | None = None
    mqtt_response_topic: str | None = None
    signals: list[SignalConfig] = field(default_factory=list)
    methods: list[MethodConfig] = field(default_factory=list)
    properties: list[PropertyConfig] = field(default_factory=list)

    def render_mqtt_command_topic(
        self, template_engine: TemplateEngine, context: dict[str, Any]
    ) -> Any:
        if self.mqtt_command_topic:
            return template_engine.render_template(self.mqtt_command_topic, str, context)
        return None

    def render_mqtt_response_topic(
        self, template_engine: TemplateEngine, context: dict[str, Any]
    ) -> str | None:
        if self.mqtt_response_topic:
            return template_engine.render_template(self.mqtt_response_topic, str, context)
        return None


@dataclass
class FlowTriggerScheduleConfig:
    type: Literal["schedule"] = "schedule"
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    cron: dict[str, Any] | None = None
    interval: dict[str, Any] | None = None


@dataclass
class FlowTriggerDbusSignalConfig:
    """Configuration for 'dbus_signal' flow trigger.

    Attributes:
        interface: Interface to filter on, e.g. 'org.freedesktop.DBus.Properties'.
        signal: Signal name to filter on, e.g. PropertiesChanged.
        bus_name: undocumented, not used.
        path: undocumented, not used.
    """

    signal: str
    type: Literal["dbus_signal"] = "dbus_signal"
    interface: str | None = None
    bus_name: str | None = None
    path: str | None = None

    def __post_init__(self):
        if self.bus_name:
            warnings.warn(
                f"{self.type} attribute 'bus_name' is not yet implemented.",
                UserWarning,
                stacklevel=2,
            )
        if self.path:
            warnings.warn(
                f"{self.type} attribute 'path' is not yet implemented.", UserWarning, stacklevel=2
            )


@dataclass
class FlowTriggerBusNameAddedConfig:
    """Configuration for 'bus_name_adde' flow trigger (DEPRECATED)."""

    type: Literal["bus_name_added"] = "bus_name_added"

    def __post_init__(self):
        warnings.warn(
            f"{self.type} flow trigger may be removed in a future version.",
            FutureWarning,
            stacklevel=2,
        )


@dataclass
class FlowTriggerBusNameRemovedConfig:
    """Configuration for 'bus_name_removed' flow trigger (DEPRECATED)."""

    type: Literal["bus_name_removed"] = "bus_name_removed"

    def __post_init__(self):
        warnings.warn(
            f"{self.type} flow trigger may be removed in a future version.",
            FutureWarning,
            stacklevel=2,
        )


@dataclass
class FlowTriggerDbusObjectAddedConfig:
    """Configuration for 'dbus_object_added' flow trigger."""

    type: Literal["dbus_object_added", "object_added"] = "dbus_object_added"

    def __post_init__(self):
        if self.type != FlowTriggerDbusObjectAddedConfig.type:
            warnings.warn(
                f"Trigger `{self.type}` has been renamed to '{FlowTriggerDbusObjectAddedConfig.type}' and might be removed in a future version.",
                FutureWarning,
                stacklevel=2,
            )
            self.type = FlowTriggerDbusObjectAddedConfig.type


@dataclass
class FlowTriggerDbusObjectRemovedConfig:
    """Configuration for 'dbus_object_removed' flow trigger."""

    type: Literal["dbus_object_removed", "object_removed"] = "dbus_object_removed"

    def __post_init__(self):
        if self.type != FlowTriggerDbusObjectRemovedConfig.type:
            warnings.warn(
                f"Trigger `{self.type}` has been renamed to '{FlowTriggerDbusObjectRemovedConfig.type}' and might be removed in a future version.",
                FutureWarning,
                stacklevel=2,
            )
            self.type = FlowTriggerDbusObjectRemovedConfig.type


@dataclass
class FlowTriggerMqttMessageConfig:
    """Configuration for 'mqtt_message' flow trigger.

    Attributes:
        topic: MQTT topic for the trigger.
        content_type: Expected payload format, 'json' or 'text'.
        filter: Optional template expression, trigger only when it evaluates truthy.
    """

    topic: str
    type: Literal["mqtt_message"] = "mqtt_message"
    content_type: Literal["json", "text"] = "json"
    filter: str | None = None

    def matches_filter(
        self, template_engine: TemplateEngine, trigger_context: dict[str, Any]
    ) -> bool:
        if self.filter:
            return template_engine.render_template(self.filter, bool, trigger_context)
        return True


@dataclass
class FlowTriggerContextChangedConfig:
    """Configuration for 'context_changed' flow trigger."""

    type: Literal["context_changed"] = "context_changed"
    scope: Literal["global"] = "global"


FlowTriggerConfig = (
    FlowTriggerContextChangedConfig
    | FlowTriggerBusNameAddedConfig
    | FlowTriggerBusNameRemovedConfig
    | FlowTriggerDbusObjectAddedConfig
    | FlowTriggerDbusObjectRemovedConfig
    | FlowTriggerDbusSignalConfig
    | FlowTriggerMqttMessageConfig
    | FlowTriggerScheduleConfig
)


@dataclass
class FlowActionContextSetConfig:
    """Configuration for 'context_set' flow action.

    Attributes:
        context: Per flow execution context.
        global_context: Global context, shared between multiple flow executions, over all subscriptions.
    """

    type: Literal["context_set"] = "context_set"
    context: dict[str, Any] | None = None
    global_context: dict[str, Any] | None = None


@dataclass
class FlowActionMqttPublishConfig:
    """Configuration for 'mqtt_publish' flow action.

    Attributes:
        topic: MQTT topic the messaage is published to
        payload_template: A string, a dict of strings, a templated string or a nested dict of templated strings
        payload_type: Message format for MQTT: json (default), yaml, text or binary. When set to binary, payload_template is expected to return a url formatted string where scheme is either file, http or https
    """

    topic: str
    payload_template: str | dict[str, Any]
    type: Literal["mqtt_publish"] = "mqtt_publish"
    payload_type: Literal["json", "yaml", "text", "binary"] = "json"


@dataclass
class FlowActionLogConfig:
    """Configuration for 'log' flow action.

    Attributes:
        msg: Message to log, a string or templated string.
        level: Log level, defaults to INFO.
    """

    msg: str
    type: Literal["log"] = "log"
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


FlowActionConfig = FlowActionMqttPublishConfig | FlowActionContextSetConfig | FlowActionLogConfig


@dataclass
class FlowConfig:
    """Flow configuration.

    Attributes:
        name: Optional human-readable name for the flow.
        triggers: Trigger configurations that start the flow.
        actions: Actions executed when the flow runs.
        conditions: Optional condition or list of conditions that must be met before a flow is executed.
        id: Unique flow identifier, automatically generated UUID.
    """

    triggers: list[FlowTriggerConfig]
    actions: list[FlowActionConfig]
    conditions: str | list[str] = field(default_factory=list)
    name: str | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass
class SubscriptionConfig:
    """Configuration for a D-Bus subscription.

    Attributes:
        bus_name: Bus name pattern, supporting '*' wildcards.
        path: Object path pattern, supporting '*' wildcards.
        interfaces: List of dbus2mqtt interface configurations.
        flows: List of dbus2mqtt flow configurations.
        id: Unique subscription identifier, automatically generated UUID.
    """

    bus_name: str
    path: str
    interfaces: list[InterfaceConfig] = field(default_factory=list)
    flows: list[FlowConfig] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def matches_dbus_object(self, bus_name: str, path: str | None = None) -> bool:
        matches = fnmatch.fnmatchcase(bus_name, self.bus_name)
        if path:
            matches &= path == self.path or fnmatch.fnmatchcase(path, self.path)
        return matches


@dataclass
class DbusConfig:
    """D-Bus configuration.

    Attributes:
        bus_type: Bus to connect to.
        subscriptions: List of SubscriptionConfig.
    """

    subscriptions: list[SubscriptionConfig]
    bus_type: Literal["SESSION", "SYSTEM"] = "SESSION"

    def is_bus_name_configured(self, bus_name: str) -> bool:

        for subscription in self.subscriptions:
            if fnmatch.fnmatchcase(bus_name, subscription.bus_name):
                return True
        return False

    def get_subscription_configs(
        self, bus_name: str, path: str | None = None
    ) -> list[SubscriptionConfig]:
        res: list[SubscriptionConfig] = []
        for subscription in self.subscriptions:
            if subscription.matches_dbus_object(bus_name, path):
                res.append(subscription)
        return res


@dataclass
class MqttConfig:
    """MQTT configuration.

    Attributes:
        host: MQTT broker hostname or IP address.
        username: Username for broker authentication.
        password: Password for broker authentication.
        port: MQTT broker TCP port.
        subscription_topics: List of MQTT topics to subscribe to. Wildcard characters '#' and '+' are supported.
    """

    host: str
    username: str
    password: SecretStr
    port: int = 1883
    subscription_topics: list[str] = field(default_factory=lambda: ["dbus2mqtt/#"])


@dataclass
class Config:
    """App configuration."""

    dbus: DbusConfig
    mqtt: MqttConfig
    flows: list[FlowConfig] = field(default_factory=list)
