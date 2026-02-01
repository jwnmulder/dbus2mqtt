from dbus2mqtt.config import Config
from dbus2mqtt.event_broker import EventBroker
from dbus2mqtt.flow.flow_state import FlowState
from dbus2mqtt.template.templating import TemplateEngine


class AppContext:
    def __init__(
        self,
        config: Config,
        event_broker: EventBroker,
        templating: TemplateEngine,
        flow_state: FlowState,
    ):
        self.config = config
        self.event_broker = event_broker
        self.templating = templating
        self.flow_state = flow_state
