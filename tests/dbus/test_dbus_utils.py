import pytest

from dbus_fast import SignatureTree, Variant

from dbus2mqtt.dbus.dbus_util import (
    _convert_and_wrap_in_variant,
    convert_mqtt_args_to_dbus,
)


class TestConvertMqttArgsToDbus:
    """Test suite for convert_mqtt_args_to_dbus function"""

    def test_empty_args_list(self):
        """Test conversion of empty arguments list"""
        result = convert_mqtt_args_to_dbus([])
        assert result == []

    def test_primitive_types_passthrough(self):
        """Test that primitive types (bool, int, float, str) pass through unchanged"""
        args = [True, 42, 3.14, "hello", None]
        result = convert_mqtt_args_to_dbus(args)

        assert result[0] is True
        assert result[1] == 42
        assert result[2] == 3.14
        assert result[3] == "hello"
        assert result[4] is None

    def test_simple_dict_conversion(self):
        """Test conversion of simple dictionary to D-Bus format"""
        args = [{"key1": "value1", "key2": 42}]
        result = convert_mqtt_args_to_dbus(args)

        assert len(result) == 1
        assert isinstance(result[0], dict)

        dict_value = result[0]
        assert dict_value["key1"] == Variant("s", "value1")
        assert dict_value["key2"].value == 42

    def test_nested_dict_conversion(self):
        """Test conversion of nested dictionary structures"""
        args = [{"outer": {"inner": "value", "number": 123}}]
        result = convert_mqtt_args_to_dbus(args)

        assert len(result) == 1
        assert isinstance(result[0], dict)

        outer_dict = result[0]
        assert "outer" in outer_dict
        assert isinstance(outer_dict["outer"], Variant)

        inner_dict = outer_dict["outer"].value
        assert inner_dict["inner"].value == "value"
        assert inner_dict["number"].value == 123

    def test_simple_list_conversion(self):
        """Test conversion of simple lists"""
        args = [[1, 2, 3], ["a", "b", "c"]]
        result = convert_mqtt_args_to_dbus(args)

        assert len(result) == 2
        assert result[0] == [1, 2, 3]  # Lists of primitives pass through
        assert result[1] == ["a", "b", "c"]

    def test_list_with_complex_items(self):
        """Test conversion of lists containing dictionaries"""
        args = [[{"key": "value"}, {"another": "item"}]]
        result = convert_mqtt_args_to_dbus(args)

        assert len(result) == 1
        assert isinstance(result[0], list)
        assert len(result[0]) == 2

        # Each dict in the list should be wrapped in Variant
        assert result[0][0] == {"key": Variant("s", "value")}
        assert result[0][1] == {"another": Variant("s", "item")}

    def test_mixed_argument_types(self):
        """Test conversion of mixed argument types in a single call"""
        args = [
            "string_arg",
            42,
            True,
            {"dict_key": "dict_value"},
            [1, 2, 3],
            None
        ]
        result = convert_mqtt_args_to_dbus(args)

        assert len(result) == 6
        assert result[0] == "string_arg"    # string passthrough
        assert result[1] == 42              # int passthrough
        assert result[2] is True            # bool passthrough
        assert isinstance(result[3], dict)  # dict wrapped
        assert result[4] == [1, 2, 3]       # list passthrough
        assert result[5] is None            # None passthrough

    def test_boolean_values(self):
        """Test specific boolean value handling"""
        args = [True, False]
        result = convert_mqtt_args_to_dbus(args)

        assert result[0] is True
        assert result[1] is False

    def test_numeric_values(self):
        """Test various numeric value types"""
        args = [0, -1, 42, 3.14159, -2.5, 0.0]
        result = convert_mqtt_args_to_dbus(args)

        assert result[0] == 0
        assert result[1] == -1
        assert result[2] == 42
        assert result[3] == 3.14159
        assert result[4] == -2.5
        assert result[5] == 0.0

    def test_string_values(self):
        """Test string value handling including special cases"""
        args = ["", "hello", "with spaces", "with\nnewlines"]
        result = convert_mqtt_args_to_dbus(args)

        assert result[0] == ""
        assert result[1] == "hello"
        assert result[2] == "with spaces"
        assert result[3] == "with\nnewlines"

    def test_empty_dict_conversion(self):
        """Test conversion of empty dictionary"""
        args = [{}]
        result = convert_mqtt_args_to_dbus(args)

        assert len(result) == 1
        assert result[0] == {}

    def test_empty_list_conversion(self):
        """Test conversion of empty list"""
        args = [[]]
        result = convert_mqtt_args_to_dbus(args)

        assert len(result) == 1
        assert result[0] == []

    def test_desktop_notification_structure(self):
        """Test conversion of desktop notification payload.

            Reference PR: https://github.com/jwnmulder/dbus2mqtt/pull/126

            - bus_name=org.freedesktop.Notifications
            - interface=org.freedesktop.Notifications
            - method=Notify
            - signature:
            .. code-block:: xml
                <arg type="s" name="app_name" direction="in"/>
                <arg type="u" name="replaces_id" direction="in"/>
                <arg type="s" name="app_icon" direction="in"/>
                <arg type="s" name="summary" direction="in"/>
                <arg type="s" name="body" direction="in"/>
                <arg type="as" name="actions" direction="in"/>
                <arg type="a{sv}" name="hints" direction="in"/>
                <arg type="i" name="expire_timeout" direction="in"/>
                <arg type="u" name="id" direction="out"/>
        """

        signature_tree = SignatureTree("susssasa{sv}i")
        args=[
            "dbus2mqtt",
            0,
            "dialog-information",
            "dbus2mqtt",
            "Message from <b><i>dbus2mqtt</i></b>",
            [],
            { "urgency": 1, "category": "device" },
            5000
        ]
        converted_args = convert_mqtt_args_to_dbus(args)

        signature_tree.verify(converted_args)

        assert converted_args[0] == "dbus2mqtt"  # app_name
        assert converted_args[1] == 0  # replaces_id
        assert converted_args[2] == "dialog-information"  # app_icon
        assert converted_args[3] == "dbus2mqtt"  # summary
        assert converted_args[4] == "Message from <b><i>dbus2mqtt</i></b>"  # body
        assert converted_args[5] == []  # actions
        assert converted_args[6] == {
            "urgency": Variant("q", 1),
            "category": Variant("s", "device")
        }  # hints
        assert converted_args[7] == 5000  # expire_timeout


class TestConvertAndWrapInVariant:
    """Test suite for _convert_and_wrap_in_variant helper function"""

    def test_none_value(self):
        """Test None value handling"""
        result = _convert_and_wrap_in_variant(None)
        assert result is None

    def test_primitive_types(self):
        """Test primitive types pass through unchanged"""
        assert _convert_and_wrap_in_variant(True) is True
        assert _convert_and_wrap_in_variant(42) == 42
        assert _convert_and_wrap_in_variant(3.14) == 3.14
        assert _convert_and_wrap_in_variant("hello") == "hello"

    def test_dict_wrapping(self):
        """Test dictionary gets wrapped in Variant"""
        test_dict = {"key": "value", "number": 42}
        result = _convert_and_wrap_in_variant(test_dict)

        assert isinstance(result, dict)

        assert result["key"].value == "value"
        assert result["number"].value == 42

    def test_list_with_primitives(self):
        """Test list with primitive values"""
        test_list = [1, 2, 3]
        result = _convert_and_wrap_in_variant(test_list)

        assert isinstance(result, list)
        assert result == [1, 2, 3]

    def test_list_with_dicts(self):
        """Test list containing dictionaries"""
        test_list = [{"a": 1}, {"b": 2}]
        result = _convert_and_wrap_in_variant(test_list)

        assert isinstance(result, list)
        assert len(result) == 2

        assert isinstance(result[0], dict)
        assert result[0] == {"a": Variant("q", 1)}
        assert result[1] == {"b": Variant("q", 2)}


class TestIntegrationScenarios:
    """Integration tests for real-world usage scenarios"""

    def test_mpris_metadata_structure(self):
        """Test conversion of MPRIS-like metadata structure"""

        signature_tree = SignatureTree("a{sv}")
        args = [{
            "xesam:title": "Song Title",
            "xesam:artist": ["Artist Name"],
            "xesam:album": "Album Name",
            "mpris:length": 180000000,  # microseconds
            "mpris:trackid": "/org/mpris/MediaPlayer2/Track/1"
        }]

        result = convert_mqtt_args_to_dbus(args)
        signature_tree.verify(result)

        assert len(result) == 1
        assert isinstance(result[0], dict)

        metadata = result[0]
        assert metadata["xesam:title"].value == "Song Title"
        assert metadata["xesam:artist"].value == ["Artist Name"]
        assert metadata["xesam:album"].value == "Album Name"
        assert metadata["mpris:length"].value == 180000000
        assert metadata["mpris:trackid"].value == "/org/mpris/MediaPlayer2/Track/1"

    def test_method_call_with_multiple_args(self):
        """Test method call with multiple different argument types"""

        signature_tree = SignatureTree("oxa{sv}")
        args = [
            "/org/mpris/MediaPlayer2/Track/1",  # object path
            180000000,                          # position in microseconds
            {"metadata": {"title": "New Song"}} # metadata dict
        ]

        result = convert_mqtt_args_to_dbus(args)
        signature_tree.verify(result)

        assert len(result) == 3
        assert result[0] == "/org/mpris/MediaPlayer2/Track/1"  # string passthrough
        assert result[1] == 180000000                          # int passthrough
        assert isinstance(result[2], dict)                     # dict wrapped

    def test_property_set_with_complex_value(self):
        """Test setting a property with a complex value"""

        signature_tree = SignatureTree("a{sv}")
        args = [{
            "Volume": 0.8,
            "LoopStatus": "None",
            "Metadata": {
                "xesam:title": "Test Song",
                "xesam:artist": ["Test Artist"]
            }
        }]

        result = convert_mqtt_args_to_dbus(args)
        signature_tree.verify(result)

        assert len(result) == 1
        assert isinstance(result[0], dict)

        properties = result[0]
        assert properties["Volume"].value == 0.8
        assert properties["LoopStatus"].value == "None"
        assert isinstance(properties["Metadata"], Variant)

        metadata = properties["Metadata"].value
        assert metadata["xesam:title"].value == "Test Song"
        assert metadata["xesam:artist"].value == ["Test Artist"]

    def test_list_of_mixed_types(self):
        """Test list containing mixed primitive and complex types"""
        args = [[
            "string",
            42,
            {"dict_item": "value"},
            True,
            [1, 2, 3]
        ]]

        result = convert_mqtt_args_to_dbus(args)

        assert len(result) == 1
        assert isinstance(result[0], list)
        assert len(result[0]) == 5

        list_items = result[0]
        assert list_items[0] == "string"        # string passthrough
        assert list_items[1] == 42              # int passthrough
        assert isinstance(list_items[2], dict)  # dict wrapped
        assert list_items[3] is True            # bool passthrough
        assert list_items[4] == [1, 2, 3]       # list passthrough

    def test_edge_case_empty_structures(self):
        """Test edge cases with empty structures"""
        args = [{}, [], ""]
        result = convert_mqtt_args_to_dbus(args)

        assert len(result) == 3
        assert isinstance(result[0], dict)     # empty dict wrapped
        assert result[0] == {}
        assert result[1] == []                 # empty list passthrough
        assert result[2] == ""                 # empty string passthrough

    def test_large_numbers(self):
        """Test handling of large numbers that might affect D-Bus signature selection"""
        args = [
            65535,      # UINT16_MAX
            65536,      # > UINT16_MAX
            2147483647, # INT32_MAX
            2147483648, # > INT32_MAX
            -2147483648, # INT32_MIN
            -2147483649  # < INT32_MIN
        ]

        result = convert_mqtt_args_to_dbus(args)

        # All should pass through as integers
        for i, expected in enumerate(args):
            assert result[i] == expected

    def test_deeply_nested_lists_and_dicts(self):
        """Test deeply nested structures"""
        args = [[
            {
                "level1": [
                    {
                        "level2": {
                            "level3": ["deep", "nesting"]
                        }
                    }
                ]
            }
        ]]

        result = convert_mqtt_args_to_dbus(args)

        assert len(result) == 1
        assert isinstance(result[0], list)
        assert len(result[0]) == 1

        # The dict in the list should be wrapped
        dict_item = result[0][0]
        assert isinstance(dict_item, dict)

        # Verify the nested structure is preserved
        level1_value = dict_item["level1"].value
        assert isinstance(level1_value, list)
        assert len(level1_value) == 1


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_conversion_with_circular_reference(self):
        """Test handling of circular references in data structures"""
        circular_dict: dict[str, object] = {"key": "value"}
        circular_dict["self"] = circular_dict

        # This should either handle gracefully or raise an exception
        # The exact behavior depends on implementation
        with pytest.raises((RecursionError, ValueError)):
            convert_mqtt_args_to_dbus([circular_dict])
