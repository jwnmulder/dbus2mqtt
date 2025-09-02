
from dbus2mqtt.template.templating import TemplateEngine


def test_preregisted_custom_function():

    # now is a custom dbus2mqtt function
    template = "now={{ now().isoformat() }}"

    templating = TemplateEngine()
    res = templating.render_template(template, object)

    assert isinstance(res, str)
    assert "now" in res

def test_non_template_str():
    templating = TemplateEngine()
    res = templating.render_template("str_value", object)
    assert res == "str_value"

def test_non_template_int_like():
    templating = TemplateEngine()
    res = templating.render_template("3", object)
    assert res == 3

def test_non_template_list_like():
    templating = TemplateEngine()
    res = templating.render_template("[1, 2, 3]", object)
    assert res == [1, 2, 3]

def test_str_template_str_result():
    templating = TemplateEngine()
    res = templating.render_template("{{ 'str_result' }}", object)
    assert res == "str_result"

def test_str_template_int_result():
    templating = TemplateEngine()
    res = templating.render_template("{{ 3 }}", object)
    assert res == 3

def test_str_template_list_result():
    templating = TemplateEngine()
    res = templating.render_template("{{ [1, 2, 3] }}", object)
    assert res == [1, 2, 3]

def test_str_template_int_result_as_str():
    templating = TemplateEngine()
    res = templating.render_template("{{ 3 }}", str)
    assert res == "3"

def test_none_result():
    templating = TemplateEngine()
    res = templating.render_template("{{ None }}", str)
    assert res is None

def test_dict_with_integer_expression():

    template = {
        "value": "{{ 1 | int }}",
    }

    templating = TemplateEngine()
    res = templating.render_template(template, dict)

    assert isinstance(res, dict)
    assert res["value"] == 1

def test_nested_dict_templates():

    nested_dict_template = {
        "a": 1,
        "b": {
            "c": "TestValueC"
        }
    }
    context = {
        "mpris_bus_names": ["org.mpris.MediaPlayer2.vlc", "org.mpris.MediaPlayer2.firefox"],
        "nested_dict_template": nested_dict_template
    }
    template = {
        "now": "{{ now().isoformat() }}",
        "dbus_names": "{{ mpris_bus_names }}",
        "nested_raw": nested_dict_template,
        "nested_template": "{{ nested_dict_template }}"
    }

    templating = TemplateEngine()
    res = templating.render_template(template, dict, context)

    assert isinstance(res, dict)

    test_dbus_names = res["dbus_names"]
    assert isinstance(test_dbus_names, list)
    assert len(test_dbus_names) == 2
    assert "org.mpris.MediaPlayer2.vlc" in res["dbus_names"]
    assert isinstance(res["now"], str)
    assert isinstance(res["nested_template"], dict)
    assert isinstance(res["nested_template"]["b"], dict)
    assert res["nested_template"]["b"]["c"] == "TestValueC"

def test_dict_template_with_quotes_and_newline():
    """
        Test that:
          1. a dict template with quotes and an ending newline is rendered correctly,
          2. dbus_call result with a nested dict is rendered correctly and convertible to a dict
    """
    custom_functions = {
        "dbus_list": lambda bus_name_pattern: ["org.mpris.MediaPlayer2.vlc", "org.mpris.MediaPlayer2.firefox"],
        "dbus_call": lambda bus_name, path, interface, method, method_args: {'Metadata': {}, 'Position': 0, 'CanControl': True},
        "dbus_property_get": lambda bus_name, path, interface, property, default_unsupported: {"value": 1}
    }

    templating = TemplateEngine()
    templating.add_functions(custom_functions)

    template = {
        "player_properties": "{{ dbus_call(mpris_bus_name, path, 'org.freedesktop.DBus.Properties', 'GetAll', ['org.mpris.MediaPlayer2.Player']) }}\n"
    }

    # This test is about the newline at the end of the string
    # assert to make sure it is there
    assert template["player_properties"].endswith("\n")

    res = templating.render_template(template, dict)

    assert isinstance(res, dict)
    assert isinstance(res["player_properties"], dict)
    assert res["player_properties"]["Position"] == 0

def test_nested_list_values():

    context = {
        "args": ["first-item", "second-item"]
    }
    template = {
        "res": {
            "plain_args": ["first-item", "second-item"],
            "args": "{{ args }}"
        }
    }

    templating = TemplateEngine()
    res = templating.render_template(template, dict, context)

    assert res["res"]["plain_args"] == ["first-item", "second-item"]
