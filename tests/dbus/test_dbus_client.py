
import dbus_fast.introspection as dbus_intr
import dbus_fast.signature as dbus_signature
import pytest

from dbus_fast.constants import ArgDirection

from tests import mocked_app_context, mocked_dbus_client


@pytest.mark.asyncio
async def test_signal_handler_unwrap_args():

    app_context = mocked_app_context()
    dbus_client = mocked_dbus_client(app_context)

    dbus_signal = dbus_intr.Signal("PropertiesChanged", [
        dbus_intr.Arg(name="interface_name", signature="s", direction=ArgDirection.IN),
        dbus_intr.Arg(name="changed_properties", signature="a{sv}", direction=ArgDirection.IN),
        dbus_intr.Arg(name="invalidated_properties", signature="as", direction=ArgDirection.IN)
    ])

    dbus_signal_state = {}
    dbus_signal_state = {
        "bus_name": "org.mpris.MediaPlayer2.vlc",
        "path": "/org/mpris/MediaPlayer2",
        "interface_name": "org.freedesktop.DBus.Properties",
        "signal_subscriptions": [{
            "subscription_config": None,
            "signal_config": None
        }]
    }

    handler = dbus_client._dbus_fast_signal_handler(dbus_signal, dbus_signal_state)
    assert handler is not None

    args = [
        "org.mpris.MediaPlayer2.Player",
        {
            "CanPause": dbus_signature.Variant("b", True)
        },
        []
    ]

    # Invoke with wrapped arguments
    handler(*args)

    # Check if message is published on the internal queue
    mqtt_message = dbus_client._dbus_signal_queue.sync_q.get_nowait()

    # message args should be unwrapped
    assert mqtt_message is not None
    assert mqtt_message.args == ["org.mpris.MediaPlayer2.Player", {"CanPause": True}, []]
