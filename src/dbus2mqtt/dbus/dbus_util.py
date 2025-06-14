import base64
import re

import dbus_fast.signature as dbus_signature


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
