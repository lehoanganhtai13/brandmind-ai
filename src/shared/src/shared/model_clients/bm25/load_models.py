from minio import Minio
from src.config.system_config import SETTINGS
from shared.model_clients.bm25.encoder import BM25Client


def init_bm25_client(
    endpoint: str,
    bucket_name: str,
    overwrite_existing: bool = False,
    init_without_load: bool = True,
    remove_after_load: bool = False
) -> BM25Client:
    """
    Initialize the BM25 client.
    
    Args:
        endpoint (str): The endpoint for the MinIO client.
        bucket_name (str): The name of the bucket to use.
        overwrite_existing (bool, optional): Whether to overwrite existing bucket in MinIO (defaults: False).
        init_without_load (bool, optional): Whether to initialize without loading the model from local or MinIO (defaults: True).
            In this case, the bucket will be created to store the model if it does not exist.
        remove_after_load (bool, optional): Whether to remove data after loading (defaults: False).

    Returns:
        BM25Client: The initialized BM25 client.
    """
    if not endpoint or not bucket_name:
        raise ValueError("Endpoint and bucket name must be provided.")

    minio_client = Minio(
        endpoint=endpoint,
        access_key=SETTINGS.MINIO_ACCESS_KEY_ID,
        secret_key=SETTINGS.MINIO_SECRET_ACCESS_KEY,
        secure=False
    )

    return BM25Client(
        storage=minio_client,
        bucket_name=bucket_name,
        overwrite_minio_bucket=overwrite_existing,
        init_without_load=init_without_load,
        remove_after_load=remove_after_load
    )
