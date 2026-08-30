from unittest.mock import MagicMock, patch

from jsonargparse.typing import SecretStr

from dbus2mqtt import AppContext, config
from dbus2mqtt.event_broker import EventBroker
from dbus2mqtt.mqtt.mqtt_client import MqttClient
from dbus2mqtt.template.templating import TemplateEngine


def _make_app_context(mqtt_config: config.MqttConfig) -> AppContext:
    cfg = config.Config(
        dbus=config.DbusConfig(subscriptions=[]),
        mqtt=mqtt_config,
        flows=[],
    )
    return AppContext(cfg, EventBroker(), TemplateEngine())


def _base_mqtt_config(**kwargs) -> config.MqttConfig:
    return config.MqttConfig(
        host="localhost", username="test", password=SecretStr("test"), **kwargs
    )


def test_tls_enabled_calls_tls_set():
    app_context = _make_app_context(_base_mqtt_config(tls_enabled=True))
    with patch("dbus2mqtt.mqtt.mqtt_client.mqtt.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        MqttClient(app_context, None)
        mock_client.tls_set.assert_called_once_with(
            ca_certs=None,
            certfile=None,
            keyfile=None,
        )
        mock_client.tls_insecure_set.assert_not_called()


def test_tls_insecure_calls_tls_insecure_set():
    app_context = _make_app_context(_base_mqtt_config(tls_enabled=True, tls_insecure=True))
    with patch("dbus2mqtt.mqtt.mqtt_client.mqtt.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        MqttClient(app_context, None)
        mock_client.tls_insecure_set.assert_called_once_with(True)


def test_tls_with_certs():
    app_context = _make_app_context(
        _base_mqtt_config(
            tls_enabled=True,
            tls_ca_certs="/path/to/ca.crt",
            tls_certfile="/path/to/client.crt",
            tls_keyfile="/path/to/client.key",
        )
    )
    with patch("dbus2mqtt.mqtt.mqtt_client.mqtt.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        MqttClient(app_context, None)
        mock_client.tls_set.assert_called_once_with(
            ca_certs="/path/to/ca.crt",
            certfile="/path/to/client.crt",
            keyfile="/path/to/client.key",
        )


def test_tls_disabled_does_not_call_tls_set():
    app_context = _make_app_context(_base_mqtt_config(tls_enabled=False))
    with patch("dbus2mqtt.mqtt.mqtt_client.mqtt.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        MqttClient(app_context, None)
        mock_client.tls_set.assert_not_called()
