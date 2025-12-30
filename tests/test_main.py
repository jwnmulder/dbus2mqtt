import sys

from unittest.mock import AsyncMock

import pytest

from dbus2mqtt.__main__ import main as main
from dbus2mqtt.config import Config


def test_main_help_shows_help_and_exits(capsys, monkeypatch):

    # Arrange: simulate CLI call with --help
    monkeypatch.setattr(sys, "argv", ["dbus2mqtt", "--help"])

    # Act & Assert: argparse exits with SystemExit(0)
    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 0

    # Capture output
    captured = capsys.readouterr()

    # Help text usually goes to stdout, but argparse may use stderr
    output = captured.out

    print(output)

    assert "usage:" in output.lower()
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
