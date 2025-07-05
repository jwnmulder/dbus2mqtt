import jsonargparse


def _custom_yaml_load(stream):
    if isinstance(stream, str):
        v = stream.strip()

        # jsonargparse tries to parse yaml 1.1 boolean like values
        # Without this, str:"{'PlaybackStatus': 'Off'}" would become dict:{'PlaybackStatus': False}
        if v in ['on', 'On', 'off', 'Off', 'TRUE', 'FALSE', 'True', 'False']:
            return stream

        # Anoyingly, values starting with {{ and ending with }} are working with the default yaml_loader
        # from jsonargparse. Somehow its not when we use the custom yaml loader.
        # This fixes it
        if v.startswith("{{") or v.startswith("{%"):
            return stream

    # Delegate to default yaml loader from jsonargparse
    yaml_loader = jsonargparse.get_loader("yaml")
    return yaml_loader(stream)

def new_argument_parser() -> jsonargparse.ArgumentParser:

    # register out custom yaml loader for jsonargparse
    jsonargparse.set_loader("yaml_custom", _custom_yaml_load)

    # unless specified otherwise, load config from config.yaml
    parser = jsonargparse.ArgumentParser(default_config_files=["config.yaml"], default_env=True, env_prefix=False, parser_mode="yaml_custom")

    return parser
