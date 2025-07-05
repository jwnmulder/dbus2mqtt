
from unittest.mock import patch

import dbus_fast.aio as dbus_aio

from pydantic import SecretStr

from dbus2mqtt import AppContext, config
from dbus2mqtt.config import (
    FlowActionConfig,
    FlowConfig,
    FlowTriggerConfig,
    InterfaceConfig,
)
from dbus2mqtt.dbus.dbus_client import DbusClient
from dbus2mqtt.event_broker import EventBroker
from dbus2mqtt.flow.flow_processor import FlowProcessor, FlowScheduler
from dbus2mqtt.template.templating import TemplateEngine


def mocked_app_context():

    test_config = config.Config(dbus=config.DbusConfig(
        subscriptions=[
            config.SubscriptionConfig(
                bus_name="test.bus_name.*",
                path="/",
                interfaces=[
                    InterfaceConfig(
                        interface="test-interface-name"
                    )
                ]

            )
        ]
    ),
    mqtt=config.MqttConfig(
        host="localhost",
        username="test",
        password=SecretStr("test")
    ),
    flows=[]
    )

    event_broker = EventBroker()
    template_engine = TemplateEngine()
    app_context = AppContext(test_config, event_broker, template_engine)

    return app_context

def mocked_flow_processor(app_context: AppContext, trigger_config: FlowTriggerConfig, actions: list[FlowActionConfig]):

    flow_config = FlowConfig(triggers=[trigger_config], actions=actions)

    app_context.config.dbus.subscriptions[0].flows = [flow_config]

    processor = FlowProcessor(app_context)
    return processor, flow_config

def mocked_dbus_client(app_context: AppContext):

    with patch("socket.socket", autospec=True):

        bus = dbus_aio.message_bus.MessageBus(bus_address="unix:path=/test-path")
        flow_scheduler = FlowScheduler(app_context)

        dbus_client = DbusClient(app_context, bus, flow_scheduler)
        return dbus_client
