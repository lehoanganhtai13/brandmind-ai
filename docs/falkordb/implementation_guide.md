# FalkorDB Implementation Guide

This document outlines the implementation details for integrating FalkorDB as a Graph Database module, similar to the existing Milvus implementation. It covers initialization, authentication, and core graph operations using the Python client.

## 1. Installation

Ensure the FalkorDB Python client is installed:

```bash
pip install falkordb
```

## 2. Initialization & Authentication

FalkorDB uses the Redis protocol. You can connect using a host and port, or a connection URL.

### Synchronous Client

```python
from falkordb import FalkorDB

# Initialize connection
# Default port is 6379
client = FalkorDB(host='localhost', port=6379, password='optional_password')

# Select a specific graph to work with
graph = client.select_graph('brand_knowledge_graph')
```

### Asynchronous Client

For high-performance applications (like the existing Milvus implementation), use the async client.

```python
import asyncio
from falkordb.asyncio import FalkorDB
from redis.asyncio import BlockingConnectionPool

async def init_async_client():
    # Use a connection pool for better performance
    pool = BlockingConnectionPool(
        host='localhost', 
        port=6379, 
        password='optional_password',
        max_connections=10, 
        timeout=5.0, 
        decode_responses=True
    )
    
    client = FalkorDB(connection_pool=pool)
    graph = client.select_graph('brand_knowledge_graph')
    return graph, pool

# Usage
# graph, pool = await init_async_client()
# ... operations ...
# await pool.aclose() # Cleanup
```

## 3. CRUD Operations (Nodes & Edges with Metadata)

FalkorDB uses **Cypher** query language. "Metadata" in graph databases is typically stored as **properties** on nodes and edges.

### 3.1 INSERT (Create)

**Create a Node with Metadata:**

```python
# Create a 'Brand' node with metadata (properties)
query = """
CREATE (n:Brand {
    name: $name,
    industry: $industry,
    founded_year: $year,
    status: 'active'
})
RETURN n
"""
params = {'name': 'Nike', 'industry': 'Apparel', 'year': 1964}
result = graph.query(query, params)
```

**Create an Edge with Metadata:**

```python
# Create a relationship between existing nodes
# Matches a Brand and a Product, then creates a 'PRODUCES' edge with metadata
query = """
MATCH (b:Brand {name: $brand_name}), (p:Product {name: $product_name})
CREATE (b)-[r:PRODUCES {
    since: $date,
    volume: $volume,
    region: 'global'
}]->(p)
RETURN r
"""
params = {
    'brand_name': 'Nike', 
    'product_name': 'Air Jordan',
    'date': '1984-11-17',
    'volume': 1000000
}
result = graph.query(query, params)
```

### 3.2 MODIFY (Update)

**Update Node Metadata:**

```python
# Update specific properties of a node
query = """
MATCH (n:Brand {name: $name})
SET n.status = $new_status, 
    n.last_updated = timestamp()
RETURN n
"""
params = {'name': 'Nike', 'new_status': 'premium'}
graph.query(query, params)
```

**Update Edge Metadata:**

```python
# Update properties on an edge
query = """
MATCH (:Brand {name: $brand_name})-[r:PRODUCES]->(:Product {name: $product_name})
SET r.volume = $new_volume
RETURN r
"""
params = {'brand_name': 'Nike', 'product_name': 'Air Jordan', 'new_volume': 2000000}
graph.query(query, params)
```

### 3.3 DELETE

**Delete a Node (and its edges):**

*Note: In Cypher, you cannot delete a node that still has relationships attached unless you use `DETACH DELETE`.*

```python
# Delete a specific node and all its relationships
query = """
MATCH (n:Brand {name: $name})
DETACH DELETE n
"""
params = {'name': 'Nike'}
graph.query(query, params)
```

**Delete a specific Edge:**

```python
# Delete just the relationship, keeping the nodes
query = """
MATCH (:Brand {name: $brand_name})-[r:PRODUCES]->(:Product {name: $product_name})
DELETE r
"""
graph.query(query, params)
```

## 4. Querying Data

### 4.1 GET All Outer Nodes (Multi-hop)

To find nodes connected to a start node at variable depths (e.g., friends of friends, or supply chain steps).

```python
# Find all nodes connected to 'Nike' within 1 to 3 hops
# Returns the path or just the end nodes
query = """
MATCH (start:Brand {name: $name})-[*1..3]-(end)
WHERE start <> end
RETURN DISTINCT end
"""
params = {'name': 'Nike'}
result = graph.query(query, params)

for record in result.result_set:
    node = record[0]
    print(f"Found connected node: {node.labels} - {node.properties}")
```

### 4.2 GET All Edges of a Node (with Target Nodes)

To retrieve a node's immediate context: all its relationships and the nodes on the other side.

```python
# Get all outgoing and incoming edges and the connected nodes
query = """
MATCH (n:Brand {name: $name})-[r]-(connected_node)
RETURN type(r) as relation_type, properties(r) as relation_props, connected_node
"""
params = {'name': 'Nike'}
result = graph.query(query, params)

for record in result.result_set:
    rel_type = record[0]
    rel_props = record[1]
    target_node = record[2]
    
    print(f"Relationship: {rel_type} {rel_props}")
        print(f"Connected to: {target_node.labels} {target_node.properties}")
```

## 5. Advanced Operations (Required for Production)

To build a robust Graph RAG system, you need more than just basic CRUD. The following features are essential for performance and data integrity.

### 5.1 Upsert (MERGE) - Idempotent Writes

When processing documents, you often encounter the same entities multiple times. Use `MERGE` to "Create if not exists, otherwise match".

**Upsert a Node:**

```python
# Ensure a Brand node exists, update its last_seen timestamp
query = """
MERGE (b:Brand {name: $name})
ON CREATE SET b.created_at = timestamp(), b.last_seen = timestamp()
ON MATCH SET b.last_seen = timestamp()
RETURN b
"""
params = {'name': 'Nike'}
graph.query(query, params)
```

**Upsert a Relationship:**

```python
# Ensure the relationship exists between two nodes
query = """
MATCH (b:Brand {name: $brand_name})
MATCH (p:Product {name: $product_name})
MERGE (b)-[r:PRODUCES]->(p)
ON CREATE SET r.since = timestamp()
RETURN r
"""
```

### 5.2 Batch Insertion (UNWIND)

Inserting nodes one by one is slow. Use `UNWIND` to process a list of dictionaries in a single query.

```python
# Batch insert multiple products
data = [
    {'name': 'Air Max', 'year': 1987},
    {'name': 'Air Force 1', 'year': 1982},
    {'name': 'Pegasus', 'year': 1983}
]

query = """
UNWIND $batch AS item
MERGE (p:Product {name: item.name})
SET p.release_year = item.year
"""
params = {'batch': data}
graph.query(query, params)
```

### 5.3 Indexing

Indexes are critical for performance when looking up nodes by properties (e.g., finding a starting node for RAG).

**Create an Index:**

```python
# Create an index on Brand names for fast lookup
query = "CREATE INDEX FOR (n:Brand) ON (n.name)"
graph.query(query)
```

**Full-Text Search Index:**

If you need to search for keywords within node properties (e.g., searching within a 'description' field).

```python
# Create a full-text index on Product descriptions
query = "CALL db.idx.fulltext.createNodeIndex('Product', 'description')"
graph.query(query)

# Query the full-text index
search_query = "CALL db.idx.fulltext.queryNodes('Product', 'running shoes') YIELD node RETURN node.name"
graph.query(search_query)
```

## 6. Implementation Notes for `src/shared`

When building the module in `src/shared/database_clients/graph_database/falkordb/`:

1.  **Base Class**: Create a `BaseGraphDatabase` similar to `BaseVectorDatabase` if one doesn't exist, or adapt the interface.
2.  **Configuration**: Use a `FalkorDBConfig` Pydantic model (host, port, password, ssl).
3.  **Connection Handling**: Implement `_initialize_client` to handle both sync and async clients (using `falkordb.asyncio`).
4.  **Error Handling**: Wrap FalkorDB exceptions (e.g., connection errors, query syntax errors) into custom application exceptions.
5.  **Type Safety**: Use `typing` for method arguments (e.g., `Dict[str, Any]` for metadata).

### Example Structure

```
src/shared/src/shared/database_clients/graph_database/
├── __init__.py
├── base.py             # Abstract base class
└── falkordb/
    ├── __init__.py
    ├── client.py       # Main implementation
    ├── config.py       # Pydantic config
    └── exceptions.py   # Custom exceptions
```
