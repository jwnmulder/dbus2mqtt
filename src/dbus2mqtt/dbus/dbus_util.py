import json
import re

import dbus_next.signature as dbus_signature


def _variant_serializer(obj):
    if isinstance(obj, dbus_signature.Variant):
        return obj.value
    return obj

def unwrap_dbus_object(o):
    # an easy way to get rid of dbus_next.signature.Variant types
    res = json.dumps(o, default=_variant_serializer)
    json_obj = json.loads(res)
    return json_obj

def unwrap_dbus_objects(args):
    res = [unwrap_dbus_object(o) for o in args]
    return res

def camel_to_snake(name):
    return re.sub(r'([a-z])([A-Z])', r'\1_\2', name).lower()
