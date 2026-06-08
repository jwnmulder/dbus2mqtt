from dataclasses import fields
from typing import Any

import jsonargparse

from docstring_parser import DocstringStyle
from jsonargparse import Namespace, set_parsing_settings
from yaml import YAMLError

default_yaml_loader = jsonargparse.get_loader("yaml")


def _custom_yaml_load(stream: str) -> Any:

    v = stream.strip()

    # jsonargparse tries to parse yaml 1.1 boolean like values
    # Without this, str:"{'PlaybackStatus': 'Off'}" would become dict:{'PlaybackStatus': False}
    if v in ["on", "On", "off", "Off", "TRUE", "FALSE", "True", "False"]:
        return stream

    # Delegate to default yaml loader from jsonargparse
    return default_yaml_loader(stream)


def new_argument_parser() -> jsonargparse.ArgumentParser:

    set_parsing_settings(
        docstring_parse_style=DocstringStyle.GOOGLE,
    )

    # register out custom yaml loader for jsonargparse
    jsonargparse.set_loader(
        mode="yaml_custom", loader_fn=_custom_yaml_load, exceptions=(YAMLError,), json_superset=True
    )

    # unless specified otherwise, load config from config.yaml
    parser = jsonargparse.ArgumentParser(
        default_config_files=["config.yaml"],
        default_env=True,
        env_prefix=False,
        parser_mode="yaml_custom",
    )

    return parser


def filtered_ns(cls, ns_dict: dict[str, Any]) -> dict[str, Any]:
    allowed_keys = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in ns_dict.items() if k in allowed_keys}
    return filtered


def ns_to_cls(cls, ns: Namespace):
    filtered = filtered_ns(cls, ns.as_dict())
    return cls(**filtered)
