from unittest.mock import AsyncMock, MagicMock

import pytest

from dbus_fast import ArgDirection
from dbus_fast import introspection as intr

import dbus2mqtt.config as config

from dbus2mqtt import AppContext
from dbus2mqtt.dbus.dbus_client import DbusClient
from dbus2mqtt.dbus.dbus_types import BusNameSubscriptions
from dbus2mqtt.event_broker import MqttMessage, MqttReceiveHints
from tests import mocked_app_context, mocked_dbus_client


@pytest.mark.asyncio
async def test_method_only():
    """Mock contains 4 bus objects, test with specific topic and method.

    Expect the method to be called 2 times, once for each bus object with matching subscription
    """
    mocked_interfaces = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={
                "method": "TestMethod2",
            },
        )
    )

    assert sum(i.call_test_method2.call_count for i in mocked_interfaces) == 2


@pytest.mark.asyncio
async def test_invalid_method():
    """Mock contains 4 bus objects, test with valid topic and invalid method.

    Expect the method to be called zero times
    """
    mocked_interfaces = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={
                "method": "InvalidTestMethod",
            },
        )
    )

    assert sum(i.call_invalid_test_method.call_count for i in mocked_interfaces) == 0


@pytest.mark.asyncio
async def test_valid_method_on_wrong_topic():
    """Mock contains 4 bus objects, test with valid method and wrong topic.

    Expect the method to be called zero times
    """
    mocked_interfaces = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={
                "method": "Notify",
            },
        )
    )

    assert sum(i.call_notify.call_count for i in mocked_interfaces) == 0


@pytest.mark.asyncio
async def test_method_with_bus_name():
    """Mock contains 4 bus objects, test with valid topic, method and bus_name.

    Expect the method to be called 1 time, once for each matching bus name and subscription
    """
    mocked_interfaces = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={"method": "TestMethod2", "bus_name": "org.mpris.MediaPlayer2.vlc"},
        )
    )

    assert sum(i.call_test_method2.call_count for i in mocked_interfaces) == 1


@pytest.mark.asyncio
async def test_method_with_bus_name_pattern():
    """Mock contains 4 bus objects, test with valid topic, method and bus_name.

    Expect the method to be called 1 time, once for each matching bus name and subscription
    """
    mocked_interfaces = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command", payload={"method": "TestMethod2", "bus_name": "*.vlc"}
        )
    )

    assert sum(i.call_test_method2.call_count for i in mocked_interfaces) == 1


@pytest.mark.asyncio
async def test_method_invalid_bus_name():
    """Mock contains 4 bus objects, test with valid topic, method and invalid bus_name.

    Expect the method to be called zero times
    """
    mocked_interfaces = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={"method": "TestMethod2", "bus_name": "org.mpris.MediaPlayer2.non-existing"},
        )
    )

    assert sum(i.call_test_method2.call_count for i in mocked_interfaces) == 0


@pytest.mark.asyncio
async def test_method_with_path():
    """Mock contains 4 bus objects, test with valid topic, method and path.

    Expect the method to be called 2 times, once for each bus name with matching path and subscription
    """
    mocked_interfaces = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={"method": "TestMethod2", "path": "/org/mpris/MediaPlayer2"},
        )
    )

    assert sum(i.call_test_method2.call_count for i in mocked_interfaces) == 2


@pytest.mark.asyncio
async def test_method_with_path_pattern():
    """Mock contains 4 bus objects, test with valid topic, method and path.

    Expect the method to be called 2 times, once for each bus name with matching path and subscription
    """
    mocked_interfaces = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={"method": "TestMethod2", "path": "*/MediaPlayer2"},
        )
    )

    assert sum(i.call_test_method2.call_count for i in mocked_interfaces) == 2


@pytest.mark.asyncio
async def test_method_invalid_path():
    """Mock contains 4 bus objects, test with valid method and invalid path.

    Expect the method to be called zero times
    """
    mocked_interfaces = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={"method": "TestMethod2", "path": "/invalid/path/to/object"},
        )
    )

    assert sum(i.call_test_method2.call_count for i in mocked_interfaces) == 0


@pytest.mark.asyncio
async def test_method_command_response():
    """Tests that a successful dbus method call publishes a MQTT response."""
    app_context = _mocked_app_context()
    dbus_client, mocked_interfaces = _mocked_dbus_client(app_context)

    # Configure a response topic for the first interface
    app_context.config.dbus.subscriptions[0].interfaces[
        0
    ].mqtt_response_topic = "dbus2mqtt/test/command"

    mocked_interfaces[0].call_test_method2.return_value = "response-val"
    msg = MqttMessage(
        topic="dbus2mqtt/test/command",
        payload={
            "bus_name": "org.mpris.MediaPlayer2.vlc",
            "method": "TestMethod2",
            "args": ["arg0", 2],
        },
    )

    # Process message and check if message is published on the internal queue
    await dbus_client._on_mqtt_msg(msg, MqttReceiveHints())
    mqtt_message = app_context.event_broker.mqtt_publish_queue.sync_q.get_nowait()

    assert mqtt_message.payload.get("success")
    assert mqtt_message.payload["bus_name"] == "org.mpris.MediaPlayer2.vlc"
    assert mqtt_message.payload["path"] == "/org/mpris/MediaPlayer2"
    assert mqtt_message.payload["interface"] == "test-interface-name"
    assert mqtt_message.payload["method"] == "TestMethod2"
    assert mqtt_message.payload["args"] == ["arg0", 2]
    assert mqtt_message.payload["result"] == "response-val"


@pytest.mark.asyncio
async def test_method_kwargs_command_response():
    """Tests that a successful dbus method call publishes a MQTT response."""
    app_context = _mocked_app_context()
    dbus_client, mocked_interfaces = _mocked_dbus_client(app_context)

    # Configure a response topic for the first interface
    app_context.config.dbus.subscriptions[0].interfaces[
        0
    ].mqtt_response_topic = "dbus2mqtt/test/command"

    # Set introspection data
    mocked_interfaces[0].introspection.methods = [
        intr.Method(
            name="TestMethod2",
            in_args=[
                intr.Arg(name="arg0", signature="s", direction=ArgDirection.IN),
                intr.Arg(name="arg1", signature="i", direction=ArgDirection.IN),
            ],
        )
    ]

    mocked_interfaces[0].call_test_method2.return_value = "response-val"
    msg = MqttMessage(
        topic="dbus2mqtt/test/command",
        payload={
            "bus_name": "org.mpris.MediaPlayer2.vlc",
            "method": "TestMethod2",
            "kwargs": {"arg0": "val0", "arg1": 1},
        },
    )

    # Process message and check if message is published on the internal queue
    await dbus_client._on_mqtt_msg(msg, MqttReceiveHints())
    mqtt_message = app_context.event_broker.mqtt_publish_queue.sync_q.get_nowait()

    assert mqtt_message.payload.get("success")
    assert mqtt_message.payload["kwargs"] == {"arg0": "val0", "arg1": 1}


@pytest.mark.asyncio
async def test_property_command_response():
    """Tests that a successful dbus property call publishes a MQTT response."""
    app_context = _mocked_app_context()
    dbus_client, proxy_interface = _mocked_dbus_client(app_context)

    # Configure a response topic for the first interface
    app_context.config.dbus.subscriptions[0].interfaces[
        0
    ].mqtt_response_topic = "dbus2mqtt/test/command"

    msg = MqttMessage(
        topic="dbus2mqtt/test/command",
        payload={
            "bus_name": "org.mpris.MediaPlayer2.vlc",
            "property": "TestProperty1",
            "value": 0.9,
        },
    )

    # Process message and check if message is published on the internal queue
    await dbus_client._on_mqtt_msg(msg, MqttReceiveHints())
    mqtt_message = app_context.event_broker.mqtt_publish_queue.sync_q.get_nowait()

    assert mqtt_message.payload.get("success")
    assert mqtt_message.payload["bus_name"] == "org.mpris.MediaPlayer2.vlc"
    assert mqtt_message.payload["path"] == "/org/mpris/MediaPlayer2"
    assert mqtt_message.payload["interface"] == "test-interface-name"
    assert mqtt_message.payload["property"] == "TestProperty1"
    assert mqtt_message.payload["value"] == 0.9
    assert mqtt_message.payload["result"] == 0.9


async def _publish_msg(msg: MqttMessage):

    app_context = _mocked_app_context()
    dbus_client, proxy_interface = _mocked_dbus_client(app_context)
    hints = MqttReceiveHints()

    await dbus_client._on_mqtt_msg(msg, hints)

    return proxy_interface


def _mocked_app_context() -> AppContext:
    app_context = mocked_app_context()

    app_context.config.dbus.subscriptions = [
        config.SubscriptionConfig(
            bus_name="org.mpris.MediaPlayer2.*",
            path="/org/mpris/MediaPlayer2",
            interfaces=[
                config.InterfaceConfig(
                    interface="test-interface-name",
                    mqtt_command_topic="dbus2mqtt/test/command",
                    methods=[
                        config.MethodConfig(method="TestMethod1"),
                        config.MethodConfig(method="TestMethod2"),
                    ],
                    properties=[config.PropertyConfig(property="TestProperty1")],
                ),
                config.InterfaceConfig(
                    interface="org.freedesktop.Notifications",
                    mqtt_command_topic="dbus2mqtt/test/Notifications/command",
                    methods=[
                        config.MethodConfig(method="Notify"),
                        config.MethodConfig(method="TestMethod2"),
                    ],
                ),
            ],
        )
    ]
    return app_context


def _mocked_dbus_client(app_context: AppContext) -> tuple[DbusClient, list[MagicMock]]:

    dbus_objects = [
        ("org.mpris.MediaPlayer2.vlc", "/org/mpris/MediaPlayer2"),
        ("org.mpris.MediaPlayer2.firefox", "/org/mpris/MediaPlayer2"),
        ("org.mpris.MediaPlayer2.kodi", "/another/path/to/object"),
        ("org.freedesktop.Notifications", "/org/freedesktop/Notifications"),
    ]

    dbus_client = mocked_dbus_client(app_context)

    proxy_interfaces = []
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

        mocked_proxy_object = MagicMock()
        mocked_proxy_object.get_interface.return_value = interface

        dbus_client._subscriptions[bus_name].path_objects[path] = mocked_proxy_object

        proxy_interfaces.append(interface)

    return dbus_client, proxy_interfaces
