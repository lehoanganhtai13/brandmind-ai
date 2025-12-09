from enum import Enum

from pydantic import BaseModel


class GraphDBBackend(Enum):
    """Enum for different graph database backends."""

    FALKORDB = "falkordb"
    NEO4J = "neo4j"  # Future support


class RelationDirection(Enum):
    """
    Enum for relationship direction in graph queries.

    Used in get_neighbors() to specify which direction to traverse:
    - OUTGOING: Follow edges going out from the node (source -> target)
    - INCOMING: Follow edges coming into the node (source <- target)
    - BOTH: Follow edges in both directions
    """

    OUTGOING = "OUTGOING"
    INCOMING = "INCOMING"
    BOTH = "BOTH"


class GraphDBConfig(BaseModel):
    """Base configuration for graph database."""

    backend: GraphDBBackend
    host: str = "localhost"
    port: int = 6379
    username: str = ""
    password: str = ""
    graph_name: str = "default"

    class Config:
        arbitrary_types_allowed = True
