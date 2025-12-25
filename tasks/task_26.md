# Task 26: Database Backup & Migration System

## 📌 Metadata

- **Epic**: Marketing AI Assistant
- **Priority**: High
- **Estimated Effort**: 1 week
- **Team**: Backend
- **Related Tasks**: Task 25 (TUI), Stage 4 (docs/brainstorm/stage_4.md)
- **Blocking**: Production deployment
- **Blocked by**: @suneox

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ [Component 1](#component-1-falkordb-backup--restore-module) - FalkorDB Backup & Restore
    - [x] ✅ [Component 2](#component-2-milvus-backup-docker-service) - Milvus Backup Docker Service
    - [x] ✅ [Component 3](#component-3-migration-cli--makefile) - Migration CLI & Makefile
- [/] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [x] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **FalkorDB Graph Exporter**: https://github.com/FalkorDB/graph-exporter
- **Milvus Backup Tool**: https://github.com/zilliztech/milvus-backup
- **Milvus Backup Docs**: https://milvus.io/docs/milvus_backup_cli.md
- **Existing FalkorDB Module**: `src/shared/src/shared/database_clients/graph_database/falkordb/`
- **Stage 4 Brainstorm**: `docs/brainstorm/stage_4.md`

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Project BrandMind AI đã hoàn thành ~50% với:
  - Knowledge Graph (FalkorDB): Entities + Relations
  - Vector Database (Milvus): Document chunks, Entity descriptions, Relation descriptions
- Cần migrate dữ liệu từ máy dev sang server production
- Không thể re-process từ đầu (tốn thời gian + API costs cho LLM/embedding)

### Mục tiêu

Implement hệ thống backup/restore hoàn chỉnh cho cả 2 databases:
1. **FalkorDB**: Export/Import graph data via CSV
2. **Milvus**: Backup/Restore via milvus-backup service
3. **Local storage**: Tất cả backup files lưu trong `./backups/`
4. **Makefile commands**: Dễ dàng thao tác

### Success Metrics / Acceptance Criteria

- **Backup**: `make backup-all` exports cả 2 DBs thành công
- **Restore**: `make restore-all` imports vào instance mới
- **Data integrity**: Count nodes/edges/vectors khớp với trước backup
- **Portability**: Backup package có thể copy sang máy khác và restore

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Dual Export/Import System**: 
- FalkorDB → CSV (nodes + edges by label/type) → Import via Cypher MERGE
- Milvus → milvus-backup API → Restore via milvus-backup

### Stack công nghệ

- **FalkorDB Backup**: Python script using existing `FalkorDBClient` module
- **Milvus Backup**: Docker service với milvus-backup (Go binary)
- **Storage**: Local `./backups/` directory
- **Orchestration**: Makefile + Python scripts

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         BACKUP WORKFLOW                              │
│                                                                      │
│  FalkorDB (6380)              Milvus (19530)                         │
│       │                            │                                 │
│       ▼                            ▼                                 │
│  falkordb_backup.py         milvus-backup API (8090)                 │
│       │                            │                                 │
│       ▼                            ▼                                 │
│  ./backups/falkordb/        MinIO → milvus_backup.py download        │
│  ├── nodes.csv              ./backups/milvus/brandmind_backup/       │
│  └── edges.csv              ├── meta/*.json                          │
│                             └── binlogs/*                            │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                        RESTORE WORKFLOW                              │
│                                                                      │
│  ./backups/falkordb/        ./backups/milvus/                        │
│       │                            │                                 │
│       ▼                            ▼                                 │
│  falkordb_restore.py        milvus-backup restore API                │
│  (MERGE nodes, CREATE edges)       │                                 │
│       │                            │                                 │
│       ▼                            ▼                                 │
│  FalkorDB (6380)              Milvus (19530)                         │
│  ✅ Graph restored           ✅ Collections restored                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Issues & Solutions

1. **FalkorDB chỉ có exporter, chưa có importer** 
   → Implement `falkordb_restore.py` using existing `FalkorDBClient` module

2. **Milvus backup cần Go runtime** 
   → Build Docker image với multi-stage (Go build → Alpine runtime)

3. **Node ID mapping khi restore** 
   → Use entity `name` + `type` as unique key (not internal ID)

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: FalkorDB Backup & Restore**

1. **Refactor & Enhance falkordb_backup.py**
   - Move to `scripts/migration/falkordb_backup.py`
   - Add password authentication support
   - Output to `./backups/falkordb/`
   - Add metadata file (backup timestamp, graph stats)

2. **Implement falkordb_restore.py**
   - Read CSV files from backup directory
   - Use `FalkorDBClient.merge_node()` for nodes
   - Use `FalkorDBClient.merge_relationship()` for edges
   - Handle node ID mapping (export name → internal ID)

### **Phase 2: Milvus Backup Docker Service**

1. **Create Dockerfile for milvus-backup**
   - Multi-stage build: Go 1.21 → Alpine
   - Clone zilliztech/milvus-backup repo
   - Build with `make all`
   - Copy binary to runtime image

2. **Add to docker-compose.yml**
   - New service: `milvus-backup`
   - Mount config: `infra/configs/backup.yaml`
   - Mount backup volume: `./backups/milvus:/backup`
   - Expose API: port 8080

3. **Create backup.yaml config**
   - Milvus connection settings
   - MinIO settings for backup storage

### **Phase 3: CLI & Makefile Integration**

1. **Create unified migration scripts**
   - `scripts/migration/backup_all.py`
   - `scripts/migration/restore_all.py`

2. **Add Makefile commands**
   - `make backup-graph` / `make restore-graph`
   - `make backup-vector` / `make restore-vector`
   - `make backup-all` / `make restore-all`

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1: FalkorDB Backup & Restore Module

#### Requirement 1 - Enhanced Backup Script

- **Requirement**: Backup FalkorDB graph to CSV with authentication and metadata
- **Implementation**:
  - `scripts/migration/falkordb_backup.py`
  ```python
  """
  FalkorDB Graph Backup - Export nodes and edges to CSV files.
  
  Exports graph data by label/type for portable backup.
  Uses existing FalkorDBClient for consistent connection handling.
  """
  import argparse
  import json
  from pathlib import Path
  from datetime import datetime
  from collections import defaultdict
  
  import pandas as pd
  from loguru import logger
  
  from shared.database_clients.graph_database.falkordb import (
      FalkorDBClient,
      FalkorDBConfig,
  )
  
  
  def backup_graph(
      graph_name: str,
      output_dir: Path,
      host: str = "localhost",
      port: int = 6379,
      password: str | None = None,
  ) -> dict:
      """
      Export FalkorDB graph to CSV files.
      
      Creates separate files for each node label and edge type:
      - nodes_{Label}.csv: All nodes with that label
      - edges_{TYPE}.csv: All edges of that type
      
      Args:
          graph_name: Name of the graph to export
          output_dir: Directory to save CSV files
          host: FalkorDB host
          port: FalkorDB port
          password: Optional password for authentication
      
      Returns:
          Backup metadata dict with statistics
      """
      config = FalkorDBConfig(
          host=host,
          port=port,
          password=password,
          graph_name=graph_name,
      )
      client = FalkorDBClient(config)
      
      output_dir.mkdir(parents=True, exist_ok=True)
      
      # Export nodes by label
      nodes_result = client.execute_query(
          "MATCH (n) RETURN labels(n)[0] as label, properties(n) as props"
      )
      nodes_by_label = defaultdict(list)
      for record in nodes_result.result_set:
          label = record[0] or "unlabeled"
          props = record[1] or {}
          nodes_by_label[label].append(props)
      
      for label, nodes in nodes_by_label.items():
          filename = output_dir / f"nodes_{label}.csv"
          pd.DataFrame(nodes).to_csv(filename, index=False)
          logger.info(f"Exported {len(nodes)} nodes [{label}] → {filename.name}")
      
      # Export edges by type
      edges_result = client.execute_query("""
          MATCH (a)-[e]->(b)
          RETURN TYPE(e) as type, 
                 properties(a).name as from_name,
                 labels(a)[0] as from_label,
                 properties(b).name as to_name,
                 labels(b)[0] as to_label,
                 properties(e) as props
      """)
      edges_by_type = defaultdict(list)
      for record in edges_result.result_set:
          edge_type = record[0]
          edge = {
              "from_name": record[1],
              "from_label": record[2],
              "to_name": record[3],
              "to_label": record[4],
              **(record[5] or {}),
          }
          edges_by_type[edge_type].append(edge)
      
      for edge_type, edges in edges_by_type.items():
          filename = output_dir / f"edges_{edge_type}.csv"
          pd.DataFrame(edges).to_csv(filename, index=False)
          logger.info(f"Exported {len(edges)} edges [{edge_type}] → {filename.name}")
      
      # Save metadata
      metadata = {
          "graph_name": graph_name,
          "backup_time": datetime.now().isoformat(),
          "node_labels": {k: len(v) for k, v in nodes_by_label.items()},
          "edge_types": {k: len(v) for k, v in edges_by_type.items()},
          "total_nodes": sum(len(v) for v in nodes_by_label.values()),
          "total_edges": sum(len(v) for v in edges_by_type.values()),
      }
      (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
      
      return metadata
  ```
- **Acceptance Criteria**:
  - [x] Exports all node labels to separate CSV files
  - [x] Exports all edge types to separate CSV files
  - [x] Saves metadata.json with backup statistics
  - [x] Supports password authentication

---

#### Requirement 2 - Restore Script

- **Requirement**: Import CSV backup into FalkorDB graph
- **Implementation**:
  - `scripts/migration/falkordb_restore.py`
  ```python
  """
  FalkorDB Graph Restore - Import nodes and edges from CSV backup.
  
  Uses MERGE operations for idempotent restore (can run multiple times safely).
  """
  import argparse
  import json
  from pathlib import Path
  
  import pandas as pd
  from loguru import logger
  
  from shared.database_clients.graph_database.falkordb import (
      FalkorDBClient,
      FalkorDBConfig,
  )
  
  
  def restore_graph(
      backup_dir: Path,
      graph_name: str,
      host: str = "localhost",
      port: int = 6379,
      password: str | None = None,
  ) -> dict:
      """
      Restore FalkorDB graph from CSV backup.
      
      Uses MERGE operations to upsert nodes and relationships.
      Safe to run multiple times (idempotent).
      
      Args:
          backup_dir: Directory containing CSV backup files
          graph_name: Target graph name
          host: FalkorDB host
          port: FalkorDB port
          password: Optional password
      
      Returns:
          Restore statistics
      """
      config = FalkorDBConfig(
          host=host,
          port=port,
          password=password,
          graph_name=graph_name,
      )
      client = FalkorDBClient(config)
      
      stats = {"nodes_restored": 0, "edges_restored": 0}
      
      # Restore nodes (by label)
      for csv_file in backup_dir.glob("nodes_*.csv"):
          label = csv_file.stem.replace("nodes_", "")
          df = pd.read_csv(csv_file)
          
          for _, row in df.iterrows():
              props = row.to_dict()
              # Remove NaN values
              props = {k: v for k, v in props.items() if pd.notna(v)}
              
              # Use 'name' as match key (unique identifier)
              if "name" in props:
                  match_props = {"name": props["name"]}
                  update_props = {k: v for k, v in props.items() if k != "name"}
                  client.merge_node(label, match_props, update_props)
                  stats["nodes_restored"] += 1
          
          logger.info(f"Restored {len(df)} nodes [{label}]")
      
      # Restore edges (by type)
      for csv_file in backup_dir.glob("edges_*.csv"):
          edge_type = csv_file.stem.replace("edges_", "")
          df = pd.read_csv(csv_file)
          
          for _, row in df.iterrows():
              source_name = row.get("from_name")
              source_label = row.get("from_label", "Entity")
              target_name = row.get("to_name")
              target_label = row.get("to_label", "Entity")
              
              # Edge properties (exclude from/to fields)
              props = {
                  k: v for k, v in row.to_dict().items()
                  if k not in ("from_name", "from_label", "to_name", "to_label")
                  and pd.notna(v)
              }
              
              client.merge_relationship(
                  source_label=source_label,
                  source_match={"name": source_name},
                  target_label=target_label,
                  target_match={"name": target_name},
                  relation_type=edge_type,
                  properties=props if props else None,
              )
              stats["edges_restored"] += 1
          
          logger.info(f"Restored {len(df)} edges [{edge_type}]")
      
      return stats
  ```
- **Acceptance Criteria**:
  - [x] Restores all nodes using MERGE (idempotent)
  - [x] Restores all edges with correct source/target mapping
  - [x] Handles missing/NaN values gracefully
  - [x] Logs progress during restore

---

### Component 2: Milvus Backup Docker Service

#### Requirement 1 - Docker Image for milvus-backup

- **Requirement**: Create Docker image with milvus-backup pre-built binary
- **Implementation**:
  - `infra/services/milvus-backup/Dockerfile`
  - Downloads pre-built binary from GitHub releases (v0.5.9)
  - Uses `envsubst` for runtime config generation
  
  ```dockerfile
  FROM alpine:3.19
  
  RUN apk add --no-cache ca-certificates curl gettext
  
  WORKDIR /app
  
  # Download pre-built binary
  ARG MILVUS_BACKUP_VERSION=0.5.9
  RUN curl -L -o milvus-backup.tar.gz \
      "https://github.com/zilliztech/milvus-backup/releases/download/v${MILVUS_BACKUP_VERSION}/milvus-backup_${MILVUS_BACKUP_VERSION}_Linux_x86_64.tar.gz" && \
      tar -xzf milvus-backup.tar.gz && chmod +x milvus-backup
  
  COPY entrypoint.sh /app/entrypoint.sh
  ENTRYPOINT ["/app/entrypoint.sh"]
  CMD ["server", "-p", "8080"]
  ```
- **Acceptance Criteria**:
  - [x] Dockerfile builds successfully
  - [x] Binary works in Alpine container
  - [x] Server starts on port 8080

---

#### Requirement 2 - Docker Compose Service

- **Requirement**: Add milvus-backup service to infrastructure
- **Implementation**:
  - Add to `infra/docker-compose.yml`:
  ```yaml
  # === Milvus Backup Service ===
  milvus-backup:
    build:
      context: ./services/milvus-backup
      dockerfile: Dockerfile
    container_name: milvus-backup
    ports:
      - "${MILVUS_BACKUP_PORT:-8080}:8080"
    volumes:
      - ./configs/backup.yaml:/app/configs/backup.yaml:ro
      - ../backups/milvus:/backup
    environment:
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-minioadmin}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-minioadmin_secret}
    depends_on:
      milvus:
        condition: service_healthy
      milvus-minio:
        condition: service_started
    networks:
      - brandmind-network
    restart: unless-stopped
  ```
- **Acceptance Criteria**:
  - [x] Service starts with docker-compose
  - [x] API accessible at http://localhost:8080
  - [x] Backup files appear in ./backups/milvus/

---

#### Requirement 3 - Backup Configuration with Environment Variables

- **Requirement**: Configure backup.yaml with environment variable support
- **Implementation**:
  - `infra/configs/backup.yaml.template` - Template with `${VAR}` placeholders
  - `infra/services/milvus-backup/entrypoint.sh` - Runs `envsubst` at container startup
  - Uses `gettext` package in Alpine for `envsubst` command
  
  **Template snippet:**
  ```yaml
  milvus:
    address: milvus-standalone
    port: 19530
    user: "root"
    password: "${MILVUS_ROOT_PASSWORD}"
  
  minio:
    accessKeyID: "${MINIO_ACCESS_KEY}"
    secretAccessKey: "${MINIO_SECRET_KEY}"
    bucketName: "a-bucket"
  ```
  
  **Entrypoint script:**
  ```bash
  #!/bin/sh
  export MILVUS_ROOT_PASSWORD="${MILVUS_ROOT_PASSWORD:-Milvus_secret}"
  export MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-minioadmin}"
  export MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-minioadmin_secret}"
  
  envsubst < /app/configs/backup.yaml.template > /app/configs/backup.yaml
  exec /app/milvus-backup "$@"
  ```
- **Acceptance Criteria**:
  - [x] Config uses environment variables from docker-compose
  - [x] Template is processed at container startup
  - [x] Default values match docker-compose defaults

---

### Component 3: Migration CLI & Makefile

#### Requirement 1 - Unified CLI Scripts

- **Requirement**: Single entry points for backup/restore operations
- **Implementation**:
  - `scripts/migration/backup_all.py`
  - `scripts/migration/restore_all.py`
  - These scripts call FalkorDB and Milvus backup/restore functions
- **Acceptance Criteria**:
  - [x] `python scripts/migration/falkordb_backup.py` backs up FalkorDB
  - [x] `python scripts/migration/falkordb_restore.py` restores FalkorDB

---

#### Requirement 2 - Makefile Commands

- **Requirement**: Easy-to-use make targets
- **Implementation**:
  - Add to `Makefile`:
  ```makefile
  # ========== Database Migration ==========
  
  .PHONY: backup-graph backup-vector backup-all restore-graph restore-vector restore-all
  
  backup-graph:
  	@echo "📦 Backing up FalkorDB graph..."
  	uv run python scripts/migration/falkordb_backup.py knowledge_graph \
  		--host localhost --port 6380 \
  		--output ./backups/falkordb
  
  backup-vector:
  	@echo "📦 Backing up Milvus collections..."
  	curl -X POST 'http://localhost:8080/api/v1/create' \
  		-H 'Content-Type: application/json' \
  		-d '{"backup_name": "brandmind_backup", "collection_names": ["DocumentChunks", "EntityDescriptions", "RelationDescriptions"]}'
  
  backup-all: backup-graph backup-vector
  	@echo "✅ Full backup complete → ./backups/"
  
  restore-graph:
  	@echo "🔄 Restoring FalkorDB graph..."
  	uv run python scripts/migration/falkordb_restore.py \
  		--backup-dir ./backups/falkordb \
  		--graph knowledge_graph \
  		--host localhost --port 6380
  
  restore-vector:
  	@echo "🔄 Restoring Milvus collections..."
  	curl -X POST 'http://localhost:8080/api/v1/restore' \
  		-H 'Content-Type: application/json' \
  		-d '{"backup_name": "brandmind_backup", "collection_suffix": ""}'
  
  restore-all: restore-graph restore-vector
  	@echo "✅ Full restore complete"
  ```
- **Acceptance Criteria**:
  - [x] All make commands work correctly
  - [x] Commands have helpful output messages

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: FalkorDB Backup
- **Purpose**: Verify graph exports correctly to CSV
- **Steps**:
  1. Ensure FalkorDB has data (knowledge_graph with entities/relations)
  2. Run `make backup-graph`
  3. Check `./backups/falkordb/` for CSV files
  4. Verify metadata.json has correct counts
- **Expected Result**: CSV files with all nodes/edges, matching metadata
- **Status**: ⏳ Pending

### Test Case 2: FalkorDB Restore
- **Purpose**: Verify graph restores from backup
- **Steps**:
  1. Delete or create new graph
  2. Run `make restore-graph`
  3. Query graph to verify node/edge counts
- **Expected Result**: Restored graph matches original backup stats
- **Status**: ⏳ Pending

### Test Case 3: Milvus Backup
- **Purpose**: Verify collections backup via API
- **Steps**:
  1. Start milvus-backup service: `docker-compose up milvus-backup`
  2. Run `make backup-vector`
  3. Check API response for success
  4. Verify backup files in MinIO/local
- **Expected Result**: Backup created successfully
- **Status**: ⏳ Pending

### Test Case 4: Milvus Restore
- **Purpose**: Verify collections restore from backup
- **Steps**:
  1. Drop collections (or use new Milvus instance)
  2. Run `make restore-vector`
  3. Query collections to verify data
- **Expected Result**: Collections restored with all vectors
- **Status**: ⏳ Pending

### Test Case 5: Full Migration (End-to-End)
- **Purpose**: Verify complete backup/restore workflow
- **Steps**:
  1. Run `make backup-all` on source machine
  2. Copy `./backups/` to new machine
  3. Start infrastructure: `make services-up`
  4. Run `make restore-all`
  5. Test TUI: `brandmind`
- **Expected Result**: BrandMind AI works identically on new machine
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: FalkorDB Backup & Restore
- [ ] [Component 2]: Milvus Backup Docker Service
- [ ] [Component 3]: Migration CLI & Makefile

**Files Created/Modified**:
```
scripts/migration/
├── falkordb_backup.py        # Export graph to nodes.csv + edges.csv
├── falkordb_restore.py       # Import graph from CSV using MERGE
├── milvus_backup.py          # Create backup + download from MinIO
├── milvus_restore.py         # Upload to MinIO + trigger restore API
└── README.md                 # Migration documentation

infra/
├── services/milvus-backup/
│   ├── Dockerfile            # Alpine + pre-built binary v0.5.9
│   └── entrypoint.sh         # envsubst config templating
├── configs/
│   └── backup.yaml.template  # Template with ${ENV_VAR} placeholders
└── docker-compose.yml        # Add milvus-backup service (port 8090)

backups/                      # Created during backup
├── backup.zip                # Complete migration package
├── falkordb/
│   ├── nodes.csv             # All nodes (18k+)
│   ├── edges.csv             # All edges (13k+)
│   └── metadata.json
└── milvus/
    └── brandmind_backup/
        ├── meta/*.json
        └── binlogs/*

Makefile                      # Migration commands added
pyproject.toml                # Added migration dependency group
```

**Makefile Commands**:
```bash
# Backup
make backup-graph           # FalkorDB → CSV
make backup-vector          # Milvus → MinIO → local download
make backup-all             # Both databases
make backup-package         # backup-all + zip + cleanup

# Restore
make restore-graph          # CSV → FalkorDB
make restore-vector         # Upload MinIO → Milvus restore
make restore-all            # Both databases
make restore-package        # Unzip + restore-all
```

**Key Features Delivered**:
1. **Portable Graph Backup**: Single nodes.csv + edges.csv (not per-label)
2. **Idempotent Restore**: MERGE operations safe to run multiple times
3. **Docker-based Milvus Backup**: Pre-built binary, no Go required
4. **MinIO Integration**: Python minio client for upload/download
5. **envsubst Config**: Environment variables in backup.yaml at runtime
6. **One-Command Migration**: `make backup-package` → `make restore-package`

------------------------------------------------------------------------
