from pathlib import Path

from dbus_fast import introspection as intr

from dbus2mqtt.dbus.introspection.patcher import IntrospectPatcher
from dbus2mqtt.dbus.introspection.patches.mpris_playerctl import mpris_introspection_playerctl
from tests.dbus.introspection import TestNode


def _introspection_from_xml(filename: str) -> TestNode:
    fixtures_dir = Path(__file__).parent / ".." / "fixtures"
    xml_path = fixtures_dir / filename

    data = xml_path.read_text(encoding="utf-8")

    return TestNode(intr.Node.parse(data))


def test_enrich_names():

    introspection = _introspection_from_xml("introspection_data_vlc_3.xml")

    patcher = IntrospectPatcher()
    patcher._enrich(introspection, reference=mpris_introspection_playerctl)

    # method arguments should have been enriched with valid names
    method = introspection.interface("org.freedesktop.DBus.Properties").method("Get")
    assert method.in_args[0].name

    # signal arguments should have been enriched with valid names
    signal = introspection.interface("org.freedesktop.DBus.Properties").signal("PropertiesChanged")
    assert signal.args[0].name
