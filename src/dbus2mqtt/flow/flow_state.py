from typing import Any


class FlowState:
    def __init__(self):
        self.global_context: dict[str, Any] = {}
        self.object_contexts: dict[str, dict[str, Any]] = {}


def to_object_context_ref(namespace: str, *args) -> str:
    return f"{namespace}:{':'.join(args)}"
