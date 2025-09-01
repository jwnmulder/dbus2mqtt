from unittest.mock import AsyncMock, MagicMock

import pytest

import dbus2mqtt.config as config

from dbus2mqtt import AppContext
from dbus2mqtt.dbus.dbus_client import DbusClient
from dbus2mqtt.dbus.dbus_types import BusNameSubscriptions
from dbus2mqtt.event_broker import MqttMessage, MqttReceiveHints
from tests import mocked_app_context, mocked_dbus_client


@pytest.mark.asyncio
async def test_method_only():
    """ Mock contains 3 bus objects, test with valid method.
        Expect the method to be called 2 times, once for each bus object with matching subscription
    """
    mocked_proxy_interface = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={
                "method": "TestMethod2",
            }
        )
    )

    assert mocked_proxy_interface.call_test_method2.call_count == 2

@pytest.mark.asyncio
async def test_invalid_method():
    """ Mock contains 3 bus objects, test with invalid method.
        Expect the method to be called zero times
    """
    mocked_proxy_interface = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={
                "method": "InvalidTestMethod",
            }
        )
    )

    assert mocked_proxy_interface.call_invalid_test_method.call_count == 0

@pytest.mark.asyncio
async def test_method_with_bus_name():
    """ Mock contains 3 bus objects, test with valid method and valid bus_name.
        Expect the method to be called 1 time, once for each matching bus name and subscription
    """
    mocked_proxy_interface = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={
                "method": "TestMethod2",
                "bus_name": "org.mpris.MediaPlayer2.vlc"
            }
        )
    )

    assert mocked_proxy_interface.call_test_method2.call_count == 1

@pytest.mark.asyncio
async def test_method_with_bus_name_pattern():
    """ Mock contains 3 bus objects, test with valid method and valid bus_name.
        Expect the method to be called 1 time, once for each matching bus name and subscription
    """
    mocked_proxy_interface = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={
                "method": "TestMethod2",
                "bus_name": "*.vlc"
            }
        )
    )

    assert mocked_proxy_interface.call_test_method2.call_count == 1

@pytest.mark.asyncio
async def test_method_invalid_bus_name():
    """ Mock contains 3 bus objects, test with valid method and valid bus_name.
        Expect the method to be called zero times
    """
    mocked_proxy_interface = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={
                "method": "TestMethod2",
                "bus_name": "org.mpris.MediaPlayer2.non-existing"
            }
        )
    )

    assert mocked_proxy_interface.call_test_method2.call_count == 0

@pytest.mark.asyncio
async def test_method_with_path():
    """ Mock contains 3 bus objects, test with valid method and path.
        Expect the method to be called 2 times, once for each bus name with matching path and subscription
    """
    mocked_proxy_interface = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={
                "method": "TestMethod2",
                "path": "/org/mpris/MediaPlayer2"
            }
        )
    )

    assert mocked_proxy_interface.call_test_method2.call_count == 2

@pytest.mark.asyncio
async def test_method_with_path_pattern():
    """ Mock contains 3 bus objects, test with valid method and path.
        Expect the method to be called 2 times, once for each bus name with matching path and subscription
    """
    mocked_proxy_interface = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={
                "method": "TestMethod2",
                "path": "*/MediaPlayer2"
            }
        )
    )

    assert mocked_proxy_interface.call_test_method2.call_count == 2

@pytest.mark.asyncio
async def test_method_invalid_path():
    """ Mock contains 3 bus objects, test with valid method and invalid path.
        Expect the method to be called zero times
    """
    mocked_proxy_interface = await _publish_msg(
        MqttMessage(
            topic="dbus2mqtt/test/command",
            payload={
                "method": "TestMethod2",
                "path": "/invalid/path/to/object"
            }
        )
    )

    assert mocked_proxy_interface.call_test_method2.call_count == 0

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
                            config.MethodConfig(method="TestMethod2")
                        ]
                    )
                ]

            )
        ]
    return app_context

def _mocked_dbus_client(app_context: AppContext) -> tuple[DbusClient, MagicMock]:

    dbus_objects = [
        ("org.mpris.MediaPlayer2.vlc", "/org/mpris/MediaPlayer2"),
        ("org.mpris.MediaPlayer2.firefox", "/org/mpris/MediaPlayer2"),
        ("org.mpris.MediaPlayer2.kodi", "/another/path/to/object"),
    ]

    dbus_client = mocked_dbus_client(app_context)

    mocked_proxy_interface = MagicMock()
    mocked_proxy_interface.call_test_method1 = AsyncMock()
    mocked_proxy_interface.call_test_method2 = AsyncMock()
    mocked_proxy_interface.call_invalid_test_method = AsyncMock()

    index = 1
    for bus_name, path in dbus_objects:

        dbus_client.subscriptions[bus_name] = BusNameSubscriptions(bus_name, f":1:{index}")

        mocked_proxy_object = MagicMock()
        mocked_proxy_object.get_interface.return_value = mocked_proxy_interface

        dbus_client.subscriptions[bus_name].path_objects[path] = mocked_proxy_object

        index += 1

    return dbus_client, mocked_proxy_interface
