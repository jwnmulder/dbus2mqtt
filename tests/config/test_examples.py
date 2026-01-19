import json

from pathlib import Path

import dotenv
import jsonschema

from jsonargparse.typing import SecretStr

from dbus2mqtt.config import Config
from dbus2mqtt.config.jsonarparse import filtered_ns, new_argument_parser, ns_to_cls

FILE_DIR = Path(__file__).resolve().parent
CONFIG_JSON_SCHEMA = {}


def setup_module(module):
    global CONFIG_JSON_SCHEMA
    schema_file = FILE_DIR.parent.parent / "schemas" / "config.schema.json"
    CONFIG_JSON_SCHEMA = json.loads(schema_file.read_text(encoding="utf-8"))


def _replace_secretstr(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = _replace_secretstr(v)
        return obj
    if isinstance(obj, list):
        return [_replace_secretstr(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_replace_secretstr(v) for v in obj)
    if isinstance(obj, SecretStr):
        return obj.get_secret_value()
    return obj


def _parse_and_validate_config(file: str) -> Config:

    dotenv.load_dotenv(".env.example")

    parser = new_argument_parser()
    parser.add_class_arguments(Config)

    cfg = parser.parse_path(file)

    # Validate with json schema
    config_dict = filtered_ns(Config, cfg.as_dict())
    config_dict = _replace_secretstr(config_dict)
    jsonschema.validate(config_dict, CONFIG_JSON_SCHEMA)

    # Validate by instantiating Config object
    cfg = parser.instantiate_classes(cfg)
    config = ns_to_cls(Config, cfg)

    return config


def test_home_assistant_media_player_example():
    config = _parse_and_validate_config(
        f"{FILE_DIR}/../../docs/examples/home_assistant_media_player.yaml"
    )
    assert config is not None


def test_linux_desktop_example():
    config = _parse_and_validate_config(f"{FILE_DIR}/../../docs/examples/linux_desktop.yaml")
    assert config is not None


def test_bluez_example():
    config = _parse_and_validate_config(f"{FILE_DIR}/../../docs/examples/bluez.yaml")
    assert config is not None


def test_connman_example():
    config = _parse_and_validate_config(f"{FILE_DIR}/../../docs/examples/connman-config.yaml")
    assert config is not None
