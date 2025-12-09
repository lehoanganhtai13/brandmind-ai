from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from shared.database_clients.graph_database.base_class import (
    GraphDBConfig,
    RelationDirection,
)


class BaseGraphDatabase(ABC):
    """
    Abstract base class for graph database operations.

    This class defines the interface for graph database operations
    including node and relationship CRUD operations. All implementations
    must provide both synchronous and asynchronous variants.
    """

    def __init__(self, config: GraphDBConfig, **kwargs):
        self.config = config
        self._initialize_client(**kwargs)

    @abstractmethod
    def _initialize_client(self, **kwargs) -> None:
        """Initialize the database client connection."""
        pass

    # === Node Operations (Sync) ===
    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute a raw Cypher query."""
        pass

    @abstractmethod
    def create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """Create a new node with given label and properties. Returns node ID."""
        pass

    @abstractmethod
    def merge_node(
        self,
        label: str,
        match_properties: Dict[str, Any],
        update_properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Merge (upsert) a node. Returns node ID."""
        pass

    @abstractmethod
    def get_node(self, label: str, match_properties: Dict[str, Any]) -> Optional[Dict]:
        """Get a single node matching the criteria."""
        pass

    @abstractmethod
    def get_nodes_by_label(self, label: str, limit: int = 100) -> List[Dict]:
        """Get all nodes with a given label."""
        pass

    @abstractmethod
    def update_node(
        self,
        label: str,
        match_properties: Dict[str, Any],
        update_properties: Dict[str, Any],
    ) -> bool:
        """Update properties of an existing node."""
        pass

    @abstractmethod
    def delete_node(
        self, label: str, match_properties: Dict[str, Any], detach: bool = True
    ) -> bool:
        """Delete a node matching the criteria. Use detach=True to delete edges too."""
        pass

    # === Relationship Operations (Sync) ===
    @abstractmethod
    def create_relationship(
        self,
        source_label: str,
        source_match: Dict[str, Any],
        target_label: str,
        target_match: Dict[str, Any],
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create a relationship between two nodes."""
        pass

    @abstractmethod
    def merge_relationship(
        self,
        source_label: str,
        source_match: Dict[str, Any],
        target_label: str,
        target_match: Dict[str, Any],
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Merge (upsert) a relationship between two nodes."""
        pass

    @abstractmethod
    def get_neighbors(
        self,
        label: str,
        match_properties: Dict[str, Any],
        relation_type: Optional[str] = None,
        direction: RelationDirection = RelationDirection.BOTH,
    ) -> List[Dict]:
        """Get neighboring nodes connected by relationships."""
        pass

    @abstractmethod
    def get_node_relationships(
        self,
        label: str,
        match_properties: Dict[str, Any],
        direction: RelationDirection = RelationDirection.BOTH,
    ) -> List[Dict]:
        """Get all relationships of a node with connected nodes."""
        pass

    # === Batch Operations (Sync) ===
    @abstractmethod
    def batch_merge_nodes(
        self, label: str, match_key: str, nodes_data: List[Dict[str, Any]]
    ) -> int:
        """Merge multiple nodes in a single query using UNWIND. Returns count."""
        pass

    # === Index & Graph Management (Sync) ===
    @abstractmethod
    def create_index(self, label: str, property_name: str) -> bool:
        """Create an index on a property for faster queries."""
        pass

    @abstractmethod
    def graph_exists(self, graph_name: str) -> bool:
        """Check if a graph exists."""
        pass

    @abstractmethod
    def delete_graph(self, graph_name: str) -> bool:
        """Delete an entire graph."""
        pass

    # === Async Variants ===
    @abstractmethod
    async def async_execute_query(
        self, query: str, params: Optional[Dict] = None
    ) -> Any: ...

    @abstractmethod
    async def async_create_node(
        self, label: str, properties: Dict[str, Any]
    ) -> str: ...

    @abstractmethod
    async def async_merge_node(
        self,
        label: str,
        match_properties: Dict[str, Any],
        update_properties: Optional[Dict[str, Any]] = None,
    ) -> str: ...

    @abstractmethod
    async def async_get_node(
        self, label: str, match_properties: Dict[str, Any]
    ) -> Optional[Dict]: ...

    @abstractmethod
    async def async_get_nodes_by_label(
        self, label: str, limit: int = 100
    ) -> List[Dict]: ...

    @abstractmethod
    async def async_update_node(
        self,
        label: str,
        match_properties: Dict[str, Any],
        update_properties: Dict[str, Any],
    ) -> bool: ...

    @abstractmethod
    async def async_delete_node(
        self, label: str, match_properties: Dict[str, Any], detach: bool = True
    ) -> bool: ...

    @abstractmethod
    async def async_create_relationship(
        self,
        source_label: str,
        source_match: Dict[str, Any],
        target_label: str,
        target_match: Dict[str, Any],
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool: ...

    @abstractmethod
    async def async_merge_relationship(
        self,
        source_label: str,
        source_match: Dict[str, Any],
        target_label: str,
        target_match: Dict[str, Any],
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool: ...

    @abstractmethod
    async def async_get_neighbors(
        self,
        label: str,
        match_properties: Dict[str, Any],
        relation_type: Optional[str] = None,
        direction: RelationDirection = RelationDirection.BOTH,
    ) -> List[Dict]: ...

    @abstractmethod
    async def async_batch_merge_nodes(
        self, label: str, match_key: str, nodes_data: List[Dict[str, Any]]
    ) -> int: ...

    @abstractmethod
    async def async_create_index(self, label: str, property_name: str) -> bool: ...
