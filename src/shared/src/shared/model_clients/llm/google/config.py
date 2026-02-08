from typing import Any, Callable, Dict, Optional, Type, Union

from pydantic import BaseModel

from shared.model_clients.llm.base_class import LLMBackend, LLMConfig

JSONSchema = Dict[str, Any]
SchemaLike = Union[Type[BaseModel], JSONSchema, type, list, Dict[str, Any]]


class GoogleAIClientLLMConfig(LLMConfig):
    """
    Configuration for the Google AI (Gemini) client.

    This class centralizes settings for connecting to Google's Generative AI API
    with advanced features like grounding, thinking budgets, and system instructions.

    Important: Grounding and structured output are mutually exclusive.
    You must choose one:
    - Option A: Enable grounding for up-to-date web information (plain text responses
        only)
    - Option B: Use structured JSON/enum responses without grounding

    Attributes:
        model (str):
            The ID of the Gemini model to use for completions
            (e.g., "gemini-3-flash-preview", "gemini-2.5-flash-lite").
            Defaults to "gemini-3-flash-preview".
        api_key (str, optional):
            The Google AI API key for authentication. It's recommended to set this via
            the `GOOGLE_API_KEY` environment variable. Defaults to None.
        temperature (float):
            Controls randomness in the output. Lower values make the model more
            deterministic.
            Range: 0.0 to 2.0. Defaults to 0.1.
        top_p (float):
            Controls diversity via nucleus sampling. Lower values restrict the model to
            more probable tokens. Range: 0.0 to 1.0. Defaults to 0.95.
        max_tokens (int):
            The maximum number of tokens to generate in the completion.
            Defaults to 8192.
        use_grounding (bool):
            If True, enables Google Search grounding to base responses on
            up-to-date, verifiable information from the web. Defaults to False.

            NOTE: When grounding is enabled, you cannot use structured output
            (`response_mime_type` must be `"text/plain"` or None, and `response_schema`
            must be None). This is a Google API limitation.
        tools (Callable[..., Any], optional):
            Set of tools for the model can call to interact with external systems to
            perform an action outside of the knowledge and scope of the model.

            NOTE: When tools are provided, you cannot use structured output
            (`response_mime_type` must be `"text/plain"` or None, and `response_schema`
            must be None). This is a Google API limitation.
        system_instruction (str, optional):
            A default system-level instruction for the model, applied to all requests.
            This serves as persistent context for the conversation. Defaults to None.
        thinking_budget (int, optional):
            Controls the model's reasoning process for Gemini 2.5 models.
            Set to 0 to disable thinking (Flash models only). Higher values
            allow more thorough reasoning. Defaults to None (uses model default).
            NOTE: Use thinking_level for Gemini 3 models instead.
        thinking_level (str, optional):
            Controls the model's reasoning process for Gemini 3 models.
            Values: "minimal" (Flash only), "low", "medium", "high" (default).
            Defaults to None (uses model default "high").
        response_mime_type (str, optional):
            The MIME type for the response, such as `"application/json"` or
            `"text/plain"` or `"text/x.enum"`.
            This specifies the format of the model's output. Defaults to None.

            IMPORTANT: Cannot be used with grounding (use_grounding=True) or tools.
            If grounding or tools are enabled, this must be None or `"text/plain"`.
        response_schema (SchemaLike, optional):
            A Pydantic model or JSON schema to validate the response structure.
            This ensures the model's output adheres to a specific format.
            Defaults to None (no validation).

            IMPORTANT: Cannot be used with grounding (use_grounding=True) or tools.
            If grounding or tools are enabled, this must be None.
    """

    def __init__(
        self,
        model: str = "gemini-3-flash-preview",
        api_key: Optional[str] = None,
        temperature: float = 0.1,
        top_p: float = 0.95,
        max_tokens: int = 8192,
        use_grounding: bool = False,
        tools: Optional[Callable[..., Any]] = None,
        system_instruction: Optional[str] = None,
        thinking_budget: Optional[int] = None,
        thinking_level: Optional[str] = None,
        response_mime_type: Optional[str] = None,
        response_schema: Optional[SchemaLike] = None,
        **kwargs,
    ):
        # We explicitly set the backend to GOOGLE for this config type.
        super().__init__(backend=LLMBackend.GOOGLE, **kwargs)
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.use_grounding = use_grounding
        self.system_instruction = system_instruction
        self.thinking_budget = thinking_budget
        self.thinking_level = thinking_level
        self.response_mime_type = response_mime_type
        self.response_schema = response_schema
        self.tools = tools

        # Validate mutually exclusive options
        self._validate_config()

    def _validate_config(self) -> None:
        """
        Validates configuration constraints.

        Raises:
            ValueError: If invalid combinations are detected.
        """
        # Check thinking parameter mutual exclusion
        if self.thinking_budget is not None and self.thinking_level is not None:
            raise ValueError(
                "Cannot use both thinking_budget and thinking_level. Choose one:\n"
                "- thinking_budget (int): For Gemini 2.5 models\n"
                "- thinking_level (str): For Gemini 3 models "
                "('low', 'medium', 'high', 'minimal')"
            )

        # Check model-parameter mismatch
        is_gemini_3 = "gemini-3" in self.model
        if is_gemini_3 and self.thinking_budget is not None:
            raise ValueError(
                f"thinking_budget is not supported for Gemini 3 models ({self.model}). "
                "Use thinking_level instead ('low', 'medium', 'high', or 'minimal' "
                "for Flash)."
            )
        if not is_gemini_3 and self.thinking_level is not None:
            raise ValueError(
                "thinking_level is not supported for Gemini 2.5 models "
                f"({self.model}). Use thinking_budget instead "
                "(integer value, 0 to disable)."
            )

        # Check grounding/tools vs structured output
        if self.use_grounding or self.tools:
            has_structured_mime_type = (
                self.response_mime_type is not None
                and self.response_mime_type != "text/plain"
            )
            has_response_schema = self.response_schema is not None

            if has_structured_mime_type or has_response_schema:
                raise ValueError(
                    "Cannot use grounding or tools with structured output. "
                    "Choose one:\n"
                    "- Option A: use_grounding=True or provide tools with "
                    "response_mime_type=None/text/plain and response_schema=None\n"
                    "- Option B: use_grounding=False and tools=None with "
                    "response_mime_type/response_schema for structured output"
                )
