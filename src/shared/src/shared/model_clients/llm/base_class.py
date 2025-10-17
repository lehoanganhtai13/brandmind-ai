from enum import Enum
from typing import AsyncGenerator, Generator, Optional
from pydantic import BaseModel


class LLMBackend(Enum):
    """Enum for different LLM backends."""
    OPENAI = "openai"
    LITELLM = "litellm"
    GOOGLE = "google"


class LLMConfig:
    """Base configuration for LLM."""
    def __init__(self, backend: LLMBackend, **kwargs):
        self.backend = backend
        self.config = kwargs


class CompletionResponse(BaseModel):
    """
    Completion response.

    Attributes:
        text (str): Text content of the response if not streaming, or if streaming,
            the current extent of streamed text.
        delta (Optional[str]): New text that just streamed in (only relevant when streaming).
    """

    text: str
    delta: Optional[str] = None

    def __str__(self) -> str:
        return self.text


CompletionResponseGen = Generator[CompletionResponse, None, None]
"""Generator yielding CompletionResponse objects."""
CompletionResponseAsyncGen = AsyncGenerator[CompletionResponse, None]
"""Async generator yielding CompletionResponse objects."""
