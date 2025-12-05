# FalkorDB Docker Setup

Self-hosted FalkorDB graph database with Docker Compose, featuring environment variable-based password configuration.

## What is FalkorDB?

FalkorDB is a super-fast graph database optimized for:
- **GraphRAG** (Graph Retrieval-Augmented Generation) for AI/LLM applications
- **Knowledge Graphs** with Cypher query language
- **High Performance** using GraphBLAS sparse matrix representation
- **Redis Protocol** compatibility (port 6379)

## Quick Start

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and set your password:**
   ```bash
   FALKORDB_USERNAME=brandmind
   FALKORDB_PASSWORD=your_secure_password_here
   ```

3. **Start FalkorDB:**
   ```bash
   docker compose up -d
   ```

4. **Verify it's running:**
   ```bash
   docker compose logs -f falkordb
   ```

5. **Access Browser UI:**
   Open your browser and navigate to: http://localhost:3000
   
   **Login credentials:**
   - Host: `localhost`
   - Port: `6379` (internal port, NOT 6380)
   - Username: `brandmind`
   - Password: `password` (or your custom password from .env)

## Configuration

### Environment Variables

- `FALKORDB_USERNAME` - ACL username (default: `brandmind`)
- `FALKORDB_PASSWORD` - ACL password (default: `password`)

### Ports

- `6380` - FalkorDB server (mapped from container's 6379)
- `3000` - FalkorDB Browser UI (web interface)

> [!IMPORTANT]
> **Port Configuration:**
> - External access (from your machine): Use port `6380`
> - Browser UI login (from within container): Use port `6379`
> 
> The Browser UI runs inside the container, so it connects to the internal port `6379`, not the external mapped port `6380`.

### Files

- `docker-compose.yml` - Docker Compose configuration
- `docker-entrypoint.sh` - Custom entrypoint that processes config template
- `conf/falkordb.conf.template` - Configuration template with env var placeholders
- `.env` - Your environment variables (create from `.env.example`)

## Usage

### Connect with redis-cli

```bash
# From host
docker exec -it falkordb-container redis-cli

# Authenticate
AUTH brandmind your_password

# Test
PING
```

### Create a Graph (Cypher)

```bash
# Create a simple graph
GRAPH.QUERY MotoGP "CREATE (:Rider {name:'Valentino Rossi'})-[:rides]->(:Team {name:'Yamaha'})"

# Query the graph
GRAPH.QUERY MotoGP "MATCH (r:Rider)-[:rides]->(t:Team) WHERE t.name = 'Yamaha' RETURN r.name"
```

### Connect from Python

```python
from falkordb import FalkorDB

# Connect to FalkorDB
db = FalkorDB(
    host='localhost',
    port=6380,
    username='brandmind',
    password='your_password'
)

# Create a graph
g = db.select_graph('MotoGP')

# Create nodes and relationships
g.query("""
    CREATE (:Rider {name:'Valentino Rossi'})-[:rides]->(:Team {name:'Yamaha'}),
           (:Rider {name:'Dani Pedrosa'})-[:rides]->(:Team {name:'Honda'})
""")

# Query the graph
result = g.query("""
    MATCH (r:Rider)-[:rides]->(t:Team) 
    WHERE t.name = 'Yamaha' 
    RETURN r.name
""")

for row in result.result_set:
    print(row[0])  # Prints: Valentino Rossi
```

### Connect from JavaScript/TypeScript

```javascript
import { FalkorDB } from 'falkordb';

const db = await FalkorDB.connect({
    username: 'brandmind',
    password: 'your_password',
    socket: {
        host: 'localhost',
        port: 6380
    }
});

const graph = db.selectGraph('MotoGP');

// Create nodes and relationships
await graph.query(`
    CREATE (:Rider {name:'Valentino Rossi'})-[:rides]->(:Team {name:'Yamaha'})
`);

// Query the graph
const result = await graph.query(`
    MATCH (r:Rider)-[:rides]->(t:Team) 
    WHERE t.name = $name 
    RETURN r.name
`, { params: { name: 'Yamaha' } });

console.log(result);
```

## How It Works

1. Docker Compose passes environment variables to the container
2. Custom entrypoint script (`docker-entrypoint.sh`) runs at startup
3. Script uses `sed` to replace `${FALKORDB_USERNAME}` and `${FALKORDB_PASSWORD}` in template
4. Generated config is saved to `/tmp/falkordb.conf`
5. FalkorDB server starts with the generated configuration

## Security Notes

⚠️ **Important:**
- Never commit `.env` file to git
- `.env` should be in `.gitignore`
- Use strong passwords in production
- Consider using Docker Secrets for production deployments

## Troubleshooting

### View generated config
```bash
docker exec falkordb-container cat /tmp/falkordb.conf
```

### Check environment variables
```bash
docker exec falkordb-container env | grep FALKORDB
```

### View logs
```bash
docker compose logs falkordb
```

### Test graph operations
```bash
docker exec -it falkordb-container redis-cli --user brandmind --pass your_password GRAPH.QUERY test "CREATE (:Node {name:'test'})"
```

## Key Differences from Redis/Valkey

- **Query Language**: Cypher (graph queries) in addition to Redis commands
- **Use Case**: Graph database for relationships, not just key-value
- **Memory Policy**: `noeviction` (graphs shouldn't lose data)
- **Commands**: `GRAPH.QUERY`, `GRAPH.DELETE`, `GRAPH.LIST`, etc.

## References

- [FalkorDB Official Site](https://www.falkordb.com/)
- [FalkorDB Documentation](https://docs.falkordb.com/)
- [FalkorDB GitHub](https://github.com/FalkorDB/FalkorDB)
- [FalkorDB Docker Hub](https://hub.docker.com/r/falkordb/falkordb)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
