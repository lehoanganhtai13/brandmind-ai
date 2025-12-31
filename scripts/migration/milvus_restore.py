"""
Milvus Restore - Upload backup to MinIO and trigger restore.

This script handles:
1. Uploading backup files from local to MinIO
2. Triggering restore via milvus-backup API

Usage:
    # Restore from local backup
    python scripts/migration/milvus_restore.py restore \
        --backup-dir ./backups/milvus/brandmind_backup \
        --name brandmind_backup

    # Just upload backup to MinIO (without restore)
    python scripts/migration/milvus_restore.py upload \
        --backup-dir ./backups/milvus/brandmind_backup \
        --name brandmind_backup
"""

import argparse
import os
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

try:
    from pymilvus import connections, utility
    PYMILVUS_AVAILABLE = True
except ImportError:
    PYMILVUS_AVAILABLE = False


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


def upload_backup(
    backup_dir: Path,
    backup_name: str,
    minio_endpoint: str = "localhost:9000",
    minio_access_key: str = "minioadmin",
    minio_secret_key: str = "minioadmin_secret",
    bucket_name: str = "a-bucket",
    backup_prefix: str = "backup",
) -> int:
    """
    Upload local backup files to MinIO.
    
    Args:
        backup_dir: Local directory containing backup files.
        backup_name: Name of the backup in MinIO.
        minio_endpoint: MinIO server endpoint.
        minio_access_key: MinIO access key.
        minio_secret_key: MinIO secret key.
        bucket_name: MinIO bucket name.
        backup_prefix: Prefix path in bucket for backups.
    
    Returns:
        Number of files uploaded.
    """
    if not backup_dir.exists():
        raise FileNotFoundError(f"Backup directory not found: {backup_dir}")
    
    logger.info(f"Connecting to MinIO at {minio_endpoint}")
    
    client = get_minio_client(
        endpoint=minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
    )
    
    # Ensure bucket exists
    if not client.bucket_exists(bucket_name):
        logger.info(f"Creating bucket: {bucket_name}")
        client.make_bucket(bucket_name)
    
    # Upload all files from backup directory
    uploaded = 0
    for local_path in backup_dir.rglob("*"):
        if local_path.is_file():
            # Calculate relative path within backup
            rel_path = local_path.relative_to(backup_dir)
            object_name = f"{backup_prefix}/{backup_name}/{rel_path}"
            
            logger.debug(f"Uploading: {local_path} → {object_name}")
            client.fput_object(bucket_name, object_name, str(local_path))
            uploaded += 1
    
    logger.info(f"✅ Uploaded {uploaded} files to {bucket_name}/{backup_prefix}/{backup_name}/")
    
    return uploaded


def drop_collections(
    milvus_password: str,
    milvus_host: str = "localhost",
    milvus_port: int = 19530,
    collections: list[str] | None = None,
) -> int:
    """
    Drop existing Milvus collections before restore.
    
    Args:
        milvus_password: Milvus password.
        milvus_host: Milvus server host.
        milvus_port: Milvus server port.
        collections: List of collection names to drop. If None, drops all.
    
    Returns:
        Number of collections dropped.
    """
    if not PYMILVUS_AVAILABLE:
        logger.error("pymilvus not installed. Cannot drop collections.")
        return 0
    
    logger.info("Connecting to Milvus to drop existing collections...")
    connections.connect(
        host=milvus_host,
        port=milvus_port,
        user="root",
        password=milvus_password,
    )
    
    if collections is None:
        collections = utility.list_collections()
    
    dropped = 0
    for coll in collections:
        if utility.has_collection(coll):
            utility.drop_collection(coll)
            logger.info(f"  Dropped: {coll}")
            dropped += 1
    
    connections.disconnect("default")
    logger.info(f"✅ Dropped {dropped} collections")
    return dropped


def trigger_restore(
    backup_name: str,
    backup_api_url: str = "http://localhost:8090",
    collection_suffix: str = "",
) -> dict:
    """
    Trigger Milvus restore via milvus-backup API.
    
    Args:
        backup_name: Name of the backup to restore.
        backup_api_url: URL of milvus-backup API.
        collection_suffix: Optional suffix to add to restored collection names.
    
    Returns:
        API response dict.
    """
    logger.info(f"Triggering restore for backup '{backup_name}'...")
    
    response = requests.post(
        f"{backup_api_url}/api/v1/restore",
        headers={"Content-Type": "application/json"},
        json={
            "backup_name": backup_name,
            "collection_suffix": collection_suffix,
        },
        timeout=300,
    )
    
    result = response.json()
    logger.info(f"Restore API response: {result.get('msg', 'unknown')}")
    
    return result


def check_restore_status(
    restore_id: str,
    backup_api_url: str = "http://localhost:8090",
) -> dict:
    """Check status of a restore operation."""
    response = requests.get(
        f"{backup_api_url}/api/v1/get_restore",
        params={"id": restore_id},
        timeout=30,
    )
    return response.json()


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Milvus restore - upload backup to MinIO and trigger restore."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload backup to MinIO")
    upload_parser.add_argument(
        "--backup-dir", "-b",
        type=Path,
        required=True,
        help="Local directory containing backup files",
    )
    upload_parser.add_argument(
        "--name", "-n",
        default="brandmind_backup",
        help="Backup name in MinIO (default: brandmind_backup)",
    )
    upload_parser.add_argument("--minio-endpoint", default="localhost:9000")
    upload_parser.add_argument("--minio-access-key", default=os.getenv("MINIO_ACCESS_KEY", "minioadmin"))
    upload_parser.add_argument("--minio-secret-key", default=os.getenv("MINIO_SECRET_KEY", "minioadmin_secret"))
    upload_parser.add_argument("--bucket", default="a-bucket")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Upload and restore backup")
    restore_parser.add_argument(
        "--backup-dir", "-b",
        type=Path,
        required=True,
        help="Local directory containing backup files",
    )
    restore_parser.add_argument(
        "--name", "-n",
        default="brandmind_backup",
        help="Backup name (default: brandmind_backup)",
    )
    restore_parser.add_argument(
        "--api-url",
        default=os.getenv("MILVUS_BACKUP_URL", "http://localhost:8090"),
        help="Milvus backup API URL",
    )
    restore_parser.add_argument(
        "--suffix",
        default="",
        help="Suffix to add to restored collection names",
    )
    restore_parser.add_argument("--minio-endpoint", default="localhost:9000")
    restore_parser.add_argument("--minio-access-key", default=os.getenv("MINIO_ACCESS_KEY", "minioadmin"))
    restore_parser.add_argument("--minio-secret-key", default=os.getenv("MINIO_SECRET_KEY", "minioadmin_secret"))
    restore_parser.add_argument("--bucket", default="a-bucket")
    restore_parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing collections before restore (required for clean restore)",
    )
    restore_parser.add_argument("--milvus-host", default=os.getenv("MILVUS_HOST", "localhost"))
    restore_parser.add_argument("--milvus-port", type=int, default=int(os.getenv("MILVUS_PORT", "19530")))
    restore_parser.add_argument("--milvus-password", default=os.getenv("MILVUS_ROOT_PASSWORD", "Milvus_secret"))
    
    # Trigger command (just call restore API, assume backup already in MinIO)
    trigger_parser = subparsers.add_parser("trigger", help="Trigger restore (backup must be in MinIO)")
    trigger_parser.add_argument(
        "--name", "-n",
        default="brandmind_backup",
        help="Backup name to restore",
    )
    trigger_parser.add_argument(
        "--api-url",
        default=os.getenv("MILVUS_BACKUP_URL", "http://localhost:8090"),
        help="Milvus backup API URL",
    )
    trigger_parser.add_argument(
        "--suffix",
        default="",
        help="Suffix to add to restored collection names",
    )
    
    args = parser.parse_args()
    
    if args.command == "upload":
        try:
            upload_backup(
                backup_dir=args.backup_dir,
                backup_name=args.name,
                minio_endpoint=args.minio_endpoint,
                minio_access_key=args.minio_access_key,
                minio_secret_key=args.minio_secret_key,
                bucket_name=args.bucket,
            )
            logger.info("✅ Upload completed!")
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            sys.exit(1)
            
    elif args.command == "restore":
        try:
            # Drop existing collections if requested
            if args.drop_existing:
                drop_collections(
                    milvus_host=args.milvus_host,
                    milvus_port=args.milvus_port,
                    milvus_password=args.milvus_password,
                )
            
            # Upload backup to MinIO
            upload_backup(
                backup_dir=args.backup_dir,
                backup_name=args.name,
                minio_endpoint=args.minio_endpoint,
                minio_access_key=args.minio_access_key,
                minio_secret_key=args.minio_secret_key,
                bucket_name=args.bucket,
            )
            
            # Trigger restore via API
            result = trigger_restore(
                backup_name=args.name,
                backup_api_url=args.api_url,
                collection_suffix=args.suffix,
            )
            
            if result.get("msg") != "success":
                logger.error(f"Restore failed: {result}")
                sys.exit(1)
            
            logger.info("✅ Restore completed!")
            
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            sys.exit(1)
            
    elif args.command == "trigger":
        try:
            result = trigger_restore(
                backup_name=args.name,
                backup_api_url=args.api_url,
                collection_suffix=args.suffix,
            )
            
            if result.get("msg") != "success":
                logger.error(f"Restore failed: {result}")
                sys.exit(1)
            
            logger.info("✅ Restore triggered!")
            
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
