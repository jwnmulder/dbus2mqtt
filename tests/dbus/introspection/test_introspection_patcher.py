from pathlib import Path

from dbus_fast import introspection as intr

from dbus2mqtt.dbus.introspection.patcher import IntrospectPatcher
from dbus2mqtt.dbus.introspection.patches.mpris_playerctl import mpris_introspection_playerctl
from tests.dbus.introspection import TestNode

# Seeked is not defined in introspection data vlc
# property and signame arguments names are empty for vlc


def get_interface(node: intr.Node, name: str) -> intr.Interface:
    return next(i for i in node.interfaces if i.name == name)


def get_method(interface: intr.Interface, name: str) -> intr.Method:
    return next(i for i in interface.methods if i.name == name)


def _introspection_from_xml(filename: str) -> TestNode:
    fixtures_dir = Path(__file__).parent / ".." / "fixtures"
    xml_path = fixtures_dir / filename

    data = xml_path.read_text(encoding="utf-8")

    return TestNode(intr.Node.parse(data))


def test_enrich_signal_arg_names():

    introspection = _introspection_from_xml("introspection_data_vlc_3.xml")

    patcher = IntrospectPatcher()
    patcher._enrich(introspection, reference=mpris_introspection_playerctl)

    # method arguments should have names
    method = introspection.interface("org.freedesktop.DBus.Properties").method("Get")
    assert method.in_args[0].name

    # signal arguments should have names
    signal = introspection.interface("org.freedesktop.DBus.Properties").signal("PropertiesChanged")
    assert signal.args[0].name
