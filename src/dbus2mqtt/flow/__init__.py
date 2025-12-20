from abc import ABC, abstractmethod
from typing import Any


class FlowExecutionContext:

    def __init__(self, name: str | None, global_flows_context: dict[str, Any], flow_context: dict[str, Any]):
        self.name = name

        self._global_context = global_flows_context
        """
        Global flows context which is shared across all flows.
        Modifiable by user.
        **Not** cleaned up after flow execution.
        """

        self._flow_context = flow_context
        """
        Flow context which contains flow specific context like 'subscription_bus_name'.
        **Not** modifiable by user.
        **Not** cleaned up after flow execution.
        """

        self._context: dict[str, Any] = {}
        """
        Per flow execution context.
        Modifiable by user.
        Cleaned up after each flow execution
        """

        self.global_context_updated = False

    def update_global_context(self, context: dict[str, Any]):
        """Update the global context with the given context update."""
        self._global_context.update(context)
        self.global_context_updated = True

    def update_context(self, context: dict[str, Any]):
        """Update the flow execution context with the given context update."""
        self._context.update(context)

    def get_aggregated_context(self) -> dict[str, Any]:
        """Get the aggregated context for the flow execution.

        This includes global flows context, flow context, and local context.
        """
        context = {}
        if self._global_context:
            context.update(self._global_context)
        if self._flow_context:
            context.update(self._flow_context)
        if self._context:
            context.update(self._context)
        return context

class FlowAction(ABC):

    @abstractmethod
    async def execute(self, context: FlowExecutionContext):
        """Execute the action with the given flow execution context."""
        pass
