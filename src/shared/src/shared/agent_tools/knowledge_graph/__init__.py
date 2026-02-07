"""Knowledge graph agent tools.

This module provides tools for knowledge graph extraction agents,
including triple validation and output finalization capabilities.
"""

from shared.agent_tools.knowledge_graph.finalize_output import finalize_output
from shared.agent_tools.knowledge_graph.validate_triples import validate_triples

__all__ = ["validate_triples", "finalize_output"]

