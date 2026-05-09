#!/usr/bin/env bash
#
# Prepare the isolated HippoRAG environment used by the BrandMind benchmark.
# The main BrandMind project stays on its Python 3.12 uv workspace; HippoRAG
# runs in Python 3.10 because that is the runtime recommended by upstream.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${HIPPO_RAG_CONDA_ENV:-brandmind-hipporag}"
HIPPO_ROOT="${PROJECT_ROOT}/.codex/benchmarks/hipporag"
HIPPO_REPO="${HIPPO_ROOT}/HippoRAG"
HIPPO_URL="https://github.com/OSU-NLP-Group/HippoRAG.git"

create_conda_env() {
    if conda env list | awk "{print \$1}" | grep -qx "${ENV_NAME}"; then
        echo "Conda environment already exists: ${ENV_NAME}"
        return
    fi

    conda create -y -n "${ENV_NAME}" python=3.10 pip
}

install_runtime_dependencies() {
    conda run -n "${ENV_NAME}" python -m pip install "litellm==1.83.14"

    mkdir -p "${HIPPO_ROOT}"
    if [ ! -d "${HIPPO_REPO}/.git" ]; then
        git clone --depth 1 "${HIPPO_URL}" "${HIPPO_REPO}"
    else
        echo "HippoRAG repository already exists: ${HIPPO_REPO}"
    fi

    conda run -n "${ENV_NAME}" python -m pip install -e "${HIPPO_REPO}" --no-deps

    conda run -n "${ENV_NAME}" python -m pip install \
        "numpy" \
        "scipy" \
        "pandas" \
        "pyarrow" \
        "tqdm" \
        "networkx==3.4.2" \
        "python_igraph==0.11.8" \
        "tenacity==8.5.0" \
        "tiktoken==0.12.0" \
        "boto3" \
        "filelock" \
        "packaging" \
        "einops" \
        "torch==2.5.1" \
        "transformers==4.45.2"
}

apply_vendor_patch() {
    local embedding_init="${HIPPO_REPO}/src/hipporag/embedding_model/__init__.py"
    local hipporag_main="${HIPPO_REPO}/src/hipporag/HippoRAG.py"

    if grep -q "gemini-embedding" "${embedding_init}" && \
       ! grep -q "^from \\.information_extraction\\.openie_vllm_offline" "${hipporag_main}";
    then
        echo "Vendor patch appears to be present."
        return
    fi

    python - "${embedding_init}" "${hipporag_main}" <<'PY'
from pathlib import Path
import sys

embedding_init = Path(sys.argv[1])
hipporag_main = Path(sys.argv[2])

embedding_init.write_text(
    '''from .base import EmbeddingConfig, BaseEmbeddingModel
from .OpenAI import OpenAIEmbeddingModel

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def _get_embedding_model_class(embedding_model_name: str = "nvidia/NV-Embed-v2"):
    """Return the embedding implementation without importing unused heavy backends."""
    if "GritLM" in embedding_model_name:
        from .GritLM import GritLMEmbeddingModel

        return GritLMEmbeddingModel
    elif "NV-Embed-v2" in embedding_model_name:
        from .NVEmbedV2 import NVEmbedV2EmbeddingModel

        return NVEmbedV2EmbeddingModel
    elif "contriever" in embedding_model_name:
        from .Contriever import ContrieverModel

        return ContrieverModel
    elif "text-embedding" in embedding_model_name or "gemini-embedding" in embedding_model_name:
        return OpenAIEmbeddingModel
    elif "cohere" in embedding_model_name:
        from .Cohere import CohereEmbeddingModel

        return CohereEmbeddingModel
    elif embedding_model_name.startswith("Transformers/"):
        from .Transformers import TransformersEmbeddingModel

        return TransformersEmbeddingModel
    elif embedding_model_name.startswith("VLLM/"):
        from .VLLM import VLLMEmbeddingModel

        return VLLMEmbeddingModel
    assert False, f"Unknown embedding model name: {embedding_model_name}"
''',
    encoding="utf-8",
)

text = hipporag_main.read_text(encoding="utf-8")
text = text.replace(
    "from .information_extraction.openie_vllm_offline import VLLMOfflineOpenIE\n"
    "from .information_extraction.openie_transformers_offline import TransformersOfflineOpenIE\n",
    "",
)
text = text.replace(
    "        elif self.global_config.openie_mode == 'offline':\n"
    "            self.openie = VLLMOfflineOpenIE(self.global_config)\n"
    "        elif self.global_config.openie_mode ==  'Transformers-offline':\n"
    "            self.openie = TransformersOfflineOpenIE(self.global_config)\n",
    "        elif self.global_config.openie_mode == 'offline':\n"
    "            from .information_extraction.openie_vllm_offline import VLLMOfflineOpenIE\n\n"
    "            self.openie = VLLMOfflineOpenIE(self.global_config)\n"
    "        elif self.global_config.openie_mode ==  'Transformers-offline':\n"
    "            from .information_extraction.openie_transformers_offline import TransformersOfflineOpenIE\n\n"
    "            self.openie = TransformersOfflineOpenIE(self.global_config)\n",
)
hipporag_main.write_text(text, encoding="utf-8")
PY
}

verify_environment() {
    conda run -n "${ENV_NAME}" python - <<'PY'
import importlib.metadata as metadata
from hipporag import HippoRAG

print("hipporag_import_ok", HippoRAG.__name__)
print("litellm_version", metadata.version("litellm"))
PY
}

main() {
    cd "${PROJECT_ROOT}"
    create_conda_env
    install_runtime_dependencies
    apply_vendor_patch
    verify_environment
}

main "$@"
