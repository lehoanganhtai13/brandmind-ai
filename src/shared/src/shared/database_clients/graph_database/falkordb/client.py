import asyncio
from typing import Any, Dict, List, Optional, cast

from falkordb import FalkorDB, Graph
from loguru import logger

from shared.database_clients.graph_database.base_class import RelationDirection
from shared.database_clients.graph_database.base_graph_database import (
    BaseGraphDatabase,
)
from shared.database_clients.graph_database.exceptions import (
    FalkorDBConnectionError,
    FalkorDBNodeError,
    FalkorDBQueryError,
    FalkorDBRelationshipError,
)
from shared.database_clients.graph_database.falkordb.config import FalkorDBConfig
from shared.database_clients.graph_database.falkordb.utils import (
    build_properties_string,
    sanitize_relation_type,
)


class FalkorDBClient(BaseGraphDatabase):
    """
    FalkorDB implementation for graph database operations.

    Example:
        >>> config = FalkorDBConfig(
        ...     host="localhost",
        ...     port=6379,
        ...     username="brandmind",
        ...     password="password",
        ...     graph_name="knowledge_graph"
        ... )
        >>> client = FalkorDBClient(config=config)
    """

    def _initialize_client(self, **kwargs) -> None:
        """Initialize FalkorDB client."""
        config: FalkorDBConfig = cast(FalkorDBConfig, self.config)

        try:
            self.client = FalkorDB(
                host=config.host,
                port=config.port,
                username=config.username if config.username else None,
                password=config.password if config.password else None,
            )
            self.graph: Graph = self.client.select_graph(config.graph_name)
            logger.info(f"Connected to FalkorDB at {config.host}:{config.port}")

        except Exception as e:
            raise FalkorDBConnectionError(f"Failed to connect to FalkorDB: {e}") from e

    # === Node Operations (Sync) ===

    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute a raw Cypher query."""
        try:
            result = self.graph.query(query, params or {})
            return result
        except Exception as e:
            raise FalkorDBQueryError(f"Query execution failed: {e}") from e

    def create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """Create a new node with given label and properties."""
        props_str = build_properties_string(properties)
        query = f"""
        CREATE (n:{label} {props_str})
        RETURN id(n) as node_id
        """
        try:
            result = self.graph.query(query, properties)
            if result.result_set:
                return str(result.result_set[0][0])
            raise FalkorDBNodeError("Node creation returned no ID")
        except Exception as e:
            raise FalkorDBNodeError(f"Failed to create node: {e}") from e

    def merge_node(
        self,
        label: str,
        match_properties: Dict[str, Any],
        update_properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Merge (upsert) a node using MERGE with ON CREATE/ON MATCH."""
        match_str = build_properties_string(match_properties)

        on_match_set = ""
        if update_properties:
            set_parts = [f"n.{k} = ${k}" for k in update_properties.keys()]
            on_match_set = f"ON MATCH SET {', '.join(set_parts)}"

        query = f"""
        MERGE (n:{label} {match_str})
        ON CREATE SET n.created_at = timestamp()
        {on_match_set}
        SET n.updated_at = timestamp()
        RETURN id(n) as node_id
        """

        params = {**match_properties, **(update_properties or {})}

        try:
            result = self.graph.query(query, params)
            if result.result_set:
                return str(result.result_set[0][0])
            raise FalkorDBNodeError("Node merge returned no ID")
        except Exception as e:
            raise FalkorDBNodeError(f"Failed to merge node: {e}") from e

    def get_node(self, label: str, match_properties: Dict[str, Any]) -> Optional[Dict]:
        """Get a single node matching the criteria."""
        match_str = build_properties_string(match_properties)
        query = f"""
        MATCH (n:{label} {match_str})
        RETURN n, id(n) as node_id
        LIMIT 1
        """
        try:
            result = self.graph.query(query, match_properties)
            if result.result_set:
                node = result.result_set[0][0]
                node_id = result.result_set[0][1]
                return {
                    "id": str(node_id),
                    "labels": node.labels,
                    "properties": node.properties,
                }
            return None
        except Exception as e:
            raise FalkorDBQueryError(f"Failed to get node: {e}") from e

    def get_nodes_by_label(self, label: str, limit: int = 100) -> List[Dict]:
        """Get all nodes with a given label."""
        query = f"""
        MATCH (n:{label})
        RETURN n, id(n) as node_id
        LIMIT $limit
        """
        try:
            result = self.graph.query(query, {"limit": limit})
            nodes = []
            for record in result.result_set:
                node = record[0]
                node_id = record[1]
                nodes.append(
                    {
                        "id": str(node_id),
                        "labels": node.labels,
                        "properties": node.properties,
                    }
                )
            return nodes
        except Exception as e:
            raise FalkorDBQueryError(f"Failed to get nodes: {e}") from e

    def update_node(
        self,
        label: str,
        match_properties: Dict[str, Any],
        update_properties: Dict[str, Any],
    ) -> bool:
        """Update properties of an existing node."""
        match_str = build_properties_string(match_properties)
        set_parts = [f"n.{k} = $upd_{k}" for k in update_properties.keys()]
        set_clause = ", ".join(set_parts)

        query = f"""
        MATCH (n:{label} {match_str})
        SET {set_clause}, n.updated_at = timestamp()
        RETURN n
        """

        params = {**match_properties}
        params.update({f"upd_{k}": v for k, v in update_properties.items()})

        try:
            result = self.graph.query(query, params)
            return len(result.result_set) > 0
        except Exception as e:
            raise FalkorDBNodeError(f"Failed to update node: {e}") from e

    def delete_node(
        self, label: str, match_properties: Dict[str, Any], detach: bool = True
    ) -> bool:
        """Delete a node. Use detach=True to delete edges too."""
        match_str = build_properties_string(match_properties)
        delete_cmd = "DETACH DELETE n" if detach else "DELETE n"

        query = f"""
        MATCH (n:{label} {match_str})
        {delete_cmd}
        """
        try:
            self.graph.query(query, match_properties)
            return True
        except Exception as e:
            raise FalkorDBNodeError(f"Failed to delete node: {e}") from e

    # === Relationship Operations (Sync) ===

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
        rel_type = sanitize_relation_type(relation_type)

        # Build property strings with prefixed params
        source_props = ", ".join([f"{k}: $s_{k}" for k in source_match.keys()])
        target_props = ", ".join([f"{k}: $t_{k}" for k in target_match.keys()])

        rel_props_str = ""
        if properties:
            rel_props = ", ".join([f"{k}: $r_{k}" for k in properties.keys()])
            rel_props_str = f"{{{rel_props}}}"

        query = f"""
        MATCH (s:{source_label} {{{source_props}}})
        MATCH (t:{target_label} {{{target_props}}})
        CREATE (s)-[r:{rel_type} {rel_props_str}]->(t)
        RETURN r
        """

        params = {}
        params.update({f"s_{k}": v for k, v in source_match.items()})
        params.update({f"t_{k}": v for k, v in target_match.items()})
        if properties:
            params.update({f"r_{k}": v for k, v in properties.items()})

        try:
            result = self.graph.query(query, params)
            return len(result.result_set) > 0
        except Exception as e:
            raise FalkorDBRelationshipError(
                f"Failed to create relationship: {e}"
            ) from e

    def merge_relationship(
        self,
        source_label: str,
        source_match: Dict[str, Any],
        target_label: str,
        target_match: Dict[str, Any],
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Merge (upsert) a relationship."""
        rel_type = sanitize_relation_type(relation_type)

        source_props = ", ".join([f"{k}: $s_{k}" for k in source_match.keys()])
        target_props = ", ".join([f"{k}: $t_{k}" for k in target_match.keys()])

        on_create_set = "ON CREATE SET r.created_at = timestamp()"
        if properties:
            prop_sets = ", ".join([f"r.{k} = $r_{k}" for k in properties.keys()])
            on_create_set += f", {prop_sets}"

        query = f"""
        MATCH (s:{source_label} {{{source_props}}})
        MATCH (t:{target_label} {{{target_props}}})
        MERGE (s)-[r:{rel_type}]->(t)
        {on_create_set}
        ON MATCH SET r.updated_at = timestamp()
        RETURN r
        """

        params = {}
        params.update({f"s_{k}": v for k, v in source_match.items()})
        params.update({f"t_{k}": v for k, v in target_match.items()})
        if properties:
            params.update({f"r_{k}": v for k, v in properties.items()})

        try:
            result = self.graph.query(query, params)
            return len(result.result_set) > 0
        except Exception as e:
            raise FalkorDBRelationshipError(f"Failed to merge relationship: {e}") from e

    def get_neighbors(
        self,
        label: str,
        match_properties: Dict[str, Any],
        relation_type: Optional[str] = None,
        direction: RelationDirection = RelationDirection.BOTH,
    ) -> List[Dict]:
        """Get neighboring nodes connected by relationships."""
        match_str = build_properties_string(match_properties)

        rel_filter = (
            f":{sanitize_relation_type(relation_type)}" if relation_type else ""
        )

        if direction == RelationDirection.OUTGOING:
            rel_pattern = f"-[r{rel_filter}]->"
        elif direction == RelationDirection.INCOMING:
            rel_pattern = f"<-[r{rel_filter}]-"
        else:
            rel_pattern = f"-[r{rel_filter}]-"

        query = f"""
        MATCH (n:{label} {match_str}){rel_pattern}(neighbor)
        RETURN DISTINCT neighbor, id(neighbor) as node_id, type(r) as rel_type
        """

        try:
            result = self.graph.query(query, match_properties)
            neighbors = []
            for record in result.result_set:
                node = record[0]
                node_id = record[1]
                rel_type = record[2]
                neighbors.append(
                    {
                        "id": str(node_id),
                        "labels": node.labels,
                        "properties": node.properties,
                        "relation_type": rel_type,
                    }
                )
            return neighbors
        except Exception as e:
            raise FalkorDBQueryError(f"Failed to get neighbors: {e}") from e

    def get_node_relationships(
        self,
        label: str,
        match_properties: Dict[str, Any],
        direction: RelationDirection = RelationDirection.BOTH,
    ) -> List[Dict]:
        """Get all relationships of a node with connected nodes."""
        match_str = build_properties_string(match_properties)

        if direction == RelationDirection.OUTGOING:
            rel_pattern = "-[r]->"
        elif direction == RelationDirection.INCOMING:
            rel_pattern = "<-[r]-"
        else:
            rel_pattern = "-[r]-"

        query = f"""
        MATCH (n:{label} {match_str}){rel_pattern}(connected)
        RETURN type(r) as rel_type, properties(r) as rel_props,
               connected, id(connected) as connected_id
        """

        try:
            result = self.graph.query(query, match_properties)
            relationships = []
            for record in result.result_set:
                relationships.append(
                    {
                        "relation_type": record[0],
                        "relation_properties": record[1],
                        "connected_node": {
                            "id": str(record[3]),
                            "labels": record[2].labels,
                            "properties": record[2].properties,
                        },
                    }
                )
            return relationships
        except Exception as e:
            raise FalkorDBQueryError(f"Failed to get relationships: {e}") from e

    # === Batch Operations (Sync) ===

    def batch_merge_nodes(
        self, label: str, match_key: str, nodes_data: List[Dict[str, Any]]
    ) -> int:
        """Merge multiple nodes using UNWIND."""
        if not nodes_data:
            return 0

        query = f"""
        UNWIND $batch AS item
        MERGE (n:{label} {{{match_key}: item.{match_key}}})
        SET n = item, n.updated_at = timestamp()
        RETURN count(n) as merged
        """

        try:
            result = self.graph.query(query, {"batch": nodes_data})
            if result.result_set:
                return result.result_set[0][0]
            return 0
        except Exception as e:
            raise FalkorDBNodeError(f"Batch merge failed: {e}") from e

    # === Graph Management (Sync) ===

    def create_index(self, label: str, property_name: str) -> bool:
        """Create an index on a property."""
        query = f"CREATE INDEX FOR (n:{label}) ON (n.{property_name})"
        try:
            self.graph.query(query)
            logger.info(f"Created index on {label}.{property_name}")
            return True
        except Exception as e:
            if "already indexed" in str(e).lower():
                logger.warning(f"Index on {label}.{property_name} already exists")
                return True
            raise FalkorDBQueryError(f"Failed to create index: {e}") from e

    def graph_exists(self, graph_name: str) -> bool:
        """Check if a graph exists."""
        try:
            graphs = self.client.list_graphs()
            return graph_name in graphs
        except Exception as e:
            raise FalkorDBQueryError(f"Failed to check graph: {e}") from e

    def delete_graph(self, graph_name: str) -> bool:
        """Delete an entire graph."""
        try:
            graph = self.client.select_graph(graph_name)
            graph.delete()
            logger.info(f"Deleted graph: {graph_name}")
            return True
        except Exception as e:
            raise FalkorDBQueryError(f"Failed to delete graph: {e}") from e

    # === Async Methods (wrap sync via asyncio.to_thread) ===

    async def async_execute_query(
        self, query: str, params: Optional[Dict] = None
    ) -> Any:
        return await asyncio.to_thread(self.execute_query, query, params)

    async def async_create_node(self, label: str, properties: Dict[str, Any]) -> str:
        return await asyncio.to_thread(self.create_node, label, properties)

    async def async_merge_node(
        self,
        label: str,
        match_properties: Dict[str, Any],
        update_properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        return await asyncio.to_thread(
            self.merge_node, label, match_properties, update_properties
        )

    async def async_get_node(
        self, label: str, match_properties: Dict[str, Any]
    ) -> Optional[Dict]:
        return await asyncio.to_thread(self.get_node, label, match_properties)

    async def async_get_nodes_by_label(
        self, label: str, limit: int = 100
    ) -> List[Dict]:
        return await asyncio.to_thread(self.get_nodes_by_label, label, limit)

    async def async_update_node(
        self,
        label: str,
        match_properties: Dict[str, Any],
        update_properties: Dict[str, Any],
    ) -> bool:
        return await asyncio.to_thread(
            self.update_node, label, match_properties, update_properties
        )

    async def async_delete_node(
        self, label: str, match_properties: Dict[str, Any], detach: bool = True
    ) -> bool:
        return await asyncio.to_thread(
            self.delete_node, label, match_properties, detach
        )

    async def async_create_relationship(
        self,
        source_label: str,
        source_match: Dict[str, Any],
        target_label: str,
        target_match: Dict[str, Any],
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        return await asyncio.to_thread(
            self.create_relationship,
            source_label,
            source_match,
            target_label,
            target_match,
            relation_type,
            properties,
        )

    async def async_merge_relationship(
        self,
        source_label: str,
        source_match: Dict[str, Any],
        target_label: str,
        target_match: Dict[str, Any],
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        return await asyncio.to_thread(
            self.merge_relationship,
            source_label,
            source_match,
            target_label,
            target_match,
            relation_type,
            properties,
        )

    async def async_get_neighbors(
        self,
        label: str,
        match_properties: Dict[str, Any],
        relation_type: Optional[str] = None,
        direction: RelationDirection = RelationDirection.BOTH,
    ) -> List[Dict]:
        return await asyncio.to_thread(
            self.get_neighbors, label, match_properties, relation_type, direction
        )

    async def async_batch_merge_nodes(
        self, label: str, match_key: str, nodes_data: List[Dict[str, Any]]
    ) -> int:
        return await asyncio.to_thread(
            self.batch_merge_nodes, label, match_key, nodes_data
        )

    async def async_create_index(self, label: str, property_name: str) -> bool:
        return await asyncio.to_thread(self.create_index, label, property_name)
