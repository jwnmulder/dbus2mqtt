import pytest
import yaml

from dbus2mqtt.template.templating import TemplateEngine


def test_non_template_dict_result():

    config = yaml.safe_load("""
        payload_template:
            a_string: "Off"
            a_number: 5
    """)

    templating = TemplateEngine()
    res = templating.render_template(config["payload_template"], dict)

    assert res["a_string"] == "Off"
    assert res["a_number"] == 5

@pytest.mark.asyncio
async def test_signal_filter_bool_result():

    config = yaml.safe_load("""
        signals:
            - signal: PropertiesChanged
              filter: "{{ args[0] == 'org.mpris.MediaPlayer2.Player' }}"
    """)

    templating = TemplateEngine()
    context = {
        "args": ["org.mpris.MediaPlayer2.Player", {}, []]
    }

    res = await templating.async_render_template(config["signals"][0]["filter"], bool, context)

    assert res

@pytest.mark.asyncio
async def test_str_template_with_dict_result():
    """Test a more complex example where functions are returning dicts
    and everything must be bcomined in a nice single structure that can be converted to json"""

    config = yaml.safe_load("""
        actions:
          - type: mqtt_publish
            topic: dbus2mqtt/org.mpris.MediaPlayer2/state
            payload_template: |
                {{
                    { 'bus_name': mpris_bus_name }
                    | combine(dbus_call(mpris_bus_name, path, 'org.freedesktop.DBus.Properties', 'GetAll', ['org.mpris.MediaPlayer2.Player']))
                    | combine({ 'Volume': dbus_property_get(mpris_bus_name, path, 'org.mpris.MediaPlayer2.Player', 'Volume', 0) })
                }}
    """)

    templating = TemplateEngine()

    async def mock_dbus_property_get(bus_name, path, interface, property, default_unsupported):
        return 50

    async def mock_dbus_call(bus_name, path, interface, method, method_args):
        return {
            "CanPlay": False,
            "CanSeek": False,
            "LoopStatus": "None",
            "MaximumRate": 32.0,
            "Metadata": {
                "mpris:trackid": "/org/mpris/MediaPlayer2/firefox",
            },
            "MinimumRate": 0.032,
            "PlaybackStatus": "Stopped",
            "Position": 0,
            "Rate": 1.0,
            "Shuffle": False
        }

    context = {
        "mpris_bus_name": "org.mpris.MediaPlayer2.Player.firefox",
        "dbus_call": mock_dbus_call,
        "dbus_property_get": mock_dbus_property_get
    }

    res = await templating.async_render_template(config["actions"][0]["payload_template"], dict, context)

    assert res["bus_name"] == "org.mpris.MediaPlayer2.Player.firefox"
    assert res["Metadata"]["mpris:trackid"] == "/org/mpris/MediaPlayer2/firefox"
    assert res["Volume"] == 50
