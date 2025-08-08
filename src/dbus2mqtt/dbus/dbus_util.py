import base64
import re
import logging

from typing import Any, Dict, List, Union

from dbus_fast import Variant
import dbus_fast.signature as dbus_signature

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

def convert_mqtt_args_to_dbus(args: List[Any]) -> List[Any]:
    """
    Convert MQTT/JSON arguments to D-Bus compatible arguments.
    
    Args:
        args: List of arguments from MQTT (typically JSON deserialized objects)
        
    Returns:
        List of D-Bus compatible arguments
        
    Example:
        # For ConnMan SetProperty with nested dict:
        mqtt_args = [{"Ethernet": {"Method": "auto", "Interface": "end1", "Address": "3E:67:8C:CE:CF:86", "MTU": 2000}}]
        dbus_args = convert_mqtt_args_to_dbus(mqtt_args)
    """
    converted_args = []
    
    for arg in args:
        converted_arg = _convert_value_to_dbus(arg)
        # If the converted argument is a dict, it needs to be wrapped in a Variant for D-Bus
        if isinstance(converted_arg, dict):
            signature = _get_dbus_signature(converted_arg)
            converted_arg = Variant(signature, converted_arg)
        converted_args.append(converted_arg)
    
    return converted_args

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
        UINT16_MIN = 0
        UINT16_MAX = 0xFFFF
        INT16_MIN = -0x7FFF - 1
        INT16_MAX = 0x7FFF
        UINT32_MIN = 0
        UINT32_MAX = 0xFFFFFFFF
        INT32_MIN = -0x7FFFFFFF - 1
        INT32_MAX = 0x7FFFFFFF
        UINT64_MIN = 0
        UINT64_MAX = 18446744073709551615

        if UINT16_MIN <= value <= UINT16_MAX:
            return 'q'  # 16-bit unsigned int
        elif INT16_MIN <= value <= INT16_MAX:
            return 'n'  # 16-bit signed int
        elif UINT32_MIN <= value <= UINT32_MAX:
            return 'u'  # 32-bit unsigned int
        elif INT32_MIN <= value <= INT32_MAX:
            return 'i'  # 32-bit signed integer
        elif UINT64_MIN <= value <= UINT64_MAX:
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

# Helper function specifically for ConnMan-style property setting
def convert_connman_property_args(property_value: Any) -> Any:
    """
    Helper function specifically for ConnMan SetProperty calls.
    
    ConnMan SetProperty expects: SetProperty(variant property_value)
    
    Args:
        property_value: Value to set (will be converted and wrapped in Variant)
        
    Returns:
        List with Variant(converted_value)
    """
    converted_value = _convert_value_to_dbus(property_value)
    signature = _get_dbus_signature(converted_value)
    return Variant(signature, converted_value)

# Alternative conversion that wraps all complex types in Variants
def convert_mqtt_args_to_dbus_explicit_variants(args: List[Any]) -> List[Any]:
    """
    Convert MQTT/JSON arguments to D-Bus with explicit Variant wrapping for all complex types.
    This version is more aggressive about wrapping things in Variants.
    
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
    elif isinstance(value, (bool, int, float, str)):
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
        return Variant('a{sv}', converted_dict)
    elif isinstance(value, list):
        # Convert list and potentially wrap in Variant
        converted_list = []
        for item in value:
            converted_list.append(_convert_and_wrap_in_variant(item))
        return converted_list
    else:
        # Fallback
        return str(value)
