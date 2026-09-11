from datetime import tzinfo

from tzlocal import get_localzone

from dbus2mqtt.config import Config
from dbus2mqtt.event_broker import EventBroker
from dbus2mqtt.template.templating import TemplateEngine


class AppContext:
    def __init__(self, config: Config, event_broker: EventBroker, templating: TemplateEngine):
        self.config = config
        self.event_broker = event_broker
        self.templating = templating

        self.timezone: tzinfo = get_localzone()
