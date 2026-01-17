from dbus_fast import introspection as intr


class TestInterface(intr.Interface):
    def __init__(self, interface: intr.Interface):
        super().__init__(
            name=interface.name,
            methods=interface.methods,
            signals=interface.signals,
            properties=interface.properties,
            annotations=interface.annotations,
        )

    def method(self, name: str) -> intr.Method:
        try:
            return next(m for m in self.methods if m.name == name)
        except StopIteration:
            raise AssertionError(
                f"Method '{name}' not found on interface '{self.name}'. "
                f"Available methods: {[m.name for m in self.methods]}"
            )

    def signal(self, name: str) -> intr.Signal:
        try:
            return next(s for s in self.signals if s.name == name)
        except StopIteration:
            raise AssertionError(
                f"Signal '{name}' not found on interface '{self.name}'. "
                f"Available signals: {[s.name for s in self.signals]}"
            )

    def property(self, name: str) -> intr.Property:
        try:
            return next(p for p in self.properties if p.name == name)
        except StopIteration:
            raise AssertionError(
                f"Property '{name}' not found on interface '{self.name}'. "
                f"Available properties: {[p.name for p in self.properties]}"
            )


class TestNode(intr.Node):
    def __init__(self, node: intr.Node):
        super().__init__(node.name, node.interfaces, node.is_root)

    def interface(self, name: str) -> TestInterface:
        try:
            return next(TestInterface(i) for i in self.interfaces if i.name == name)
        except StopIteration:
            raise AssertionError(
                f"Interface '{name}' not found. "
                f"Available interfaces: {[i.name for i in self.interfaces]}"
            )
