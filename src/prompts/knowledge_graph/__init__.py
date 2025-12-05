"""Knowledge graph prompts."""

from prompts.knowledge_graph.cartographer_system_prompt import (
    CARTOGRAPHER_SYSTEM_PROMPT,
)
from prompts.knowledge_graph.cartographer_task_prompt import CARTOGRAPHER_TASK_PROMPT
from prompts.knowledge_graph.miner_system_prompt import (
    MINER_SYSTEM_PROMPT,
    SPECIALIZED_DOMAIN,
)
from prompts.knowledge_graph.miner_task_prompt import MINER_TASK_PROMPT_TEMPLATE
from prompts.knowledge_graph.miner_validation_prompt import VALIDATION_PROMPT_TEMPLATE

__all__ = [
    "CARTOGRAPHER_SYSTEM_PROMPT",
    "CARTOGRAPHER_TASK_PROMPT",
    "MINER_SYSTEM_PROMPT",
    "MINER_TASK_PROMPT_TEMPLATE",
    "SPECIALIZED_DOMAIN",
    "VALIDATION_PROMPT_TEMPLATE",
]
