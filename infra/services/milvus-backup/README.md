# Milvus Backup Service

Docker container for [milvus-backup](https://github.com/zilliztech/milvus-backup) tool.

## Building

The image is built automatically by docker-compose:

```bash
docker-compose build milvus-backup
```

Or manually:

```bash
cd infra/services/milvus-backup
docker build -t milvus-backup .
```

## Usage

### Start the service

```bash
docker-compose up -d milvus-backup
```

### API Endpoints

The backup service exposes a REST API on port 8080.

**Create backup:**
```bash
curl -X POST 'http://localhost:8080/api/v1/create' \
    -H 'Content-Type: application/json' \
    -d '{
        "backup_name": "my_backup",
        "collection_names": ["DocumentChunks", "EntityDescriptions", "RelationDescriptions"]
    }'
```

**List backups:**
```bash
curl 'http://localhost:8080/api/v1/list'
```

**Restore backup:**
```bash
curl -X POST 'http://localhost:8080/api/v1/restore' \
    -H 'Content-Type: application/json' \
    -d '{
        "backup_name": "my_backup",
        "collection_suffix": ""
    }'
```

**Health check:**
```bash
curl 'http://localhost:8080/api/v1/health'
```

## Configuration

The service uses `/app/configs/backup.yaml` for configuration.
This is mounted from `infra/configs/backup.yaml`.

## Backup Storage

Backups are stored in MinIO (same bucket as Milvus data).
The backup directory is also mounted to `./backups/milvus/` for local access.
