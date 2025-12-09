from shared.database_clients.graph_database.base_class import (
    GraphDBBackend,
    GraphDBConfig,
)


class FalkorDBConfig(GraphDBConfig):
    """
    Configuration for FalkorDB database connection.

    Attributes:
        host: FalkorDB server host (default: localhost)
        port: FalkorDB server port (default: 6379, mapped to 6380 in docker)
        username: Authentication username (FALKORDB_USERNAME env var)
        password: Authentication password (FALKORDB_PASSWORD env var)
        graph_name: Name of the graph to work with
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        username: str = "",
        password: str = "",
        graph_name: str = "knowledge_graph",
        **kwargs,
    ):
        super().__init__(
            backend=GraphDBBackend.FALKORDB,
            host=host,
            port=port,
            username=username,
            password=password,
            graph_name=graph_name,
            **kwargs,
        )
