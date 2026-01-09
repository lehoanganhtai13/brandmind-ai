#!/bin/sh
# Entrypoint script for milvus-backup container
# Substitutes environment variables in the config template before starting

set -e

# Default values for environment variables
export MILVUS_ROOT_PASSWORD="${MILVUS_ROOT_PASSWORD:-Milvus_secret}"
export MINIO_ACCESS_KEY_ID="${MINIO_ACCESS_KEY_ID:-minioadmin}"
export MINIO_SECRET_ACCESS_KEY="${MINIO_SECRET_ACCESS_KEY:-minioadmin_secret}"

# Substitute environment variables in template
echo "Generating backup.yaml from template..."
envsubst < /app/configs/backup.yaml.template > /app/configs/backup.yaml

echo "Configuration generated:"
echo "  - MILVUS_ROOT_PASSWORD: ****"
echo "  - MINIO_ACCESS_KEY_ID: ${MINIO_ACCESS_KEY_ID}"
echo "  - MINIO_SECRET_ACCESS_KEY: ****"

# Create logs directory
mkdir -p /app/logs

# Execute the main command
echo "Starting milvus-backup server..."
exec /app/milvus-backup "$@"
