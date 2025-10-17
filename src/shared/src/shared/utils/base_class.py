from typing import Dict, List

import numpy as np
from pydantic import BaseModel
from scipy.sparse import csr_array


# ----------------- API Classes -----------------

class Payload(BaseModel):
    """Class to store payload data for the API."""

    actor: str
    input: Dict[str, str]


# ----------------- Embedding Types -----------------

DenseEmbedding = List[float]    # Type alias for embedding vectors
BinaryEmbedding = np.ndarray    # Type alias for binary embeddings (0s and 1s)
SparseEmbedding = csr_array     # Type alias for sparse embeddings