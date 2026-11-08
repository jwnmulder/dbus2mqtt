from unittest.mock import MagicMock, patch

from dbus2mqtt.mqtt.mqtt_client import MqttClient
from tests import mocked_app_context


def test_tls_enabled_calls_tls_set():
    app_context = mocked_app_context()
    app_context.config.mqtt.tls_enabled = True
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
    app_context = mocked_app_context()
    app_context.config.mqtt.tls_enabled = True
    app_context.config.mqtt.tls_insecure = True
    with patch("dbus2mqtt.mqtt.mqtt_client.mqtt.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        MqttClient(app_context, None)
        mock_client.tls_insecure_set.assert_called_once_with(True)


def test_tls_with_certs():
    app_context = mocked_app_context()
    app_context.config.mqtt.tls_enabled = True
    app_context.config.mqtt.tls_ca_file = "/path/to/ca.crt"
    app_context.config.mqtt.tls_cert_file = "/path/to/client.crt"
    app_context.config.mqtt.tls_key_file = "/path/to/client.key"
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
    app_context = mocked_app_context()
    app_context.config.mqtt.tls_enabled = False
    with patch("dbus2mqtt.mqtt.mqtt_client.mqtt.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        MqttClient(app_context, None)
        mock_client.tls_set.assert_not_called()


def test_tls_auto_enabled_when_port_8883():
    """Test that TLS is auto-enabled when tls_enabled is None and port is 8883."""
    # Create config with tls_enabled=None (simulating YAML null) and port=8883
    app_context = mocked_app_context()
    app_context.config.mqtt.tls_enabled = None
    app_context.config.mqtt.port = 8883
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


def test_tls_not_auto_enabled_when_port_not_8883():
    """Test that TLS is NOT auto-enabled when tls_enabled is None and port is not 8883."""
    app_context = mocked_app_context()
    app_context.config.mqtt.tls_enabled = None
    app_context.config.mqtt.port = 1883
    with patch("dbus2mqtt.mqtt.mqtt_client.mqtt.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        MqttClient(app_context, None)
        mock_client.tls_set.assert_not_called()
