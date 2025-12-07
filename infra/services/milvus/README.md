# Milvus Vector Database Setup

Self-hosted Milvus vector database with Docker Compose, featuring etcd for metadata, MinIO for object storage, and Attu UI for management.

## What is Milvus?

Milvus is an open-source vector database built for AI applications:
- **Vector Search**: Store and search high-dimensional vectors
- **Use Cases**: Semantic search, RAG, recommendation systems, image similarity
- **Performance**: Billion-scale vector search with millisecond latency
- **Compatibility**: Works with popular AI frameworks (LangChain, LlamaIndex, etc.)

## Architecture

This setup includes 4 services:

1. **Milvus Server** (port 19530) - Vector database engine
2. **etcd** (internal) - Metadata storage for schemas and indexes
3. **MinIO** (internal) - Object storage for vector data
4. **Attu UI** (port 3001) - Web-based management interface

## Quick Start

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and set your password:**
   ```bash
   MINIO_ROOT_PASSWORD=your_secure_password_here
   ```

3. **Start Milvus:**
   ```bash
   docker compose up -d
   ```

4. **Verify it's running:**
   ```bash
   docker compose logs -f milvus
   ```

5. **Access Attu UI:**
   Open your browser and navigate to: http://localhost:3001
   
   **Connection settings:**
   - Host: `milvus`
   - Port: `19530`
   - Authentication: Leave blank (disabled by default)
   
   > [!TIP]
   > If you enable authentication (see Authentication section), use:
   > - Username: `root`
   > - Password: `Milvus` (default)

## Configuration

### Environment Variables

- `MILVUS_PORT` - Milvus gRPC port (default: `19530`)
- `MILVUS_METRICS_PORT` - Metrics/health port (default: `9091`)
- `ATTU_PORT` - Attu UI port (default: `3001`)
- `MINIO_ROOT_USER` - MinIO username (default: `minioadmin`)
- `MINIO_ROOT_PASSWORD` - MinIO password (change this!)

> [!NOTE]
> **Authentication**: Milvus runs **without authentication by default**. To enable authentication, you need to mount a custom `milvus.yaml` config file (see Authentication section below).

### Ports

- `19530` - Milvus gRPC API (vector operations)
- `9091` - Milvus metrics and health check
- `3001` - Attu UI (web interface)

### Files

- `docker-compose.yml` - Docker Compose configuration with all services
- `.env` - Your environment variables (create from `.env.example`)

> [!NOTE]
> Milvus configuration is done entirely through environment variables in `docker-compose.yml`.
> No separate config file is needed.

## Usage

### Connect from Python

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

# Connect to Milvus
connections.connect(
    alias="default",
    host="localhost",
    port="19530",
    user="root",
    password="Milvus"
)

# Create a collection
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=512)
]
schema = CollectionSchema(fields=fields, description="Test collection")
collection = Collection(name="test_collection", schema=schema)

# Insert vectors
import numpy as np
vectors = np.random.rand(100, 128).tolist()
texts = [f"text_{i}" for i in range(100)]
collection.insert([vectors, texts])

# Create index
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "L2",
    "params": {"nlist": 128}
}
collection.create_index(field_name="embedding", index_params=index_params)

# Load collection
collection.load()

# Search
search_vectors = np.random.rand(1, 128).tolist()
search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
results = collection.search(
    data=search_vectors,
    anns_field="embedding",
    param=search_params,
    limit=10,
    output_fields=["text"]
)

print(results)
```

### Using Existing Milvus Client

The project already has a Milvus client in `src/shared/src/shared/database_clients/milvus/`:

```python
from shared.database_clients.milvus import MilvusVectorDatabase, MilvusConfig

# Configure
config = MilvusConfig(
    host="localhost",
    port="19530"
)

# Initialize
db = MilvusVectorDatabase(config=config)

# Use the database
# (See client code for available methods)
```

## Authentication

### Authentication is Enabled by Default

Milvus is configured with authentication **enabled** via environment variables:

```yaml
environment:
  COMMON_SECURITY_AUTHORIZATIONENABLED: ${MILVUS_AUTH_ENABLED:-true}
  COMMON_SECURITY_DEFAULTROOTPASSWORD: ${MILVUS_ROOT_PASSWORD:-Milvus}
```

### Default Credentials

- **Username**: `root`
- **Password**: `Milvus` (or value from `MILVUS_ROOT_PASSWORD` env var)

> [!WARNING]
> **Change the default password immediately in production!**

### Environment Variables

Configure authentication in `.env` file:

```bash
# Enable/disable authentication
MILVUS_AUTH_ENABLED=true

# Set root password
MILVUS_ROOT_PASSWORD=your_secure_password
```

### Connecting with Authentication

**Python:**
```python
from pymilvus import connections

connections.connect(
    host="localhost",
    port="19530",
    user="root",
    password="Milvus"  # or your custom password
)
```

**Using Project's Milvus Client:**
```python
from shared.database_clients.milvus import MilvusVectorDatabase, MilvusConfig

config = MilvusConfig(
    host="localhost",
    port="19530"
)
db = MilvusVectorDatabase(config=config)
# Note: Current client doesn't support auth yet - needs update
```

### Change Root Password

```python
from pymilvus import connections, utility

# Connect with current password
connections.connect(
    host="localhost",
    port="19530",
    user="root",
    password="Milvus"
)

# Change password
utility.reset_password(
    user="root",
    old_password="Milvus",
    new_password="your_new_secure_password"
)
```

### Create Application User

Instead of using root, create a dedicated user:

```python
from pymilvus import connections, utility

connections.connect(host="localhost", port="19530", user="root", password="Milvus")

# Create new user
utility.create_user(user="app_user", password="app_password")

# Grant privileges
utility.create_role("app_role")
utility.grant_privilege(
    role_name="app_role",
    object_type="Global",
    privilege="*",
    object_name="*"
)
utility.add_user_to_role(username="app_user", role_name="app_role")
```

### Disable Authentication

To disable authentication, set in `.env`:

```bash
MILVUS_AUTH_ENABLED=false
```

Then restart:
```bash
docker compose restart milvus
```

## Management with Attu UI

Attu provides a web interface for:
- **Collections**: Create, view, delete collections
- **Data**: Browse and query vector data
- **Indexes**: Manage vector indexes
- **Users**: User and role management
- **System**: Monitor system status and metrics

Access at: http://localhost:3001

## Health Check

Check if Milvus is healthy:
```bash
curl http://localhost:9091/healthz
```

Expected response: `OK`

## Troubleshooting

### View logs
```bash
# All services
docker compose logs

# Specific service
docker compose logs milvus
docker compose logs etcd
docker compose logs minio
docker compose logs attu
```

### Check service status
```bash
docker compose ps
```

### Test connection
```bash
# Using Python
python -c "from pymilvus import connections; connections.connect(host='localhost', port='19530'); print('Connected!')"
```

### Common Issues

**Issue: Milvus fails to start**
- Check etcd and MinIO are running: `docker compose ps`
- Check logs: `docker compose logs milvus`
- Ensure ports 19530, 9091, 3001 are not in use

**Issue: Cannot connect from Python**
- Verify Milvus is running: `curl http://localhost:9091/healthz`
- Check authentication is enabled and credentials are correct
- Ensure port 19530 is accessible

**Issue: Attu UI cannot connect**
- In Attu login, use host `milvus` (not `localhost`)
- Use port `19530` (internal port)
- Check Milvus is running and healthy

## Data Persistence

All data is persisted in Docker volumes:
- `etcd-data` - Metadata (schemas, indexes)
- `minio-data` - Vector data and index files
- `milvus-data` - Milvus runtime data

Data persists across container restarts. To completely remove data:
```bash
docker compose down -v
```

## Security Notes

⚠️ **Important:**
- Change default MinIO password in `.env`
- Change default Milvus root password after first login
- Add `.env` to `.gitignore`
- For production, use Docker Secrets or external secret management
- Enable TLS for production deployments

## Performance Tuning

For better performance:
- Adjust `ETCD_QUOTA_BACKEND_BYTES` for larger metadata
- Configure appropriate index type for your use case
- Monitor metrics at http://localhost:9091/metrics
- Scale to cluster mode for production workloads

## References

- [Milvus Official Docs](https://milvus.io/docs)
- [Milvus Python SDK](https://github.com/milvus-io/pymilvus)
- [Attu GitHub](https://github.com/zilliztech/attu)
- [Vector Index Types](https://milvus.io/docs/index.md)
- [Milvus Architecture](https://milvus.io/docs/architecture_overview.md)
