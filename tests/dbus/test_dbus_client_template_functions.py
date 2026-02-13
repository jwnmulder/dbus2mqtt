import pytest

from dbus2mqtt.template.dbus_template_functions import jinja_custom_dbus_functions
from tests import mocked_app_context, mocked_dbus_client_with_dbus_objects


@pytest.mark.asyncio
async def test_dbus_list():
    """Test dbus template function: dbus_list."""
    app_context = mocked_app_context()
    dbus_client, _ = mocked_dbus_client_with_dbus_objects(app_context)
    app_context.templating.add_functions(
        jinja_custom_dbus_functions(dbus_client, app_context.flow_state)
    )

    # pattern: match all
    template = "{{ dbus_list('*') }}"
    res = await app_context.templating.async_render_template(template, list, {})

    assert isinstance(res, list)
    assert "org.mpris.MediaPlayer2.vlc" in res
    assert "org.freedesktop.Notifications" in res

    # pattern: match single
    template = "{{ dbus_list('org.mpris.MediaPlayer2.vlc') }}"
    res = await app_context.templating.async_render_template(template, list, {})

    assert isinstance(res, list)
    assert len(res) == 1
    assert "org.mpris.MediaPlayer2.vlc" in res

    # pattern: match multiple
    template = "{{ dbus_list('org.mpris.MediaPlayer2.*') }}"
    res = await app_context.templating.async_render_template(template, list, {})

    assert isinstance(res, list)
    assert len(res) > 1
    assert "org.freedesktop.Notifications" not in res
    assert "org.mpris.MediaPlayer2.vlc" in res


@pytest.mark.asyncio
async def test_dbus_call():
    """Test dbus template function: dbus_call."""
    app_context = mocked_app_context()
    dbus_client, interfaces = mocked_dbus_client_with_dbus_objects(app_context)
    app_context.templating.add_functions(
        jinja_custom_dbus_functions(dbus_client, app_context.flow_state)
    )

    mocked_interface = interfaces["org.mpris.MediaPlayer2.firefox"]
    mocked_interface.call_test_method1.return_value = "response-val"

    template = "{{ dbus_call('org.mpris.MediaPlayer2.firefox', '/org/mpris/MediaPlayer2', 'any.interface', 'TestMethod1', []) }}"
    res = await app_context.templating.async_render_template(template, str, {})

    assert res == "response-val"


@pytest.mark.asyncio
async def test_dbus_property_get():
    """Test dbus template function: dbus_property_get."""
    app_context = mocked_app_context()
    dbus_client, interfaces = mocked_dbus_client_with_dbus_objects(app_context)
    app_context.templating.add_functions(
        jinja_custom_dbus_functions(dbus_client, app_context.flow_state)
    )

    mocked_interface = interfaces["org.mpris.MediaPlayer2.firefox"]
    mocked_interface.get_test_property1.return_value = "response-val"

    template = "{{ dbus_property_get('org.mpris.MediaPlayer2.firefox', '/org/mpris/MediaPlayer2', 'any.interface', 'TestProperty1') }}"
    res = await app_context.templating.async_render_template(template, str, {})

    assert res == "response-val"


@pytest.mark.asyncio
async def test_dbus_contexts_function():

    app_context = mocked_app_context()
    dbus_client, proxy_interfaces = mocked_dbus_client_with_dbus_objects(app_context)
    app_context.templating.add_functions(
        jinja_custom_dbus_functions(dbus_client, app_context.flow_state)
    )

    # signature (bus_name_pattern: str, path_pattern: str)
    template = "{{ dbus_contexts('*', '*') }}"

    res = await app_context.templating.async_render_template(template, list)

    assert len(res) > 0
    # assert len(res) == len(proxy_interfaces)
