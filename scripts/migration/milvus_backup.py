"""
Milvus Backup Management - Create backup and download from MinIO.

This script handles:
1. Triggering backup via milvus-backup API
2. Downloading backup files from MinIO to local storage

Output:
    ./backups/milvus/
    └── brandmind_backup/   # Backup data from MinIO

Usage:
    # Create backup and download
    python scripts/migration/milvus_backup.py backup \
        --collections DocumentChunks,EntityDescriptions \
        --output ./backups/milvus

    # Download existing backup
    python scripts/migration/milvus_backup.py download \
        --backup-name brandmind_backup \
        --output ./backups/milvus
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import requests
from loguru import logger

try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:
    logger.error("minio package not installed. Run: uv sync --group migration")
    sys.exit(1)


def get_minio_client(
    endpoint: str = "localhost:9000",
    access_key: str = "minioadmin",
    secret_key: str = "minioadmin_secret",
) -> Minio:
    """Create MinIO client."""
    return Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=False,
    )


def delete_backup(
    backup_name: str,
    backup_api_url: str = "http://localhost:8090",
) -> bool:
    """Delete existing backup."""
    logger.info(f"Deleting existing backup '{backup_name}'...")
    try:
        response = requests.delete(
            f"{backup_api_url}/api/v1/delete",
            params={"backup_name": backup_name},
            timeout=60,
        )
        result = response.json()
        logger.info(f"Delete response: {result.get('msg', 'unknown')}")
        return result.get("msg") == "success"
    except Exception as e:
        logger.warning(f"Failed to delete backup: {e}")
        return False


def create_backup(
    backup_name: str,
    collections: list[str],
    backup_api_url: str = "http://localhost:8090",
    force: bool = True,
) -> dict:
    """
    Create Milvus backup via milvus-backup API.
    
    Args:
        backup_name: Name for the backup.
        collections: List of collection names to backup.
        backup_api_url: URL of milvus-backup API.
        force: If True, delete existing backup with same name.
    
    Returns:
        API response dict.
    """
    logger.info(f"Creating backup '{backup_name}' for collections: {collections}")
    
    # Try to create backup
    response = requests.post(
        f"{backup_api_url}/api/v1/create",
        headers={"Content-Type": "application/json"},
        json={
            "backup_name": backup_name,
            "collection_names": collections,
        },
        timeout=300,
    )
    
    result = response.json()
    
    # If backup already exists and force=True, delete and retry
    if "already exist" in result.get("msg", "") and force:
        logger.warning("Backup already exists, deleting and recreating...")
        delete_backup(backup_name, backup_api_url)
        
        # Retry create
        response = requests.post(
            f"{backup_api_url}/api/v1/create",
            headers={"Content-Type": "application/json"},
            json={
                "backup_name": backup_name,
                "collection_names": collections,
            },
            timeout=300,
        )
        result = response.json()
    
    logger.info(f"Backup API response: {result.get('msg', 'unknown')}")
    
    return result


def download_backup(
    backup_name: str,
    output_dir: Path,
    minio_endpoint: str = "localhost:9000",
    minio_access_key: str = "minioadmin",
    minio_secret_key: str = "minioadmin_secret",
    bucket_name: str = "a-bucket",
    backup_prefix: str = "backup",
) -> int:
    """
    Download Milvus backup from MinIO to local storage.
    
    Args:
        backup_name: Name of the backup to download.
        output_dir: Local directory to save backup files.
        minio_endpoint: MinIO server endpoint.
        minio_access_key: MinIO access key.
        minio_secret_key: MinIO secret key.
        bucket_name: MinIO bucket name.
        backup_prefix: Prefix path in bucket for backups.
    
    Returns:
        Number of files downloaded.
    """
    logger.info(f"Connecting to MinIO at {minio_endpoint}")
    
    client = get_minio_client(
        endpoint=minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
    )
    
    # Check if bucket exists
    if not client.bucket_exists(bucket_name):
        raise ValueError(f"Bucket '{bucket_name}' does not exist")
    
    # List all objects in backup path
    prefix = f"{backup_prefix}/{backup_name}/"
    logger.info(f"Searching for backup at: {bucket_name}/{prefix}")
    
    objects = list(client.list_objects(bucket_name, prefix=prefix, recursive=True))
    
    if not objects:
        raise FileNotFoundError(f"No backup found at {bucket_name}/{prefix}")
    
    logger.info(f"Found {len(objects)} files to download")
    
    # Create output directory
    backup_output = output_dir / backup_name
    backup_output.mkdir(parents=True, exist_ok=True)
    
    # Download each file
    downloaded = 0
    for obj in objects:
        # Get relative path within backup
        rel_path = obj.object_name.replace(prefix, "")
        if not rel_path:
            continue
            
        local_path = backup_output / rel_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Downloading: {obj.object_name} → {local_path}")
        client.fget_object(bucket_name, obj.object_name, str(local_path))
        downloaded += 1
    
    logger.info(f"✅ Downloaded {downloaded} files → {backup_output}/")
    
    return downloaded


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Milvus backup management - create and download backups."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create backup and download")
    backup_parser.add_argument(
        "--name", "-n",
        default="brandmind_backup",
        help="Backup name (default: brandmind_backup)",
    )
    backup_parser.add_argument(
        "--collections", "-c",
        default="DocumentChunks,EntityDescriptions,RelationDescriptions",
        help="Comma-separated collection names",
    )
    backup_parser.add_argument(
        "--api-url",
        default=os.getenv("MILVUS_BACKUP_URL", "http://localhost:8090"),
        help="Milvus backup API URL",
    )
    backup_parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("./backups/milvus"),
        help="Output directory",
    )
    backup_parser.add_argument("--minio-endpoint", default="localhost:9000")
    backup_parser.add_argument("--minio-access-key", default=os.getenv("MINIO_ACCESS_KEY_ID", "minioadmin"))
    backup_parser.add_argument("--minio-secret-key", default=os.getenv("MINIO_SECRET_ACCESS_KEY", "minioadmin_secret"))
    backup_parser.add_argument("--bucket", default="a-bucket")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download existing backup")
    download_parser.add_argument(
        "--name", "-n",
        default="brandmind_backup",
        help="Backup name to download",
    )
    download_parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("./backups/milvus"),
        help="Output directory",
    )
    download_parser.add_argument("--minio-endpoint", default="localhost:9000")
    download_parser.add_argument("--minio-access-key", default=os.getenv("MINIO_ACCESS_KEY_ID", "minioadmin"))
    download_parser.add_argument("--minio-secret-key", default=os.getenv("MINIO_SECRET_ACCESS_KEY", "minioadmin_secret"))
    download_parser.add_argument("--bucket", default="a-bucket")
    
    args = parser.parse_args()
    
    if args.command == "backup":
        try:
            # Create backup via API
            collections = [c.strip() for c in args.collections.split(",")]
            result = create_backup(args.name, collections, args.api_url)
            
            if result.get("msg") != "success":
                logger.error(f"Backup creation failed: {result}")
                sys.exit(1)
            
            # Download from MinIO
            download_backup(
                backup_name=args.name,
                output_dir=args.output,
                minio_endpoint=args.minio_endpoint,
                minio_access_key=args.minio_access_key,
                minio_secret_key=args.minio_secret_key,
                bucket_name=args.bucket,
            )
            
            logger.info("✅ Backup and download completed!")
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            sys.exit(1)
            
    elif args.command == "download":
        try:
            download_backup(
                backup_name=args.name,
                output_dir=args.output,
                minio_endpoint=args.minio_endpoint,
                minio_access_key=args.minio_access_key,
                minio_secret_key=args.minio_secret_key,
                bucket_name=args.bucket,
            )
            logger.info("✅ Download completed!")
            
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
