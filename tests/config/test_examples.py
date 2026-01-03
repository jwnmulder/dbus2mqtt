import os

import dotenv

from dbus2mqtt.config import Config
from dbus2mqtt.config.jsonarparse import new_argument_parser

FILE_DIR = os.path.dirname(__file__)


def test_home_assistant_media_player_example():

    dotenv.load_dotenv(".env.example")

    parser = new_argument_parser()
    parser.add_class_arguments(Config)

    cfg = parser.parse_path(f"{FILE_DIR}/../../docs/examples/home_assistant_media_player.yaml")
    config = parser.instantiate_classes(cfg)

    assert config is not None


def test_linux_desktop_example():
    dotenv.load_dotenv(".env.example")

    parser = new_argument_parser()
    parser.add_class_arguments(Config)

    cfg = parser.parse_path(f"{FILE_DIR}/../../docs/examples/linux_desktop.yaml")
    config = parser.instantiate_classes(cfg)

    assert config is not None


def test_bluez_example():
    dotenv.load_dotenv(".env.example")

    parser = new_argument_parser()
    parser.add_class_arguments(Config)

    cfg = parser.parse_path(f"{FILE_DIR}/../../docs/examples/bluez.yaml")
    config = parser.instantiate_classes(cfg)

    assert config is not None


def test_connman_example():
    dotenv.load_dotenv(".env.example")

    parser = new_argument_parser()
    parser.add_class_arguments(Config)

    cfg = parser.parse_path(f"{FILE_DIR}/../../docs/examples/connman-config.yaml")
    config = parser.instantiate_classes(cfg)

    assert config is not None
