# Database Migration Scripts

Scripts for backing up and restoring FalkorDB (graph) and Milvus (vector) databases.

## Quick Start

### Backup (Create migration package)
```bash
# Backup and create zip package
make backup-package
# → Creates backups/backup.zip
```

### Restore (On target machine)
```bash
# Copy backups/backup.zip to target machine
# Then run:
make restore-package
# → Extracts and restores both databases
```

## Individual Commands

### Backup Commands
```bash
make backup-graph      # Backup FalkorDB → backups/falkordb/
make backup-vector     # Backup Milvus → backups/milvus/
make backup-all        # Backup both databases
make backup-package    # Backup all + create zip
```

### Restore Commands
```bash
make restore-graph     # Restore FalkorDB from CSV
make restore-vector    # Restore Milvus (upload to MinIO + API)
make restore-all       # Restore both databases
make restore-package   # Extract zip + restore all
```

## Scripts

### FalkorDB
- `falkordb_backup.py` - Export graph to `nodes.csv` and `edges.csv`
- `falkordb_restore.py` - Import from CSV using MERGE (idempotent)

### Milvus
- `milvus_backup.py` - Create backup via API + download from MinIO
- `milvus_restore.py` - Upload to MinIO + trigger restore API

## Output Structure

```
backups/
├── backup.zip              # Complete migration package
├── falkordb/
│   ├── nodes.csv           # All nodes
│   ├── edges.csv           # All edges
│   └── metadata.json       # Backup stats
└── milvus/
    └── brandmind_backup/   # Milvus backup files
        ├── meta/
        └── binlogs/
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FALKORDB_PORT` | 6380 | FalkorDB port |
| `FALKORDB_USERNAME` | brandmind | FalkorDB username |
| `FALKORDB_PASSWORD` | password | FalkorDB password |
| `MINIO_PORT` | 9000 | MinIO port |
| `MINIO_ACCESS_KEY` | minioadmin | MinIO access key |
| `MINIO_SECRET_KEY` | minioadmin_secret | MinIO secret key |
| `MILVUS_BACKUP_PORT` | 8090 | Milvus backup API port |
