import asyncio
import traceback
from typing import Dict, List, Optional, cast

from loguru import logger
from pymilvus import (
    AnnSearchRequest,
    AsyncMilvusClient,
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    Function,
    FunctionType,
    MilvusClient,
    RRFRanker,
    connections,
)
from pymilvus.milvus_client import IndexParams

from shared.database_clients.vector_database.base_class import (
    EmbeddingData,
    EmbeddingType,
)
from shared.database_clients.vector_database.base_vector_database import (
    BaseVectorDatabase,
)
from shared.database_clients.vector_database.milvus.config import MilvusConfig
from shared.database_clients.vector_database.milvus.exceptions import (
    CreateMilvusCollectionError,
    GetMilvusItemsError,
    InsertMilvusVectorsError,
    MilvusConnectionError,
    SearchMilvusVectorsError,
)
from shared.database_clients.vector_database.milvus.utils import (
    IndexParam,
    IndexType,
    MetricType,
    SchemaField,
)


class MilvusVectorDatabase(BaseVectorDatabase):
    """
    Milvus implementation for vector database.

    Example
    ------

    Initialize the Milvus database client

    >>> config = MilvusConfig(host="localhost", port="19530", run_async=False)
    >>> milvus_db = MilvusVectorDatabase(config=config)
    """

    def _initialize_client(self, **kwargs) -> None:
        """Initialize the Milvus client."""
        config: MilvusConfig = cast(MilvusConfig, self.config)

        # Initialize synchronous and asynchronous clients
        try:
            self.client = MilvusClient(uri=config.uri)
            self.async_client = (
                AsyncMilvusClient(uri=config.uri) if config.run_async else None
            )
        except Exception as e:
            raise MilvusConnectionError(f"Failed to connect to Milvus: {e}") from e

        self.reranker = RRFRanker()
        self.run_async = config.run_async
        self.uri = config.uri

    def _create_schema_and_index(
        self,
        collection_structure: List[SchemaField],
        auto_id: bool = False,
        enable_dynamic_field: bool = False,
        json_index_params: Optional[Dict[str, List[IndexParam]]] = None,
        bm25_function_config: Optional[Dict[str, str]] = None,
    ) -> tuple[CollectionSchema, IndexParams]:
        """
        Create schema and index parameters for a collection.

        Args:
            collection_structure (List[SchemaField]): List of SchemaField objects
                defining the structure of the collection.
            auto_id (bool): Enable auto ID generation for the collection.
            enable_dynamic_field (bool): Enable dynamic field for the collection
                allowing new fields to be added.
            json_index_params (Dict[str, List[IndexParam]]): Index parameters of JSON
                type for the collection. Key is the field name and value is a list of
                IndexParam objects.
            bm25_function_config (Dict[str, str]): BM25 function configuration mapping
                sparse field names to their corresponding text field names.
                Example: {"content_sparse": "content"} creates a BM25 function that
                converts text from "content" field to sparse vector in "content_sparse".

        Returns:
            tuple[CollectionSchema, IndexParams]: Schema and index parameters for the
                collection.
        """
        data_type_mapping = {
            "int": DataType.INT64,
            "string": DataType.VARCHAR,
            "dense_vector": DataType.FLOAT_VECTOR,
            "sparse_vector": DataType.SPARSE_FLOAT_VECTOR,
            "array": DataType.ARRAY,
            "bool": DataType.BOOL,
            "json": DataType.JSON,
            "binary": DataType.BINARY_VECTOR,
            "float": DataType.FLOAT,
        }

        fields = []
        index_params = self.client.prepare_index_params()

        for field in collection_structure:
            if field.field_type.value == "int":
                schema_field = FieldSchema(
                    name=field.field_name,
                    dtype=data_type_mapping[field.field_type.value],
                    description=field.field_description or "",
                    is_primary=field.is_primary,
                )
                # Add index only if explicitly requested
                if field.index_config and field.index_config.index:
                    index_params.add_index(
                        field_name=field.field_name,
                        index_type=IndexType.STL_SORT.value,
                    )
            elif field.field_type.value == "dense_vector":
                if not field.index_config:
                    raise ValueError(
                        f"Index config is required for dense_vector field "
                        f"{field.field_name}"
                    )
                if not field.index_config.index:
                    raise ValueError(
                        f"Index is required for dense_vector field {field.field_name}"
                    )
                if not field.index_config.index_type:
                    raise ValueError(
                        f"Index type is required for dense_vector field "
                        f"{field.field_name}"
                    )
                if not field.index_config.metric_type:
                    raise ValueError(
                        f"Metric type is required for dense_vector field "
                        f"{field.field_name}"
                    )

                schema_field = FieldSchema(
                    name=field.field_name,
                    dtype=data_type_mapping[field.field_type.value],
                    description=field.field_description or "",
                    dim=field.dimension,
                    is_primary=field.is_primary,
                )

                index_type = self.check_index_type(field.index_config.index_type)
                metric_type = self.check_metric_type(field.index_config.metric_type)

                index_params.add_index(
                    field_name=field.field_name,
                    index_type=index_type.value,
                    metric_type=metric_type.value,
                    params={
                        "M": (
                            field.index_config.hnsw_m
                            if field.index_config and field.index_config.hnsw_m
                            else 16
                        ),
                        "efConstruction": (
                            field.index_config.hnsw_ef_construction
                            if field.index_config
                            and field.index_config.hnsw_ef_construction
                            else 500
                        ),
                    },
                )
            elif field.field_type.value == "sparse_vector":
                if not (field.index_config and field.index_config.index):
                    raise ValueError(
                        f"Index is required for sparse_vector field {field.field_name}"
                    )

                schema_field = FieldSchema(
                    name=field.field_name,
                    dtype=data_type_mapping[field.field_type.value],
                    description=field.field_description or "",
                    is_primary=field.is_primary,
                )

                # Determine metric type based on whether this field has BM25 function
                if bm25_function_config and field.field_name in bm25_function_config:
                    metric = MetricType.BM25.value
                else:
                    metric = MetricType.IP.value

                index_params.add_index(
                    field_name=field.field_name,
                    index_type=IndexType.SPARSE_INVERTED_INDEX.value,
                    metric_type=metric,
                    params={"inverted_index_algo": "DAAT_MAXSCORE"},
                )
            elif field.field_type.value == "string":
                analyzer_params = {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                }
                schema_field = FieldSchema(
                    name=field.field_name,
                    dtype=data_type_mapping[field.field_type.value],
                    description=field.field_description or "",
                    max_length=65535,
                    analyzer_params=analyzer_params,
                    enable_analyzer=True,
                    enable_match=True,
                    is_primary=field.is_primary,
                )
                # Add index only if explicitly requested
                if field.index_config and field.index_config.index:
                    index_params.add_index(
                        field_name=field.field_name, index_type=IndexType.INVERTED.value
                    )
            elif field.field_type.value == "array":
                if not field.element_type:
                    raise ValueError(
                        f"Element type is required for array field {field.field_name}"
                    )

                schema_field = FieldSchema(
                    name=field.field_name,
                    dtype=data_type_mapping[field.field_type.value],
                    description=field.field_description or "",
                    element_type=data_type_mapping[field.element_type.value],
                    max_capacity=field.max_capacity or 100,
                    max_length=65535,
                    is_primary=field.is_primary,
                    nullable=True,
                )
                # Add index only if explicitly requested
                if field.index_config and field.index_config.index:
                    index_params.add_index(
                        field_name=field.field_name,
                        index_type=IndexType.AUTOINDEX.value,
                    )
            elif field.field_type.value == "bool":
                schema_field = FieldSchema(
                    name=field.field_name,
                    dtype=data_type_mapping[field.field_type.value],
                    description=field.field_description or "",
                    is_primary=field.is_primary,
                )
                # Add index only if explicitly requested
                if field.index_config and field.index_config.index:
                    index_params.add_index(
                        field_name=field.field_name,
                        index_type=IndexType.AUTOINDEX.value,
                    )
            elif field.field_type.value == "json":
                schema_field = FieldSchema(
                    name=field.field_name,
                    dtype=data_type_mapping[field.field_type.value],
                    description=field.field_description or "",
                    is_primary=field.is_primary,
                )

                # Add index parameters for JSON fields
                if json_index_params and json_index_params.get(field.field_name, None):
                    for _, index_param in enumerate(
                        json_index_params[field.field_name]
                    ):
                        index_params.add_index(
                            field_name=field.field_name,
                            index_type=IndexType.INVERTED.value,
                            index_name=index_param.index_name,
                            params={
                                "json_path": index_param.indexed_key,
                                "json_cast_type": index_param.value_type.value,
                            },
                        )
            elif field.field_type.value == "binary":
                schema_field = FieldSchema(
                    name=field.field_name,
                    dtype=data_type_mapping[field.field_type.value],
                    description=field.field_description or "",
                    dim=field.dimension,
                    is_primary=field.is_primary,
                )
                # Add index only if explicitly requested
                if field.index_config and field.index_config.index:
                    index_params.add_index(
                        field_name=field.field_name,
                        index_type=IndexType.BIN_FLAT.value,
                        metric_type=MetricType.HAMMING.value,
                    )
            else:
                raise ValueError(
                    (
                        "Invalid field type. Please provide one of 'int', 'string', "
                        "'dense_vector', 'sparse_vector', 'array', 'bool', 'json', "
                        "or 'binary'."
                    )
                )

            fields.append(schema_field)

        # Create BM25 functions for sparse fields
        functions = []
        if bm25_function_config:
            for sparse_field_name, text_field_name in bm25_function_config.items():
                functions.append(
                    Function(
                        name=f"bm25_{sparse_field_name}",
                        function_type=FunctionType.BM25,
                        input_field_names=[text_field_name],
                        output_field_names=[sparse_field_name],
                    )
                )

        schema = CollectionSchema(
            fields=fields,
            auto_id=auto_id,
            enable_dynamic_field=enable_dynamic_field,
            functions=functions if functions else None,
        )

        return schema, index_params

    def create_collection(
        self,
        collection_name: str,
        collection_structure: List[SchemaField],
        auto_id: bool = False,
        enable_dynamic_field: bool = False,
        json_index_params: Optional[Dict[str, List[IndexParam]]] = None,
        bm25_function_config: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        """
        Args:
            collection_name (str): Name of the collection to create.
            collection_structure (List[SchemaField]): List of SchemaField objects
                defining the collection structure.
            auto_id (bool): Enable auto ID generation for the collection.
            enable_dynamic_field (bool): Enable dynamic field for the collection
                allowing new fields to be added.
            json_index_params (Dict[str, List[IndexParam]]): Index parameters of JSON
                type for the collection. Key is the field name and value is a list of
                IndexParam objects.
            bm25_function_config (Dict[str, str]): BM25 function configuration mapping
                sparse field names to text field names for full-text search.
        """
        # Check if collection exists
        if self.has_collection(collection_name):
            self.delete_collection(collection_name)

        # Create schema and index parameters
        try:
            schema, index_params = self._create_schema_and_index(
                collection_structure=collection_structure,
                auto_id=auto_id,
                enable_dynamic_field=enable_dynamic_field,
                json_index_params=json_index_params,
                bm25_function_config=bm25_function_config,
            )
        except Exception as e:
            raise CreateMilvusCollectionError(
                f"Error creating collection schema: {str(e)}"
            )

        # Create collection
        self.client.create_collection(  # type: ignore[union-attr]
            collection_name=collection_name, schema=schema, index_params=index_params
        )

        logger.info(f"Collection {collection_name} created successfully!")

    async def async_create_collection(
        self,
        collection_name: str,
        collection_structure: List[SchemaField],
        auto_id: bool = False,
        enable_dynamic_field: bool = False,
        json_index_params: Optional[Dict[str, List[IndexParam]]] = None,
        bm25_function_config: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        """
        Asynchronously create a new collection in the vector database.

        Args:
            collection_name (str): Name of the collection to create.
            collection_structure (List[SchemaField]): List of SchemaField objects
                defining the collection structure.
            auto_id (bool): Enable auto ID generation for the collection.
            enable_dynamic_field (bool): Enable dynamic field for the collection
                allowing new fields to be added.
            json_index_params (Dict[str, List[IndexParam]]): Index parameters of JSON
                type for the collection. Key is the field name and value is a list of
                IndexParam objects.
            bm25_function_config (Dict[str, str]): BM25 function configuration mapping
                sparse field names to text field names for full-text search.
        """
        # Check if collection exists
        if await self.async_has_collection(collection_name):
            await self.async_delete_collection(collection_name)

        # Create schema and index parameters
        try:
            schema, index_params = self._create_schema_and_index(
                collection_structure=collection_structure,
                auto_id=auto_id,
                enable_dynamic_field=enable_dynamic_field,
                json_index_params=json_index_params,
                bm25_function_config=bm25_function_config,
            )
        except Exception as e:
            raise CreateMilvusCollectionError(
                f"Error creating collection schema: {str(e)}"
            )

        # Create collection
        await self.async_client.create_collection(  # type: ignore[union-attr]
            collection_name=collection_name, schema=schema, index_params=index_params
        )

        logger.info(f"Collection {collection_name} created successfully!")

    def load_collection(self, collection_name: str, **kwargs) -> bool:
        """
        Load the collection into memory for faster search operations.

        Args:
            collection_name (str): Name of the collection to load.

        Returns:
            bool: True if the collection is loaded successfully, False otherwise.
        """

        if not self.client.has_collection(collection_name):
            logger.error(f"Collection {collection_name} does not exist!")
            return False

        # Load the collection
        self.client.load_collection(collection_name)  # type: ignore[union-attr]

        # Check if the collection is loaded
        load_state = self.client.get_load_state(collection_name=collection_name)  # type: ignore[union-attr]
        if load_state:
            logger.info(f"Collection {collection_name} is loaded successfully!")
            return True
        else:
            logger.warning(f"Failed to load collection {collection_name}!")
            return False

    async def async_load_collection(self, collection_name: str, **kwargs) -> bool:
        """
        Asynchronously load the collection into memory for faster search operations.

        Args:
            collection_name (str): Name of the collection to load.

        Returns:
            bool: True if the collection is loaded successfully, False otherwise.
        """
        if not self.has_collection(collection_name):
            logger.error(f"Collection {collection_name} does not exist!")
            return False

        # Load the collection
        await self.async_client.load_collection(collection_name)  # type: ignore[union-attr]

        # Check if the collection is loaded
        load_state = self.client.get_load_state(collection_name=collection_name)  # type: ignore[union-attr]
        if load_state:
            logger.info(f"Collection {collection_name} is loaded successfully!")
            return True
        else:
            logger.warning(f"Failed to load collection {collection_name}!")
            return False

    def delete_collection(self, collection_name: str, **kwargs) -> None:
        """Delete a collection from Milvus."""
        self.client.drop_collection(collection_name)  # type: ignore[union-attr]

    async def async_delete_collection(self, collection_name: str, **kwargs) -> None:
        """Asynchronously delete a collection from Milvus."""
        await self.async_client.drop_collection(collection_name)  # type: ignore[union-attr]

    def list_collections(self, **kwargs) -> List[str]:
        """List all collections in Milvus."""
        return self.client.list_collections()  # type: ignore[union-attr]

    async def async_list_collections(self, **kwargs) -> List[str]:
        """Asynchronously list all collections in Milvus."""
        return await asyncio.to_thread(self.list_collections)

    def has_collection(self, collection_name: str, **kwargs) -> bool:
        """Check if a collection exists in Milvus."""
        return self.client.has_collection(collection_name)  # type: ignore[union-attr]

    async def async_has_collection(self, collection_name: str, **kwargs) -> bool:
        """Asynchronously check if a collection exists in Milvus."""
        return await asyncio.to_thread(self.has_collection, collection_name)

    def check_metric_type(self, metric_type: MetricType) -> MetricType:
        """
        Check if the metric type is supported.

        Args:
            metric_type (MetricType): Metric type of the index.

        Returns:
            MetricType: Metric type if supported.

        Raises:
            ValueError: If the metric type is not supported.
        """
        assert isinstance(
            metric_type, MetricType
        ), "metric_type must be an instance of MetricType Enum"

        supported_metric_types = list(MetricType)
        if metric_type not in supported_metric_types:
            raise ValueError(
                f"Invalid metric type. Please provide one of {supported_metric_types}"
            )
        return metric_type

    def check_index_type(self, index_type: IndexType) -> IndexType:
        """
        Check if the index type is supported.

        Args:
            index_type (IndexType): Index type of the index.

        Returns:
            IndexType: Index type if supported.

        Raises:
            ValueError: If the index type is not supported.
        """
        assert isinstance(
            index_type, IndexType
        ), "index_type must be an instance of IndexType Enum"

        supported_index_types = list(IndexType)
        if index_type not in supported_index_types:
            raise ValueError(
                f"Invalid index type. Please provide one of {supported_index_types}"
            )
        return index_type

    def insert_vectors(
        self,
        data: List[Dict],
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Insert vectors into the collection.

        Args:
            collection_name (str): Name of the collection.
            data (List[Dict]): List of dictionaries containing the data to insert.
        """
        if not collection_name:
            raise ValueError("Collection name must be provided for inserting vectors.")

        try:
            self.client.insert(collection_name=collection_name, data=data)  # type: ignore[union-attr]
        except Exception as e:
            raise InsertMilvusVectorsError(f"Error inserting vectors: {str(e)}")

    async def async_insert_vectors(
        self, data: List[Dict], collection_name: Optional[str] = None, **kwargs
    ) -> None:
        """
        Asynchronously insert vectors into the collection.

        Args:
            collection_name (str): Name of the collection.
            data (List[Dict]): List of dictionaries containing the data to insert.

        Raises:
            InsertMilvusVectorsError: If there is an error during insertion.
        """
        if not collection_name:
            raise ValueError("Collection name must be provided for inserting vectors.")

        try:
            await self.async_client.insert(collection_name=collection_name, data=data)  # type: ignore[union-attr]
        except Exception as e:
            raise InsertMilvusVectorsError(f"Error inserting vectors: {str(e)}")

    def get_items(
        self, ids: List[str], collection_name: Optional[str] = None, **kwargs
    ) -> List[dict]:
        """
        Get items from the collection by their IDs.

        Args:
            collection_name (str): Name of the collection.
            ids (List[int]): List of IDs to retrieve.

        Returns:
            List[dict]: List of dictionaries containing the items.
        """
        if not collection_name:
            raise ValueError("Collection name must be provided for getting items.")

        try:
            return self.client.get(collection_name=collection_name, ids=ids)  # type: ignore[union-attr]
        except Exception as e:
            raise GetMilvusItemsError(f"Error getting items: {str(e)}")

    async def async_get_items(
        self, ids: List[str], collection_name: Optional[str] = None, **kwargs
    ) -> List[dict]:
        """
        Asynchronously get items from the collection by their IDs.

        Args:
            collection_name (str): Name of the collection.
            ids (List[int]): List of IDs to retrieve.

        Returns:
            List[dict]: List of dictionaries containing the items.
        """
        if not collection_name:
            raise ValueError("Collection name must be provided for getting items.")

        try:
            result = await self.async_client.get(  # type: ignore[union-attr]
                collection_name=collection_name, ids=ids
            )
            return result
        except Exception as e:
            raise GetMilvusItemsError(f"Error getting items: {str(e)}")

    def build_hybrid_search_requests(
        self,
        embedding_data: List[EmbeddingData],
        top_k: int,
        metric_type: MetricType,
        index_type: IndexType,
    ) -> List[AnnSearchRequest]:
        """
        Build hybrid search requests for the given embedding data.

        Args:
            embedding_data (List[EmbeddingData]): List of EmbeddingData objects
                containing dense or/and sparse data.
            top_k (int): Number of results to return.
            metric_type (MetricType): Metric type for the dense search query.
            index_type (IndexType): Index type for the dense vector ("FLAT",
                "IVF_FLAT", "HNSW").

        Returns:
            List[AnnSearchRequest]: List of AnnSearchRequest objects for hybrid search.
        """
        search_requests = []
        for embedding in embedding_data:
            if not isinstance(embedding, EmbeddingData):
                raise TypeError("Invalid embedding data type. Expected EmbeddingData.")

            embedding_type = embedding.embedding_type
            param: dict = {}
            data: list = []

            # Determine data and params based on embedding type
            if embedding_type == EmbeddingType.SPARSE:
                # For BM25 full-text search with raw text query
                if embedding.query:
                    data = [embedding.query]
                    param = {"drop_ratio_search": 0.2}
                # For manual sparse vector search
                else:
                    data = [embedding.embeddings]
                    param = {"metric_type": MetricType.IP.value, "params": {}}
            elif embedding_type == EmbeddingType.DENSE:
                data = [embedding.embeddings]
                param = {
                    "metric_type": metric_type.value,
                    "params": (
                        {"ef": (top_k * 2)}
                        if index_type == IndexType.HNSW
                        else {"nprobe": 16}
                    ),
                }
            elif embedding_type == EmbeddingType.BINARY:
                data = [embedding.embeddings]
                param = {
                    "metric_type": MetricType.HAMMING.value,
                    "params": {"nprobe": 64},
                }
            else:
                raise ValueError(f"Unsupported embedding type: {embedding_type}")

            if not data or not param:
                continue

            search_params = {
                "data": data,
                "anns_field": embedding.field_name,
                "param": param,
                "limit": (top_k * 2),
                "expr": embedding.filtering_expr,
            }
            search_requests.append(AnnSearchRequest(**search_params))

        return search_requests

    def hybrid_search_vectors(
        self,
        embedding_data: List[EmbeddingData],
        output_fields: List[str],
        top_k: int = 5,
        metric_type: MetricType = MetricType.COSINE,
        index_type: IndexType = IndexType.HNSW,
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> List[dict]:
        """
        Perform hybrid search (in multiple types: dense or sparse or binary) for
        vectors in the collection.

        Args:
            collection_name (str): Name of the collection.
            embedding_data (List[EmbeddingData]): List of EmbeddingData objects
                containing dense or/and sparse data.
            output_fields (List[str]): List of fields to return in the search results.
            top_k (int): Number of results to return.
            metric_type (MetricType): Metric type for the dense search query.
            index_type (IndexType): Index type for dense vector.

        Returns:
            List[dict]: The top-k search result for the input query, containing the
                expected output fields and "_score" key.

        Example
        -------
        >>> embedding_data = [
        >>>     EmbeddingData(embedding_type=EmbeddingType.DENSE,
        >>>                   embeddings=[[0.1, 0.2, 0.3]], field_name="dense_field"),
        >>>     EmbeddingData(embedding_type=EmbeddingType.SPARSE,
        >>>                   embeddings=[[0.0, 1.0, 0.0]], field_name="sparse_field")
        >>> ]
        >>> output_fields = ["id", "name", "dense_field", "sparse_field"]
        >>> results = milvus_db.hybrid_search_vectors(
        >>>     collection_name="my_collection",
        >>>     embedding_data=embedding_data,
        >>>     output_fields=output_fields,
        >>>     top_k=5,
        >>>     metric_type=MetricType.COSINE,
        >>>     index_type=IndexType.HNSW
        >>> )
            [
                {
                    "id": "123",
                    "name": "example_item",
                    "dense_field": [0.1, 0.15, 0.22],
                    "sparse_field": [1.0, 1.0, 0.0],
                    "_score": 0.95
                },
                ...
            ]
        """
        if not collection_name:
            raise ValueError("Collection name must be provided for hybrid search.")

        self.check_index_type(index_type)
        self.check_metric_type(metric_type)

        if not connections.has_connection(alias="default"):
            # If no connection exists, create a new one
            try:
                connections.connect(
                    uri=cast(MilvusConfig, self.config).uri, _async=self.run_async
                )
            except Exception as e:
                raise MilvusConnectionError(
                    f"Failed to connect to Milvus: {str(e)}"
                ) from e

        # Construct the collection
        self.collection = Collection(collection_name)

        try:
            search_requests = self.build_hybrid_search_requests(
                embedding_data=embedding_data,
                top_k=top_k,
                metric_type=metric_type,
                index_type=index_type,
            )
            if not search_requests:
                raise SearchMilvusVectorsError(
                    "No valid search requests were created. "
                    "Check the input embedding data."
                )

            results = self.client.hybrid_search(  # type: ignore[union-attr]
                collection_name=collection_name,
                reqs=search_requests,
                ranker=self.reranker,
                limit=top_k,
                output_fields=output_fields,
                **kwargs,
            )

            if not results:
                return []

            # Flatten the structure by moving entity fields to top level
            flattened_results = []
            for result in results[0]:
                flattened_result = {}

                # Copy non-entity fields (like distance, id, etc.)
                for key, value in result.items():
                    if key != "entity":
                        if key == "distance":
                            flattened_result["_score"] = value
                        else:
                            flattened_result[key] = value

                # Move entity fields to top level
                if "entity" in result:
                    for entity_key, entity_value in result["entity"].items():
                        flattened_result[entity_key] = entity_value

                flattened_results.append(flattened_result)

            return flattened_results
        except Exception as e:
            logger.error(traceback.format_exc())
            raise SearchMilvusVectorsError(f"Error in hybrid search: {str(e)}")

    async def async_hybrid_search_vectors(
        self,
        embedding_data: List[EmbeddingData],
        output_fields: List[str],
        top_k: int = 5,
        metric_type: MetricType = MetricType.COSINE,
        index_type: IndexType = IndexType.HNSW,
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> List[dict]:
        """
        Asynchronously perform hybrid search (in multiple types: dense or sparse or
        binary) for vectors in the collection.

        Args:
            collection_name (str): Name of the collection.
            embedding_data (List[EmbeddingData]): List of EmbeddingData objects
                containing dense or/and sparse data.
            output_fields (List[str]): List of fields to return in the search results.
            top_k (int): Number of results to return.
            metric_type (MetricType): Metric type for the dense search query.
            index_type (IndexType): Index type for dense vector.

        Returns:
            List[dict]: The top-k search result for the input query, containing the
                expected output fields and "_score" key.

        Example
        -------
        >>> embedding_data = [
        >>>     EmbeddingData(embedding_type=EmbeddingType.DENSE,
        >>>                   embeddings=[[0.1, 0.2, 0.3]], field_name="dense_field"),
        >>>     EmbeddingData(embedding_type=EmbeddingType.SPARSE,
        >>>                   embeddings=[[0.0, 1.0, 0.0]], field_name="sparse_field")
        >>> ]
        >>> output_fields = ["id", "name", "dense_field", "sparse_field"]
        >>> results = milvus_db.hybrid_search_vectors(
        >>>     collection_name="my_collection",
        >>>     embedding_data=embedding_data,
        >>>     output_fields=output_fields,
        >>>     top_k=5,
        >>>     metric_type=MetricType.COSINE,
        >>>     index_type=IndexType.HNSW
        >>> )
            [
                {
                    "id": "123",
                    "name": "example_item",
                    "dense_field": [0.1, 0.15, 0.22],
                    "sparse_field": [1.0, 1.0, 0.0],
                    "_score": 0.95
                },
                ...
            ]
        """
        if not collection_name:
            raise ValueError("Collection name must be provided for hybrid search.")

        self.check_index_type(index_type)
        self.check_metric_type(metric_type)

        if not connections.has_connection(alias="default"):
            # If no connection exists, create a new one
            try:
                connections.connect(
                    uri=cast(MilvusConfig, self.config).uri, _async=self.run_async
                )
            except Exception as e:
                raise MilvusConnectionError(
                    f"Failed to connect to Milvus: {str(e)}"
                ) from e

        # Construct the collection
        self.collection = Collection(collection_name)

        try:
            search_requests = self.build_hybrid_search_requests(
                embedding_data=embedding_data,
                top_k=top_k,
                metric_type=metric_type,
                index_type=index_type,
            )
            if not search_requests:
                raise SearchMilvusVectorsError(
                    "No valid search requests were created. "
                    "Check the input embedding data."
                )

            results = await self.async_client.hybrid_search(  # type: ignore[union-attr]
                collection_name=collection_name,
                reqs=search_requests,
                ranker=self.reranker,
                limit=top_k,
                output_fields=output_fields,
                **kwargs,
            )

            if not results:
                return []

            return results[0]
        except Exception as e:
            logger.error(traceback.format_exc())
            raise SearchMilvusVectorsError(f"Error in hybrid search: {str(e)}")

    def search_dense_vectors(
        self,
        query_embeddings: List[List],
        field_name: str,
        output_fields: List[str],
        filtering_expr: str = "",
        top_k: int = 5,
        metric_type: MetricType = MetricType.COSINE,
        index_type: IndexType = IndexType.HNSW,
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> List[List[dict]]:
        """
        Search for dense vectors in the collection in Milvus database.

        Args:
            collection_name (str): Name of the collection.
            query_embeddings (List[List]): List of query embeddings.
            field_name (str): Field name to search.
            output_fields (List[str]): List of fields to return in the search results.
            filtering_expr (str): Filtering expression for the search query.
            top_k (int): Number of results to return.
            metric_type (MetricType): Metric type for the search query.
            index_type (IndexType): Index type for dense vector ("FLAT", "IVF_FLAT",
                "HNSW").

        Returns:
            List[List[dict]]: List of top-k search results of each input query
                embedding. The number of lists in the output is equal to the number
                of query embeddings. The output contains the expected output fields
                and "_score" key.
        """
        if not collection_name:
            raise ValueError(
                "Collection name must be provided for searching dense vectors."
            )

        self.check_index_type(index_type)
        self.check_metric_type(metric_type)

        if not connections.has_connection(alias="default"):
            # If no connection exists, create a new one
            try:
                connections.connect(
                    uri=cast(MilvusConfig, self.config).uri, _async=self.run_async
                )
            except Exception as e:
                raise MilvusConnectionError(
                    f"Failed to connect to Milvus: {str(e)}"
                ) from e

        # Construct the collection
        self.collection = Collection(collection_name)

        try:
            results = self.client.search(  # type: ignore[union-attr]
                collection_name=collection_name,
                data=query_embeddings,
                anns_field=field_name,
                limit=top_k,
                output_fields=output_fields,
                search_params={
                    "metric_type": metric_type.value,
                    "params": (
                        {"ef": top_k} if index_type == IndexType.HNSW else {"nprobe": 8}
                    ),
                },
                filter=filtering_expr,
                **kwargs,
            )

            # Flatten the structure for each query result
            flattened_results = []
            for query_result in results:
                flattened_query_result = []
                for result in query_result:
                    flattened_result = {}

                    # Copy non-entity fields (like distance, id, etc.)
                    for key, value in result.items():
                        if key != "entity":
                            if key == "distance":
                                flattened_result["_score"] = value
                            else:
                                flattened_result[key] = value

                    # Move entity fields to top level
                    if "entity" in result:
                        for entity_key, entity_value in result["entity"].items():
                            flattened_result[entity_key] = entity_value

                    flattened_query_result.append(flattened_result)

                flattened_results.append(flattened_query_result)

            return flattened_results
        except Exception as e:
            logger.error(traceback.format_exc())
            raise SearchMilvusVectorsError(
                f"Error in searching dense vectors: {str(e)}"
            )

    async def async_search_dense_vectors(
        self,
        query_embeddings: List[List],
        field_name: str,
        output_fields: List[str],
        filtering_expr: str = "",
        top_k: int = 5,
        metric_type: MetricType = MetricType.COSINE,
        index_type: IndexType = IndexType.HNSW,
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> List[List[dict]]:
        """
        Asynchronously search for dense vectors in the collection in Milvus database.

        Args:
            collection_name (str): Name of the collection.
            query_embeddings (List[List]): List of query embeddings.
            field_name (str): Field name to search.
            output_fields (List[str]): List of fields to return in the search results.
            filtering_expr (str): Filtering expression for the search query.
            top_k (int): Number of results to return.
            metric_type (MetricType): Metric type for the search query.
            index_type (IndexType): Index type for dense vector ("FLAT", "IVF_FLAT",
                "HNSW").

        Returns:
            List[List[dict]]: List of top-k search results of each input query
                embedding. The number of lists in the output is equal to the number
                of query embeddings. The output contains the expected output fields
                and "_score" key.
        """
        if not collection_name:
            raise ValueError(
                "Collection name must be provided for searching dense vectors."
            )

        self.check_index_type(index_type)
        self.check_metric_type(metric_type)

        if not connections.has_connection(alias="default"):
            # If no connection exists, create a new one
            try:
                connections.connect(
                    uri=cast(MilvusConfig, self.config).uri, _async=self.run_async
                )
            except Exception as e:
                raise MilvusConnectionError(
                    f"Failed to connect to Milvus: {str(e)}"
                ) from e

        # Construct the collection
        self.collection = Collection(collection_name)

        try:
            results = await self.async_client.search(  # type: ignore[union-attr]
                collection_name=collection_name,
                data=query_embeddings,
                anns_field=field_name,
                limit=top_k,
                output_fields=output_fields,
                search_params={
                    "metric_type": metric_type.value,
                    "params": (
                        {"ef": top_k} if index_type == IndexType.HNSW else {"nprobe": 8}
                    ),
                },
                filter=filtering_expr,
                **kwargs,
            )

            # Flatten the structure for each query result
            flattened_results = []
            for query_result in results:
                flattened_query_result = []
                for result in query_result:
                    flattened_result = {}

                    # Copy non-entity fields (like distance, id, etc.)
                    for key, value in result.items():
                        if key != "entity":
                            if key == "distance":
                                flattened_result["_score"] = value
                            else:
                                flattened_result[key] = value

                    # Move entity fields to top level
                    if "entity" in result:
                        for entity_key, entity_value in result["entity"].items():
                            flattened_result[entity_key] = entity_value

                    flattened_query_result.append(flattened_result)

                flattened_results.append(flattened_query_result)

            return flattened_results
        except Exception as e:
            logger.error(traceback.format_exc())
            raise SearchMilvusVectorsError(
                f"Error in searching dense vectors: {str(e)}"
            )
