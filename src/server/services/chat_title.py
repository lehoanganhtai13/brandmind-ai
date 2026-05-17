"""Auto-generate a short chat title from the first user message.

The web UI replaces the default ``Untitled`` row label in the chat
picker with a 3–4 word summary produced by Gemini Flash Lite. Keeping
the service inside ``server/services`` rather than the brand-strategy
domain stays honest about scope — the title is a UX label, not part
of the strategy artefact.
"""

from __future__ import annotations

from loguru import logger

from config.system_config import SETTINGS
from shared.model_clients.llm.google.config import GoogleAIClientLLMConfig
from shared.model_clients.llm.google.llm import GoogleAIClientLLM

_TITLE_SYSTEM_PROMPT = (
    "You are a chat title generator for a brand-strategy assistant. "
    "Given the user's first message, produce a 3 to 4 word title that "
    "captures what the chat is about. Match the user's language. Output "
    "only the title — no quotes, no trailing punctuation, no preface. "
    "Avoid generic words like 'question' or 'chat'. Be specific."
)

_MAX_FIRST_MESSAGE_CHARS = 1200
_MAX_TITLE_CHARS = 64


def _truncate(text: str) -> str:
    """Cap the first-message excerpt sent to Gemini to keep latency stable."""
    text = (text or "").strip()
    if len(text) <= _MAX_FIRST_MESSAGE_CHARS:
        return text
    return text[:_MAX_FIRST_MESSAGE_CHARS]


def _clean_title(raw: str) -> str:
    """Strip wrappers and clamp the model's title back to a sane length."""
    title = (raw or "").strip().strip('"').strip("'").rstrip(".!?…")
    title = " ".join(title.split())
    if len(title) > _MAX_TITLE_CHARS:
        title = title[:_MAX_TITLE_CHARS].rstrip() + "…"
    return title


async def generate_chat_title(first_message: str) -> str:
    """Summarise the first user message into a short chat-row label.

    Returns an empty string when generation fails — the caller treats
    that as "leave the existing title alone" so the sidebar gracefully
    falls back to its ``Untitled`` placeholder rather than surfacing a
    transient backend error.
    """
    message = _truncate(first_message)
    if not message:
        return ""
    llm = GoogleAIClientLLM(
        config=GoogleAIClientLLMConfig(
            model="gemini-2.5-flash-lite",
            api_key=SETTINGS.GEMINI_API_KEY,
            temperature=0.2,
            thinking_budget=0,
            response_mime_type="text/plain",
            system_instruction=_TITLE_SYSTEM_PROMPT,
        )
    )
    try:
        response = await llm.acomplete(message)
    except Exception as exc:
        logger.warning(f"chat title generation failed: {exc}")
        return ""
    return _clean_title(response.text)
