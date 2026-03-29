"""Pre-compact workspace notes middleware.

Injects a system reminder when the conversation approaches the context window
limit, instructing the agent to do an incremental workspace save before
summarization compresses older messages.
"""

from .middleware import PreCompactNotesMiddleware

__all__ = ["PreCompactNotesMiddleware"]
