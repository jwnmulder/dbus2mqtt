import base64
import logging
import re

from typing import Any

import dbus_fast.signature as dbus_signature

from dbus_fast import Variant

logger = logging.getLogger(__name__)

def unwrap_dbus_object(obj):
    if isinstance(obj, dict):
        return {k: unwrap_dbus_object(v) for k, v in obj.items()}
    elif isinstance(obj, list | tuple | set):
        return type(obj)(unwrap_dbus_object(i) for i in obj)
    elif isinstance(obj, dbus_signature.Variant):
        return unwrap_dbus_object(obj.value)
    elif isinstance(obj, bytes):
        return base64.b64encode(obj).decode('utf-8')
    else:
        return obj

def unwrap_dbus_objects(args):
    res = [unwrap_dbus_object(o) for o in args]
    return res

def camel_to_snake(name):
    return re.sub(r'([a-z])([A-Z])', r'\1_\2', name).lower()

def _convert_value_to_dbus(value: Any) -> Any:
    """
    Recursively convert a single value to D-Bus compatible type.

    Args:
        value: The value to convert (can be dict, list, primitive, etc.)

    Returns:
        D-Bus compatible value
    """
    if value is None:
        return value

    elif isinstance(value, dict):
        # Convert dict to D-Bus dictionary (a{sv} - dictionary of string to variant)
        dbus_dict = {}
        for k, v in value.items():
            # Keys are typically strings in D-Bus dictionaries
            key = str(k)
            # Recursively convert the value first, then wrap in Variant
            converted_value = _convert_value_to_dbus(v)
            # Determine the appropriate D-Bus signature for the converted value
            signature = _get_dbus_signature(converted_value)
            dbus_dict[key] = Variant(signature, converted_value)
        return dbus_dict

    elif isinstance(value, list):
        # Convert list to D-Bus array
        converted_list = []
        for item in value:
            converted_list.append(_convert_value_to_dbus(item))
        return converted_list

    elif isinstance(value, bool):
        # Boolean values are fine as-is for D-Bus
        return value

    elif isinstance(value, int):
        # Integer values are fine as-is for D-Bus
        return value

    elif isinstance(value, float):
        # Float values are fine as-is for D-Bus
        return value

    elif isinstance(value, str):
        # String values are fine as-is for D-Bus
        return value

    else:
        # For any other type, try to convert to string as fallback
        logger.warning(f"Unknown type {type(value)} for D-Bus conversion, converting to string: {value}")
        return str(value)

def _get_dbus_signature(value: Any) -> str:
    """
    Get the appropriate D-Bus signature for a value.

    Args:
        value: The value to get signature for

    Returns:
        D-Bus type signature string
    """
    if isinstance(value, bool):
        return 'b'  # boolean
    elif isinstance(value, int):
        uint16_min = 0
        uint16_max = 0xFFFF
        int16_min = -0x7FFF - 1
        int16_max = 0x7FFF
        uint32_min = 0
        uint32_max = 0xFFFFFFFF
        int32_min = -0x7FFFFFFF - 1
        int32_max = 0x7FFFFFFF
        uint64_min = 0
        uint64_max = 18446744073709551615

        if uint16_min <= value <= uint16_max:
            return 'q'  # 16-bit unsigned int
        elif int16_min <= value <= int16_max:
            return 'n'  # 16-bit signed int
        elif uint32_min <= value <= uint32_max:
            return 'u'  # 32-bit unsigned int
        elif int32_min <= value <= int32_max:
            return 'i'  # 32-bit signed integer
        elif uint64_min <= value <= uint64_max:
            return 't'  # 64-bit unsigned integer
        else:
            return 'x'  # 64-bit signed integer
    elif isinstance(value, float):
        return 'd'  # double
    elif isinstance(value, str):
        return 's'  # string
    elif isinstance(value, list):
        if not value:
            return 'as'  # assume array of strings for empty arrays
        # Get signature of first element and assume homogeneous array
        element_sig = _get_dbus_signature(value[0])
        return f'a{element_sig}'  # array of elements
    elif isinstance(value, dict):
        return 'a{sv}'  # dictionary of string to variant
    else:
        return 's'  # fallback to string

# Wraps all complex types in VariantList
def convert_mqtt_args_to_dbus(args: list[Any]) -> list[Any]:
    """
    Convert MQTT/JSON arguments to D-Bus with explicit Variant wrapping for all complex types.

    Args:
        args: List of arguments from MQTT

    Returns:
        List of D-Bus compatible arguments with explicit Variants
    """
    converted_args = []

    for arg in args:
        converted_arg = _convert_and_wrap_in_variant(arg)
        converted_args.append(converted_arg)

    return converted_args

def _convert_and_wrap_in_variant(value: Any) -> Any:
    """
    Convert a value and wrap complex types in Variants.
    """
    if value is None:
        return value
    elif isinstance(value, bool | int | float | str):
        # Primitive types can be used as-is or wrapped in Variant if needed
        return value
    elif isinstance(value, dict):
        # Convert dict and wrap in Variant
        converted_dict = {}
        for k, v in value.items():
            key = str(k)
            converted_value = _convert_value_to_dbus(v)
            signature = _get_dbus_signature(converted_value)
            converted_dict[key] = Variant(signature, converted_value)
        return converted_dict
    elif isinstance(value, list):
        # Convert list and potentially wrap in Variant
        converted_list = []
        for item in value:
            converted_list.append(_convert_and_wrap_in_variant(item))
        return converted_list
    else:
        # Fallback
        return value
