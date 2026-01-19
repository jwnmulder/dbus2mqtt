from dbus2mqtt import config
from dbus2mqtt.generate_schema import SchemaGenerator


def test_schema_generator():
    generator = SchemaGenerator(config)
    schema = generator.build(config.Config)

    assert schema
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
