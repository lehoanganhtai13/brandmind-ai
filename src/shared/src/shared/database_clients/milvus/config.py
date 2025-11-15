from shared.database_clients.base_class import VectorDBBackend, VectorDBConfig


class MilvusConfig(VectorDBConfig):
    """Configuration for Milvus database."""

    def __init__(
        self,
        host: str = "localhost",
        port: str = "19530",
        run_async: bool = False,
        **kwargs,
    ):
        super().__init__(VectorDBBackend.MILVUS, **kwargs)
        self.host = host
        self.port = port
        self.run_async = run_async
        self.uri = f"http://{host}:{port}"
