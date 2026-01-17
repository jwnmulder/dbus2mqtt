import logging

from copy import deepcopy

from dbus_fast.introspection import Interface, Node

from dbus2mqtt.dbus.introspection.patches.mpris_playerctl import mpris_introspection_playerctl

logger = logging.getLogger(__name__)


class IntrospectPatcher:
    def patch_if_needed(self, bus_name: str, path: str, introspection: Node) -> Node:

        if path == "/org/mpris/MediaPlayer2" and bus_name.startswith("org.mpris.MediaPlayer2.vlc"):
            # vlc 3.x branch contains an incomplete and wrong dbus introspection
            # https://github.com/videolan/vlc/commit/48e593f164d2bf09b0ca096d88c86d78ec1a2ca0
            # Until vlc 4.x is out we use the official specification instead
            return mpris_introspection_playerctl

        reference = None
        if path == "/org/mpris/MediaPlayer2" and bus_name.startswith("org.mpris.MediaPlayer2."):
            # MPRIS: If no introspection data is available, load a default
            if len(introspection.interfaces) == 0:
                return mpris_introspection_playerctl

            # Not all players provide argument names in their introspection data.
            # Load well known mpris introspection data to enrich the original
            reference = mpris_introspection_playerctl

        if reference:
            introspection = deepcopy(introspection)
            self._enrich(introspection, reference)

        return introspection

    def _enrich(self, introspection: Node, reference: Node):
        """Enrich target introspection using reference metadata."""
        ref_interfaces = {i.name: i for i in reference.interfaces}

        for interface in introspection.interfaces:
            ref_iface = ref_interfaces.get(interface.name)
            if not ref_iface:
                continue

            self._enrich_signals(interface, ref_iface)
            self._enrich_methods(interface, ref_iface)

    def _enrich_signals(self, interface: Interface, reference: Interface):
        ref_signals = {s.name: s for s in reference.signals}

        for signal in interface.signals:
            ref_signal = ref_signals.get(signal.name)
            if not ref_signal:
                continue

            for idx, arg in enumerate(signal.args):
                if arg.name:
                    continue

                if idx < len(ref_signal.args):
                    arg.name = ref_signal.args[idx].name

    def _enrich_methods(self, interface: Interface, reference: Interface):
        ref_methods = {m.name: m for m in reference.methods}

        for method in interface.methods:
            ref_method = ref_methods.get(method.name)
            if not ref_method:
                continue

            for idx, arg in enumerate(method.in_args):
                if arg.name:
                    continue

                if idx < len(ref_method.in_args):
                    arg.name = ref_method.in_args[idx].name
