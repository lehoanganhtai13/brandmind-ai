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
from prompts.knowledge_graph.name_normalization_instruction import (
    NAME_NORMALIZATION_INSTRUCTION,
)
from prompts.knowledge_graph.name_normalization_task_prompt import (
    NAME_NORMALIZATION_TASK_PROMPT,
)

__all__ = [
    "CARTOGRAPHER_SYSTEM_PROMPT",
    "CARTOGRAPHER_TASK_PROMPT",
    "MINER_SYSTEM_PROMPT",
    "MINER_TASK_PROMPT_TEMPLATE",
    "NAME_NORMALIZATION_INSTRUCTION",
    "NAME_NORMALIZATION_TASK_PROMPT",
    "SPECIALIZED_DOMAIN",
    "VALIDATION_PROMPT_TEMPLATE",
]
