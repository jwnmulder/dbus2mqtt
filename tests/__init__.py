from unittest.mock import AsyncMock, MagicMock, patch

import dbus_fast.aio as dbus_aio

from jsonargparse.typing import SecretStr

from dbus2mqtt import AppContext, config
from dbus2mqtt.config import FlowActionConfig, FlowConfig, FlowTriggerConfig, InterfaceConfig
from dbus2mqtt.dbus.dbus_client import DbusClient
from dbus2mqtt.dbus.dbus_types import BusNameSubscriptions
from dbus2mqtt.event_broker import EventBroker
from dbus2mqtt.flow.flow_processor import FlowProcessor
from dbus2mqtt.flow.flow_scheduler import FlowScheduler
from dbus2mqtt.mqtt.mqtt_client import MqttClient
from dbus2mqtt.template.templating import TemplateEngine


def mocked_app_context():

    test_config = config.Config(
        dbus=config.DbusConfig(
            subscriptions=[
                config.SubscriptionConfig(
                    bus_name="test.bus_name.*",
                    path="/",
                    interfaces=[InterfaceConfig(interface="test-interface-name")],
                )
            ]
        ),
        mqtt=config.MqttConfig(host="localhost", username="test", password=SecretStr("test")),
        flows=[],
    )

    event_broker = EventBroker()
    template_engine = TemplateEngine()
    app_context = AppContext(test_config, event_broker, template_engine)

    return app_context


def mocked_flow_processor(
    app_context: AppContext,
    triggers: list[FlowTriggerConfig],
    actions: list[FlowActionConfig],
    conditions: list[str] = [],
):

    flow_config = FlowConfig(triggers=triggers, actions=actions, conditions=conditions)

    app_context.config.dbus.subscriptions[0].flows = [flow_config]

    processor = FlowProcessor(app_context)
    return processor, flow_config


def mocked_dbus_client(app_context: AppContext):

    with patch("socket.socket", autospec=True):
        flow_scheduler = FlowScheduler(app_context)

        bus = dbus_aio.message_bus.MessageBus(bus_address="unix:path=/test-path")
        bus.unique_name = "FAKE-CONNECTION-NAME"

        dbus_client = DbusClient(app_context, flow_scheduler, bus)
        return dbus_client


def mocked_mqtt_client(app_context: AppContext) -> MqttClient:

    dbus_client = MqttClient(app_context, None)
    return dbus_client


def mocked_dbus_client_with_dbus_object(
    app_context, bus_name: str, path: str
) -> tuple[DbusClient, MagicMock]:

    dbus_client = mocked_dbus_client(app_context)

    dbus_client._subscriptions[bus_name] = BusNameSubscriptions(bus_name, ":1.1")

    interface = MagicMock()
    interface.bus_name = bus_name
    interface.path = path

    mocked_proxy_object = MagicMock()
    mocked_proxy_object.get_interface.return_value = interface

    dbus_client._subscriptions[bus_name].path_objects[path] = mocked_proxy_object

    return dbus_client, interface


def mocked_dbus_client_with_dbus_objects(
    app_context: AppContext,
) -> tuple[DbusClient, dict[str, MagicMock]]:

    dbus_objects = [
        ("org.mpris.MediaPlayer2.vlc", "/org/mpris/MediaPlayer2"),
        ("org.mpris.MediaPlayer2.firefox", "/org/mpris/MediaPlayer2"),
        ("org.mpris.MediaPlayer2.kodi", "/another/path/to/object"),
        ("org.freedesktop.Notifications", "/org/freedesktop/Notifications"),
    ]

    dbus_client = mocked_dbus_client(app_context)

    proxy_interfaces: dict[str, MagicMock] = {}
    for bus_name, path in dbus_objects:
        dbus_client._subscriptions[bus_name] = BusNameSubscriptions(
            bus_name, f":1:{len(proxy_interfaces)}"
        )

        interface = MagicMock()
        interface.bus_name = bus_name
        interface.path = path
        interface.call_test_method1 = AsyncMock()
        interface.call_test_method2 = AsyncMock()
        interface.call_invalid_test_method = AsyncMock()
        interface.call_notify = AsyncMock()
        interface.set_test_property1 = AsyncMock()
        interface.get_test_property1 = AsyncMock()

        mocked_proxy_object = MagicMock()
        mocked_proxy_object.get_interface.return_value = interface

        dbus_client._subscriptions[bus_name].path_objects[path] = mocked_proxy_object

        proxy_interfaces[bus_name] = interface

    return dbus_client, proxy_interfaces
