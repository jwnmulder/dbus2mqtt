import sys

from unittest.mock import AsyncMock

import pytest

from dbus2mqtt.__main__ import main as main
from dbus2mqtt.config import Config


def test_main_help_shows_help_and_exits(capsys, monkeypatch):

    monkeypatch.setattr(sys, "argv", ["dbus2mqtt", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 0

    output = capsys.readouterr().out

    assert "usage:" in output
    assert "--help" in output
    assert "--config" in output
    assert "--verbose" in output


def test_main_invokes_run_with_config(monkeypatch):

    mock_run = AsyncMock()
    monkeypatch.setattr("dbus2mqtt.main.run", mock_run)
    monkeypatch.setattr(sys, "argv", ["dbus2mqtt", "--config", "docs/examples/linux_desktop.yaml"])

    main()

    mock_run.assert_awaited_once()
    config = mock_run.call_args.args[0]

    assert isinstance(config, Config)
    assert len(config.dbus.subscriptions) > 0


def test_main_print_config_with_comments(capsys, monkeypatch):

    monkeypatch.setattr(
        sys,
        "argv",
        ["dbus2mqtt", "--config", "docs/examples/linux_desktop.yaml", "--print_config=comments"],
    )
    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 0

    output = capsys.readouterr().out

    assert "# MQTT broker hostname or IP address" in output
