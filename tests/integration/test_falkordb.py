import os
import pytest
from shared.database_clients.graph_database.falkordb.client import FalkorDBClient
from shared.database_clients.graph_database.falkordb.config import FalkorDBConfig
from shared.database_clients.graph_database.base_class import RelationDirection

# Skip tests if FALKORDB_HOST is not set (CI/CD check)
# But locally we expect it to run if docker is up
@pytest.mark.integration
class TestFalkorDBIntegration:
    @pytest.fixture
    def client(self):
        """Setup FalkorDB client for testing."""
        config = FalkorDBConfig(
            host=os.getenv("FALKORDB_HOST", "localhost"),
            port=int(os.getenv("FALKORDB_PORT", 6380)),
            username=os.getenv("FALKORDB_USERNAME", "brandmind"),
            password=os.getenv("FALKORDB_PASSWORD", "password"),
            graph_name="test_graph_integration"
        )
        client = FalkorDBClient(config=config)
        yield client
        # Cleanup after tests
        try:
            client.delete_graph("test_graph_integration")
        except:
            pass

    def test_connection(self, client):
        """Test simple connection and query."""
        result = client.execute_query("RETURN 1")
        assert result.result_set[0][0] == 1

    def test_node_crud(self, client):
        """Test Node Create, Read, Update, Delete."""
        # Create
        node_id = client.create_node(
            "TestEntity", 
            {"name": "TestNode", "value": 123}
        )
        assert node_id is not None
        
        # Read
        node = client.get_node(
            "TestEntity", 
            {"name": "TestNode"}
        )
        assert node is not None
        assert node["properties"]["name"] == "TestNode"
        assert node["properties"]["value"] == 123
        
        # Update (Merge)
        updated_id = client.merge_node(
            "TestEntity",
            {"name": "TestNode"},
            {"value": 456, "status": "updated"}
        )
        assert updated_id == node_id
        
        updated_node = client.get_node("TestEntity", {"name": "TestNode"})
        assert updated_node["properties"]["value"] == 456
        assert updated_node["properties"]["status"] == "updated"
        
        # Delete
        deleted = client.delete_node("TestEntity", {"name": "TestNode"})
        assert deleted is True
        
        # Verify Delete
        node = client.get_node("TestEntity", {"name": "TestNode"})
        assert node is None

    def test_relationship_crud(self, client):
        """Test Relationship Create and Query."""
        # Setup nodes
        client.create_node("Person", {"name": "Alice"})
        client.create_node("Person", {"name": "Bob"})
        
        # Create Relationship
        created = client.create_relationship(
            source_label="Person",
            source_match={"name": "Alice"},
            target_label="Person",
            target_match={"name": "Bob"},
            relation_type="knows",
            properties={"since": 2023}
        )
        assert created is True
        
        # Query Neighbors (Outgoing)
        neighbors = client.get_neighbors(
            label="Person",
            match_properties={"name": "Alice"},
            direction=RelationDirection.OUTGOING
        )
        assert len(neighbors) == 1
        assert neighbors[0]["properties"]["name"] == "Bob"
        assert neighbors[0]["relation_type"] == "KNOWS"
        
        # Query Neighbors (Incoming)
        neighbors = client.get_neighbors(
            label="Person",
            match_properties={"name": "Bob"},
            direction=RelationDirection.INCOMING
        )
        assert len(neighbors) == 1
        assert neighbors[0]["properties"]["name"] == "Alice"

    def test_batch_operations(self, client):
        """Test Batch Merge Nodes."""
        nodes_data = [
            {"id": 1, "name": "Node1"},
            {"id": 2, "name": "Node2"},
            {"id": 3, "name": "Node3"}
        ]
        
        count = client.batch_merge_nodes(
            label="BatchNode",
            match_key="id",
            nodes_data=nodes_data
        )
        assert count == 3
        
        # Verify
        nodes = client.get_nodes_by_label("BatchNode", limit=10)
        assert len(nodes) == 3
