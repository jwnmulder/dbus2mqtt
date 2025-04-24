from abc import ABC, abstractmethod
from typing import Any


class FlowExecutionContext:

    def __init__(self, name: str | None, global_context: dict[str, Any], dbus_object_context: dict[str, Any] | None):
        self.name = name

        self.global_context = global_context
        """
        Updatable global context which is shared across all flows.
        """

        self.dbus_object_context = dbus_object_context
        """
        Updatable context bound to the lifecycle of the bus_name / dbus_object.
        """

        self.context: dict[str, Any] = {}
        """
        Updatable per flow execution context.
        """

    def get_aggregated_context(self) -> dict[str, Any]:
        """
        Get the aggregated context for the flow execution.
        Merges global flows context, flow context, and local context
        """

        aggregated_context = {}
        if self.global_context:
            aggregated_context.update(self.global_context)
        if self.dbus_object_context:
            aggregated_context.update(self.dbus_object_context)
        if self.context:
            aggregated_context.update(self.context)
        return aggregated_context

class FlowAction(ABC):

    @abstractmethod
    async def execute(self, context: FlowExecutionContext):
        """Execute the action with the given flow execution context."""
        pass
