"""Natural progress-update guard for long BrandMind action chains."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelCallResult,
    ModelRequest,
    ModelResponse,
)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from core.brand_strategy.session import get_active_session


class NaturalProgressUpdateMiddleware(AgentMiddleware):
    """Nudge the main agent to author a progress note before expensive work.

    The Web UI no longer fabricates status text from tool names. This guard
    stays deliberately selective: it only re-prompts when the first model call
    of a user turn jumps straight into work that is likely to leave the user
    waiting, such as specialist delegation or artifact generation.
    """

    _PROGRESS_REMINDER = (
        "You are about to start work that may leave the user waiting. Call "
        "`share_progress_update(message=...)` once only if a short human note "
        "would feel natural here. Do not greet, repeat the user's request, or "
        "preview the final answer. Write one brief sentence in the user's "
        "language and relationship tone that names the useful outcome you are "
        "working toward. Do not mention internal tools, agents, or step names. "
        "For this retry, call only `share_progress_update`; after it returns, "
        "continue the work normally."
    )
    _VISIBLE_WAIT_TOOL_NAMES = frozenset(
        {
            "task",
            "generate_artifact",
            "generate_document",
            "generate_image",
            "generate_presentation",
            "generate_spreadsheet",
        }
    )

    def __init__(self, *, tool_name: str = "share_progress_update") -> None:
        """Create the progress-update guard.

        Args:
            tool_name: Name of the model-authored progress-note tool.
        """
        super().__init__()
        self.tool_name = tool_name

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        """Retry once with a progress reminder when the first tool chain is silent."""
        response = handler(request)
        if not self._needs_progress_retry(request, response):
            return response
        return handler(self._with_progress_reminder(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        """Async counterpart to :meth:`wrap_model_call`."""
        response = await handler(request)
        if not self._needs_progress_retry(request, response):
            return response
        return await handler(self._with_progress_reminder(request))

    def _needs_progress_retry(
        self,
        request: ModelRequest,
        response: ModelResponse,
    ) -> bool:
        """Return whether this first-turn action chain needs a progress note."""
        if not self._is_first_model_call_of_user_turn(request):
            return False

        tool_names = self._tool_names(response)
        if not tool_names or self.tool_name in tool_names:
            return False

        return any(name in self._VISIBLE_WAIT_TOOL_NAMES for name in tool_names)

    @staticmethod
    def _is_first_model_call_of_user_turn(request: ModelRequest) -> bool:
        """Detect the opening model call before any tool results are present."""
        if not request.messages:
            return False
        if not isinstance(request.messages[-1], HumanMessage):
            return False

        active_session = get_active_session()
        if active_session is None:
            return True

        marker = f"_natural_progress_retry_turn_{active_session.turn_index}"
        if request.state is None:
            return True
        if request.state.get(marker):
            return False
        request.state[marker] = True
        return True

    @staticmethod
    def _tool_names(response: ModelResponse) -> list[str]:
        """Extract tool names from the terminal model message."""
        message = NaturalProgressUpdateMiddleware._last_ai_message(response)
        if message is None:
            return []

        names: list[str] = []
        for call in getattr(message, "tool_calls", []) or []:
            if isinstance(call, dict):
                name = call.get("name")
                if isinstance(name, str) and name:
                    names.append(name)

        function_call = getattr(message, "additional_kwargs", {}).get("function_call")
        if isinstance(function_call, dict):
            name = function_call.get("name")
            if isinstance(name, str) and name:
                names.append(name)

        return names

    @staticmethod
    def _last_ai_message(response: ModelResponse) -> AIMessage | None:
        """Return the last AI message from a model response."""
        result = getattr(response, "result", None)
        if not isinstance(result, list) or not result:
            return None

        message = result[-1]
        return message if isinstance(message, AIMessage) else None

    def _with_progress_reminder(self, request: ModelRequest) -> ModelRequest:
        """Append a narrowly scoped retry reminder to the model request."""
        messages = [
            *request.messages,
            SystemMessage(content=self._PROGRESS_REMINDER),
        ]
        return request.override(messages=messages)
