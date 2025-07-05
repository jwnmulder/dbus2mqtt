
import os

from typing import cast

import dotenv

from dbus2mqtt.config import Config
from dbus2mqtt.config.jsonarparse import new_argument_parser

FILE_DIR = os.path.dirname(__file__)

def test_off_string_value():

    dotenv.load_dotenv(".env.example")

    parser = new_argument_parser()
    parser.add_class_arguments(Config)

    cfg = parser.parse_path(f"{FILE_DIR}/fixtures/payload_template_off.yaml")
    config: Config = cast(Config, parser.instantiate_classes(cfg))

    assert config is not None

    action = config.flows[0].actions[0]
    assert action.type == "mqtt_publish"
    assert action.payload_template == {
        'PlaybackStatus': 'Off',  # This is the real test, it was False before the 'yaml_custom' loader
        'TestFalseString': False  # This is one that should also be fixed. For now it's what it is
    }

def test_cron_trigger_string_value():
    """Test that the cron trigger is parsed correctly from a string value
    More specifically, the value '*/5' will fail jsonargparse for some weird reason
    """
    dotenv.load_dotenv(".env.example")

    parser = new_argument_parser()
    parser.add_class_arguments(Config)

    cfg = parser.parse_path(f"{FILE_DIR}/fixtures/schedule_cron_trigger.yaml")
    config: Config = cast(Config, parser.instantiate_classes(cfg))

    assert config is not None

    trigger = config.flows[0].triggers[0]
    assert trigger.type == "schedule"
    assert trigger.cron == {"minute": "*/5"}

def test_jsonargparse_jinja_expressions():
    """values starting with {{ are not parsed correctly
    """
    dotenv.load_dotenv(".env.example")

    parser = new_argument_parser()
    parser.add_class_arguments(Config)

    cfg = parser.parse_path(f"{FILE_DIR}/fixtures/payload_template_jinja_expressions.yaml")
    config: Config = cast(Config, parser.instantiate_classes(cfg))

    assert config is not None

    # double left curly brace
    action = config.flows[0].actions[0]
    assert action.type == "mqtt_publish"
    assert action.payload_template == """{{ "testvalue" }}"""

    action = config.flows[1].actions[0]
    assert action.type == "mqtt_publish"
    assert action.payload_template == """{% set val = "testvalue" %}"""
