import json

from dbus2mqtt.config import Config
from dbus2mqtt.config.jsonargparse import new_argument_parser

if __name__ == "__main__":
    parser = new_argument_parser()
    parser.add_class_arguments(Config)

    schema_str = parser.get_completion_script("jsonschema")
    schema = json.loads(schema_str)

    # patch the generated schema
    # some properties are also set via environment variables and not in yaml
    required_properties: list[str] = schema["required"]
    required_properties.remove("mqtt")

    mqtt_required_properties: list[str] = schema["properties"]["mqtt"]["required"]
    mqtt_required_properties.remove("host")
    mqtt_required_properties.remove("username")
    mqtt_required_properties.remove("password")

    print(json.dumps(schema, indent=2))
