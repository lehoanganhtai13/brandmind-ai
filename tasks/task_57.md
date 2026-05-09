# Task 57: HippoRAG Benchmark Foundation

## Metadata

- **Epic**: Marketing KG Evaluation — HippoRAG comparison
- **Priority**: High
- **Status**: Implemented
- **Estimated Effort**: 2-3 days for foundation; later tasks cover dataset curation and full runs
- **Team**: Backend / Evaluation
- **Related Tasks**: `evaluation/kg_tools_search_baseline_comparison.py`, shared memory HippoRAG status
- **Blocking**: Five-book HippoRAG vs BrandMind benchmark run
- **Blocked by**: None for the foundation slice

### Progress Checklist

> Agent: Update checkboxes as each section is completed. Do not mark a section done until it is
> fully verified.

- [x] Agent Protocol — Read and confirmed from `tasks/task_template.md`
- [x] Context & Goals — Problem definition and success metrics
- [x] Solution Design — Architecture and technical approach
- [x] Pre-Implementation Research — Findings logged before coding
- [x] Implementation Plan — Phased execution plan drafted
- [x] Implementation Detail — Full ready-to-apply code reviewed by user before file writes
    - [x] Component 1 — Reproducible HippoRAG environment setup
    - [x] Component 2 — LiteLLM/Gemini embedding dimension adapter
    - [x] Component 3 — Five-book corpus exporter
    - [x] Component 4 — Unit tests for adapter and exporter
- [x] Test Execution Log — All tests run and results recorded
- [x] Decision Log — Key decisions documented
- [x] Task Summary — Final implementation summary completed

## Reference Documentation

- **Coding Standards**: `tasks/task_template.md`, Rule 4 and Rule 2.5.
- **Existing benchmark pattern**: `evaluation/kg_tools_search_baseline_comparison.py`.
- **Existing question sets**: `evaluation/test_questions.py` and
  `evaluation/test_questions_extended.py`.
- **Source corpus**: `data/parsed_documents/*/chunks.json`.
- **HippoRAG upstream**: `.codex/benchmarks/hipporag/HippoRAG/README.md`,
  `.codex/benchmarks/hipporag/HippoRAG/setup.py`,
  `.codex/benchmarks/hipporag/HippoRAG/src/hipporag/embedding_model/OpenAI.py`.
- **Memory checkpoint**:
  `/Users/lehoanganhtai/shared-agent-memory/wiki/projects/brandmind-ai.md`,
  section `HippoRAG Benchmark Status — added 2026-05-09`.

------------------------------------------------------------------------

## Agent Protocol

This task follows `tasks/task_template.md`:

1. Research before writing implementation code.
2. Stop and ask if requirements conflict.
3. Fill Implementation Detail with full ready-to-apply code before project files are written.
4. Use production-grade Python: module/class/function docstrings, type hints, double quotes,
   English-only code comments, and focused modules.
5. Do not print, store, or commit secrets.

------------------------------------------------------------------------

## Context & Goals

### Context

BrandMind already has a historical benchmark comparing the current Deep Agent against a hybrid
RAG baseline. The user now wants an analogous, more rigorous benchmark against HippoRAG over the
five-book marketing KG corpus. The first implementation slice must make the HippoRAG runtime
reproducible, force Gemini embedding dimensionality to `1536` for fairness with BrandMind, and
export the five existing `chunks.json` files into HippoRAG's custom corpus format.

### Goal

Create the foundation needed to run HippoRAG against the same five-book corpus as BrandMind,
without changing BrandMind's existing Milvus/FalkorDB services and without allowing HippoRAG
dependencies to downgrade LiteLLM below `1.83.14`.

### Success Metrics / Acceptance Criteria

- **Runtime**: `conda run -n brandmind-hipporag python -c "from hipporag import HippoRAG"`
  succeeds after running the setup script.
- **Security constraint**: `litellm==1.83.14` remains installed in `brandmind-hipporag`.
- **Fairness**: HippoRAG embedding calls to `gemini-embedding-001` pass `dimensions=1536`.
- **Corpus export**: Exporter writes HippoRAG corpus JSON with exactly 3,185 records from the
  five canonical books, excluding `test_sample_stage4`.
- **Traceability**: Metadata sidecar maps every exported record to stable
  `book_slug::chunk_id`, pages, source, original document, author, and section summary.
- **Tests**: Unit tests cover dimension patching and corpus export behavior without live API calls.

------------------------------------------------------------------------

## Solution Design

### Proposed Approach

**Project-owned wrapper around an ignored HippoRAG vendor clone.** Keep the experimental HippoRAG
source under ignored `.codex/`, but place reproducible setup, adapter, exporter, and tests in
tracked project files. This avoids contaminating the main project dependency graph while preserving
enough setup knowledge for another agent to reproduce the benchmark.

### Technology Stack

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| Conda Python 3.10 | HippoRAG runtime | Upstream HippoRAG README recommends Python 3.10 |
| LiteLLM `1.83.14` | OpenAI-compatible Gemini proxy | User-required patched version |
| HippoRAG editable `--no-deps` install | Graph/text RAG baseline | Avoids upstream dependency downgrades |
| OpenAI-compatible `/v1` API | LLM and embedding bridge | HippoRAG supports OpenAI-compatible base URLs |
| Project exporter module | Five-book corpus conversion | Keeps corpus IDs and metadata stable |
| Pytest unit tests | Adapter/exporter validation | Avoids live API calls for CI-safe checks |

### Architecture Overview

```text
data/parsed_documents/*/chunks.json
    |
    | export_hipporag_corpus.py
    v
.codex/benchmarks/hipporag/corpus/marketing_5books_corpus.json
.codex/benchmarks/hipporag/corpus/marketing_5books_metadata.json
    |
    | brandmind-hipporag conda env
    | install_humane_hipporag_patch()
    v
HippoRAG(save_dir=.codex/benchmarks/hipporag/index, ...)
    |
    | LiteLLM http://localhost:4000/v1
    v
gemini-2.5-flash-lite + gemini-embedding-001(dimensions=1536)
```

### Issues & Solutions

1. **HippoRAG pins old LiteLLM** -> install HippoRAG editable with `--no-deps`, then install only
   the minimum dependencies needed for the online OpenAI-compatible path.
2. **HippoRAG upstream does not pass `dimensions` to embeddings** -> project adapter monkeypatches
   `OpenAIEmbeddingModel.encode()` at runtime to include `dimensions=1536`.
3. **HippoRAG imports unused heavy backends eagerly** -> setup script applies the small ignored
   vendor patch that makes unused embedding backends lazy-loaded.
4. **Five-book source traceability** -> exporter uses `book_slug::chunk_id` as both the HippoRAG
   passage title and metadata key.

------------------------------------------------------------------------

## Pre-Implementation Research

### Codebase Audit

- **Files read**:
  - `evaluation/kg_tools_search_baseline_comparison.py`
  - `evaluation/test_questions.py`
  - `evaluation/test_questions_extended.py`
  - `tasks/task_template.md`
  - `pyproject.toml`
  - `data/parsed_documents/*/chunks.json`
  - `/Users/lehoanganhtai/shared-agent-memory/wiki/projects/brandmind-ai.md`
- **Relevant patterns found**:
  - Existing benchmark code is monolithic and useful as a behavior reference, but the HippoRAG
    work should be modular under `evaluation/hipporag_comparison/`.
  - Existing parsed chunks have `chunk_id`, `content`, and metadata keys: `author`,
    `original_document`, `pages`, `section_summary`, `source`, `word_count`.
  - Canonical five-book chunk counts are 224, 439, 1,385, 162, and 975, totaling 3,185.
- **Potential conflicts**:
  - Main project uses Python `>=3.12`; HippoRAG upstream recommends Python 3.10. Use a separate
    conda env.
  - Main BrandMind embedding dim is `1536`; LiteLLM default for `gemini-embedding-001` remains
    `3072` unless `dimensions=1536` is supplied.

### External Library / API Research

- **Library/API**: HippoRAG 2 upstream.
- **Documentation source**:
  - `.codex/benchmarks/hipporag/HippoRAG/README.md`
  - `.codex/benchmarks/hipporag/HippoRAG/setup.py`
  - `.codex/benchmarks/hipporag/HippoRAG/src/hipporag/embedding_model/OpenAI.py`
- **Key findings**:
  - Upstream install command is `conda create -n hipporag python=3.10` followed by
    `pip install hipporag`.
  - Upstream custom corpus format is a JSON array of records with `title`, `text`, and `idx`.
  - OpenAI-compatible LLM and embedding endpoints can be passed as `llm_base_url` and
    `embedding_base_url`.
  - Vector database integration is a TODO upstream; no extra Milvus/Qdrant/Neo4j service is
    required for native HippoRAG.
  - Upstream `OpenAIEmbeddingModel.encode()` calls
    `self.client.embeddings.create(input=texts, model=self.embedding_model_name)` and therefore
    does not pass `dimensions`.
- **Interface confirmed**:
  - `HippoRAG(global_config=BaseConfig(...))`
  - `BaseConfig(llm_name=..., llm_base_url=..., embedding_model_name=..., embedding_base_url=...)`
  - `OpenAIEmbeddingModel.encode(self, texts: list[str])`

### Unknown / Risks Identified

- [x] Whether LiteLLM supports `dimensions=1536` for `gemini-embedding-001`: verified yes.
- [x] Whether default LiteLLM embedding dim changed after user update: verified no, still `3072`.
- [x] Whether HippoRAG path can use LiteLLM: verified with LLM smoke, embedding smoke, and tiny
  end-to-end index/retrieve.
- [x] Whether the five-book export is stable at 3,185 chunks: verified by running the exporter.
- [ ] Whether the full HippoRAG five-book index build is stable after OpenIE and retrieval runner
  implementation: deferred to the next benchmark phase.

### Research Status

- [x] All referenced documentation read
- [x] Existing codebase patterns understood
- [x] External dependencies verified
- [x] No unresolved ambiguities remain for this foundation slice

------------------------------------------------------------------------

## Implementation Plan

### Phase 1: Reproducible setup and adapter

1. Create `scripts/setup_hipporag_env.sh`.
   - Create/reuse conda env `brandmind-hipporag` with Python 3.10.
   - Install `litellm==1.83.14`.
   - Clone HippoRAG into `.codex/benchmarks/hipporag/HippoRAG` if missing.
   - Install HippoRAG editable with `--no-deps`.
   - Install minimum online-path dependencies.
   - Apply ignored vendor lazy-import patch.
   - Verify import and LiteLLM version.
2. Create `evaluation/hipporag_comparison/hipporag_litellm.py`.
   - Runtime patch for `OpenAIEmbeddingModel.encode()` to pass `dimensions=1536`.
   - Factory for HippoRAG `BaseConfig`.
   - No secrets are read or printed.

### Phase 2: Corpus exporter

1. Create `evaluation/hipporag_comparison/export_corpus.py`.
   - Read five canonical `chunks.json` files.
   - Write HippoRAG corpus JSON list: `title`, `text`, `idx`.
   - Write metadata sidecar with stable source IDs and chunk metadata.
2. Add unit tests for exporter.

### Phase 3: Verification

1. Run unit tests:
   - `uv run pytest tests/unit/test_hipporag_comparison.py -q`
2. Run setup verification:
   - `bash scripts/setup_hipporag_env.sh`
3. Run a smoke embedding call in `brandmind-hipporag` and confirm `1536`.

### Rollback Plan

Remove the new files:

- `scripts/setup_hipporag_env.sh`
- `evaluation/hipporag_comparison/`
- `tests/unit/test_hipporag_comparison.py`

No existing BrandMind runtime, Milvus collection, or FalkorDB graph is modified by this task.

------------------------------------------------------------------------

## Implementation Detail

> This section was the pre-apply review surface. The user approved it, and the implementation has
> now been applied. The final tracked code is the source of truth where it differs from the
> originally reviewed snippets.

### Component 1: Reproducible HippoRAG environment setup

> Status: Implemented in `scripts/setup_hipporag_env.sh`.

#### Requirement 1 — Setup script

- **Requirement**: Provide a reproducible setup script that creates the isolated HippoRAG conda
  environment without downgrading LiteLLM below `1.83.14`.

- **Implementation**:

Target file: `scripts/setup_hipporag_env.sh` `[NEW]`

```bash
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
       ! grep -q "^from \\.information_extraction\\.openie_vllm_offline import VLLMOfflineOpenIE" "${hipporag_main}"; then
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
```

### Component 2: LiteLLM/Gemini embedding dimension adapter

> Status: Implemented in `evaluation/hipporag_comparison/hipporag_litellm.py`.

#### Requirement 2 — Runtime adapter

- **Requirement**: Patch HippoRAG's OpenAI-compatible embedding class at runtime so calls to
  `gemini-embedding-001` include `dimensions=1536`.

- **Implementation**:

Target file: `evaluation/hipporag_comparison/__init__.py` `[NEW]`

```python
"""Utilities for the HippoRAG comparison benchmark."""
```

Target file: `evaluation/hipporag_comparison/hipporag_litellm.py` `[NEW]`

```python
"""LiteLLM integration helpers for running HippoRAG in BrandMind benchmarks.

The benchmark runs HippoRAG in a separate Python 3.10 conda environment while
BrandMind remains in its Python 3.12 uv workspace. HippoRAG can speak to any
OpenAI-compatible endpoint, so the local LiteLLM proxy is the bridge to Gemini
LLM and embedding models.

Business context:
    BrandMind uses 1536-dimensional Gemini embeddings in its Milvus/FalkorDB
    retrieval stack. LiteLLM returns 3072 dimensions for ``gemini-embedding-001``
    unless the OpenAI-compatible ``dimensions`` parameter is supplied. This
    module patches HippoRAG's OpenAI-compatible embedding adapter so HippoRAG and
    BrandMind are compared with the same embedding dimensionality.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np
from pydantic import BaseModel, Field

DEFAULT_LITELLM_BASE_URL = "http://localhost:4000/v1"
DEFAULT_LLM_MODEL = "gemini-2.5-flash-lite"
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_EMBEDDING_DIMENSIONS = 1536


class EmbeddingResponseItem(Protocol):
    """Protocol for one OpenAI-compatible embedding response item."""

    embedding: list[float]


class EmbeddingResponse(Protocol):
    """Protocol for an OpenAI-compatible embedding response."""

    data: list[EmbeddingResponseItem]


class EmbeddingsClient(Protocol):
    """Protocol for an OpenAI-compatible embeddings client."""

    def create(
        self,
        *,
        input: list[str],
        model: str,
        dimensions: int,
    ) -> EmbeddingResponse:
        """Create embeddings for a batch of texts."""


class OpenAIClient(Protocol):
    """Protocol for the OpenAI client object owned by HippoRAG."""

    embeddings: EmbeddingsClient


class HippoRagOpenAIEmbeddingModel(Protocol):
    """Structural type for HippoRAG's OpenAI embedding model instances."""

    client: OpenAIClient
    embedding_model_name: str


class HippoRagLiteLLMConfig(BaseModel):
    """Configuration for the BrandMind HippoRAG LiteLLM bridge.

    Args:
        save_dir: Directory where HippoRAG stores indexes, OpenIE results, and
            local parquet embedding stores.
        llm_base_url: OpenAI-compatible LiteLLM base URL.
        embedding_base_url: OpenAI-compatible LiteLLM embedding base URL.
        llm_model_name: Gemini chat model exposed by LiteLLM.
        embedding_model_name: Gemini embedding model exposed by LiteLLM.
        embedding_dimensions: Embedding dimensionality used for fair comparison
            with BrandMind's retrieval stack.
        embedding_batch_size: Batch size used by HippoRAG embedding stores.
    """

    save_dir: str
    llm_base_url: str = DEFAULT_LITELLM_BASE_URL
    embedding_base_url: str = DEFAULT_LITELLM_BASE_URL
    llm_model_name: str = DEFAULT_LLM_MODEL
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL
    embedding_dimensions: int = Field(default=DEFAULT_EMBEDDING_DIMENSIONS, gt=0)
    embedding_batch_size: int = Field(default=16, gt=0)


def install_gemini_embedding_dimension_patch(
    embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
) -> None:
    """Patch HippoRAG's OpenAI embedding adapter to pass Gemini dimensions.

    Args:
        embedding_dimensions: The OpenAI-compatible ``dimensions`` value to send
            to LiteLLM for ``gemini-embedding-001`` calls.

    Raises:
        ValueError: If ``embedding_dimensions`` is not positive.
    """

    if embedding_dimensions <= 0:
        raise ValueError("embedding_dimensions must be a positive integer.")

    from hipporag.embedding_model.OpenAI import OpenAIEmbeddingModel

    def encode_with_dimensions(
        self: HippoRagOpenAIEmbeddingModel,
        texts: list[str],
    ) -> np.ndarray:
        """Encode texts with the configured Gemini embedding dimensionality."""

        sanitized_texts = [text.replace("\n", " ") if text else " " for text in texts]
        response = self.client.embeddings.create(
            input=sanitized_texts,
            model=self.embedding_model_name,
            dimensions=embedding_dimensions,
        )
        return np.array([item.embedding for item in response.data])

    OpenAIEmbeddingModel.encode = encode_with_dimensions


def build_hipporag_config(config: HippoRagLiteLLMConfig):
    """Build a HippoRAG ``BaseConfig`` for the local LiteLLM proxy.

    Args:
        config: Bridge configuration with model names, base URLs, save path, and
            embedding settings.

    Returns:
        A HippoRAG ``BaseConfig`` instance. The return type is intentionally not
        imported at module import time because this module may be imported from
        the BrandMind Python 3.12 environment where HippoRAG is not installed.
    """

    from hipporag.utils.config_utils import BaseConfig

    return BaseConfig(
        save_dir=config.save_dir,
        llm_name=config.llm_model_name,
        llm_base_url=config.llm_base_url,
        embedding_model_name=config.embedding_model_name,
        embedding_base_url=config.embedding_base_url,
        embedding_batch_size=config.embedding_batch_size,
    )


def build_hipporag(config: HippoRagLiteLLMConfig):
    """Create a HippoRAG instance configured for BrandMind's LiteLLM proxy.

    Args:
        config: Bridge configuration.

    Returns:
        A configured HippoRAG instance ready for indexing or retrieval.
    """

    install_gemini_embedding_dimension_patch(config.embedding_dimensions)

    from hipporag import HippoRAG

    return HippoRAG(global_config=build_hipporag_config(config))
```

### Component 3: Five-book corpus exporter

> Status: Implemented in `evaluation/hipporag_comparison/export_corpus.py`.

#### Requirement 3 — Export parsed chunks to HippoRAG corpus format

- **Requirement**: Convert the five canonical `chunks.json` files into HippoRAG's custom corpus
  JSON format and a metadata sidecar for source-grounded benchmark traceability.

- **Implementation**:

Target file: `evaluation/hipporag_comparison/export_corpus.py` `[NEW]`

```python
"""Export BrandMind parsed book chunks into HippoRAG custom corpus format.

HippoRAG custom corpora use a JSON array of objects with ``title``, ``text``,
and ``idx`` fields. BrandMind needs more source traceability than HippoRAG's
minimal format, so this exporter writes two files:

1. A HippoRAG corpus JSON file for indexing.
2. A metadata sidecar keyed by the same stable source IDs.

Business context:
    The benchmark must compare BrandMind and HippoRAG on the same five marketing
    books. Stable source IDs are required so QA and retrieval metrics can report
    whether a system found the supporting source chunks, not just whether the
    final answer sounded correct.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

CANONICAL_BOOK_DIRS = (
    "How_Brands_Grow_What_Marketers_Dont_Know_20260206_171611",
    "Influence_New_and_Expanded_The_Psychology_of_Persuasion_20260206_172109",
    "Kotler_and_Armstrong_Principles_of_Marketing_20251123_193123",
    "Positioning_The_Battle_for_Your_Mind_20260206_170800",
    "Strategic_Brand_Management_20260206_164738",
)


@dataclass(frozen=True)
class HippoRagCorpusRecord:
    """One passage in HippoRAG custom corpus format."""

    title: str
    text: str
    idx: int


@dataclass(frozen=True)
class SourceMetadata:
    """Traceability metadata for one exported BrandMind chunk.

    Args:
        source_id: Stable benchmark source identifier.
        book_slug: Stable slug derived from the parsed document directory name.
        book_dir: Original parsed document directory name.
        chunk_id: Chunk identifier from BrandMind's parser.
        pages: Page numbers recorded by the parser.
        source: Source field from chunk metadata.
        original_document: Original document name from chunk metadata.
        author: Author field from chunk metadata.
        section_summary: Parser-generated section summary.
        word_count: Parser-reported word count if available.
    """

    source_id: str
    book_slug: str
    book_dir: str
    chunk_id: str
    pages: list[int]
    source: str
    original_document: str
    author: str
    section_summary: str
    word_count: int | None


def slugify(value: str) -> str:
    """Convert a parsed document directory name into a stable lowercase slug.

    Args:
        value: Directory name or source string.

    Returns:
        A lowercase slug containing only letters, digits, and underscores.
    """

    normalized = re.sub(r"_[0-9]{8}_[0-9]{6}$", "", value)
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", normalized)
    return normalized.strip("_").lower()


def normalize_pages(raw_pages: object) -> list[int]:
    """Normalize parser page metadata into a list of integers.

    Args:
        raw_pages: Page metadata from a parsed chunk.

    Returns:
        A sorted list of integer page numbers. Invalid values are ignored.
    """

    if raw_pages is None:
        return []
    if isinstance(raw_pages, int):
        return [raw_pages]
    if isinstance(raw_pages, list):
        pages = []
        for page in raw_pages:
            if isinstance(page, int):
                pages.append(page)
            elif isinstance(page, str) and page.isdigit():
                pages.append(int(page))
        return sorted(set(pages))
    if isinstance(raw_pages, str) and raw_pages.isdigit():
        return [int(raw_pages)]
    return []


def load_chunks(chunks_path: Path) -> list[dict[str, object]]:
    """Load and validate a BrandMind ``chunks.json`` file.

    Args:
        chunks_path: Path to a parsed document ``chunks.json`` file.

    Returns:
        The list of chunk dictionaries.

    Raises:
        ValueError: If the file does not contain a ``chunks`` list.
    """

    payload = json.loads(chunks_path.read_text(encoding="utf-8"))
    chunks = payload.get("chunks")
    if not isinstance(chunks, list):
        raise ValueError(f"Expected a chunks list in {chunks_path}.")
    return chunks


def iter_book_chunk_paths(parsed_root: Path) -> Iterable[Path]:
    """Yield canonical five-book chunk paths in deterministic order.

    Args:
        parsed_root: Root directory containing parsed document folders.

    Yields:
        Paths to canonical ``chunks.json`` files.

    Raises:
        FileNotFoundError: If a canonical book folder is missing ``chunks.json``.
    """

    for book_dir in CANONICAL_BOOK_DIRS:
        chunks_path = parsed_root / book_dir / "chunks.json"
        if not chunks_path.exists():
            raise FileNotFoundError(f"Missing canonical chunks file: {chunks_path}")
        yield chunks_path


def build_records(
    parsed_root: Path,
) -> tuple[list[HippoRagCorpusRecord], dict[str, SourceMetadata]]:
    """Build HippoRAG corpus records and source metadata from parsed chunks.

    Args:
        parsed_root: Root directory containing parsed document folders.

    Returns:
        A pair of corpus records and metadata keyed by source ID.
    """

    records: list[HippoRagCorpusRecord] = []
    metadata_by_source_id: dict[str, SourceMetadata] = {}

    for chunks_path in iter_book_chunk_paths(parsed_root):
        book_dir = chunks_path.parent.name
        book_slug = slugify(book_dir)
        chunks = load_chunks(chunks_path)

        for chunk in chunks:
            chunk_id = str(chunk.get("chunk_id", "")).strip()
            content = str(chunk.get("content", "")).strip()
            raw_metadata = chunk.get("metadata", {})
            chunk_metadata = raw_metadata if isinstance(raw_metadata, dict) else {}

            if not chunk_id:
                raise ValueError(f"Chunk without chunk_id in {chunks_path}.")
            if not content:
                raise ValueError(f"Chunk {chunk_id} in {chunks_path} has empty content.")

            source_id = f"{book_slug}::{chunk_id}"
            if source_id in metadata_by_source_id:
                raise ValueError(f"Duplicate source_id generated: {source_id}")

            record = HippoRagCorpusRecord(
                title=source_id,
                text=content,
                idx=len(records),
            )
            records.append(record)

            word_count = chunk_metadata.get("word_count")
            metadata_by_source_id[source_id] = SourceMetadata(
                source_id=source_id,
                book_slug=book_slug,
                book_dir=book_dir,
                chunk_id=chunk_id,
                pages=normalize_pages(chunk_metadata.get("pages")),
                source=str(chunk_metadata.get("source", "")),
                original_document=str(chunk_metadata.get("original_document", "")),
                author=str(chunk_metadata.get("author", "")),
                section_summary=str(chunk_metadata.get("section_summary", "")),
                word_count=word_count if isinstance(word_count, int) else None,
            )

    return records, metadata_by_source_id


def write_json(path: Path, payload: object) -> None:
    """Write pretty JSON with UTF-8 encoding.

    Args:
        path: Output path.
        payload: JSON-serializable payload.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def export_corpus(parsed_root: Path, corpus_path: Path, metadata_path: Path) -> None:
    """Export five-book corpus and source metadata files.

    Args:
        parsed_root: Root directory containing parsed documents.
        corpus_path: Output path for HippoRAG corpus JSON.
        metadata_path: Output path for metadata sidecar JSON.
    """

    records, metadata_by_source_id = build_records(parsed_root)
    write_json(corpus_path, [asdict(record) for record in records])
    write_json(
        metadata_path,
        {
            "total_records": len(records),
            "canonical_book_dirs": list(CANONICAL_BOOK_DIRS),
            "sources": {
                source_id: asdict(metadata)
                for source_id, metadata in metadata_by_source_id.items()
            },
        },
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for corpus export."""

    parser = argparse.ArgumentParser(
        description="Export BrandMind five-book chunks to HippoRAG corpus format.",
    )
    parser.add_argument(
        "--parsed-root",
        type=Path,
        default=Path("data/parsed_documents"),
        help="Root directory containing parsed document folders.",
    )
    parser.add_argument(
        "--corpus-output",
        type=Path,
        default=Path(".codex/benchmarks/hipporag/corpus/marketing_5books_corpus.json"),
        help="Output HippoRAG corpus JSON path.",
    )
    parser.add_argument(
        "--metadata-output",
        type=Path,
        default=Path(".codex/benchmarks/hipporag/corpus/marketing_5books_metadata.json"),
        help="Output source metadata JSON path.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the corpus exporter from the command line."""

    args = parse_args()
    export_corpus(
        parsed_root=args.parsed_root,
        corpus_path=args.corpus_output,
        metadata_path=args.metadata_output,
    )


if __name__ == "__main__":
    main()
```

### Component 4: Unit tests

> Status: Implemented in `tests/unit/test_hipporag_comparison.py`.

#### Requirement 4 — Test adapter and exporter without live API calls

- **Requirement**: Add tests that verify the dimension patch and exporter behavior without calling
  LiteLLM, Gemini, Milvus, or FalkorDB.

- **Implementation**:

Target file: `tests/unit/test_hipporag_comparison.py` `[NEW]`

```python
"""Unit tests for HippoRAG benchmark foundation utilities."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from evaluation.hipporag_comparison.export_corpus import (
    CANONICAL_BOOK_DIRS,
    build_records,
    export_corpus,
    normalize_pages,
    slugify,
)


def test_slugify_removes_timestamp_suffix() -> None:
    """Directory timestamps should not leak into stable benchmark book slugs."""

    slug = slugify("Positioning_The_Battle_for_Your_Mind_20260206_170800")

    assert slug == "positioning_the_battle_for_your_mind"


@pytest.mark.parametrize(
    ("raw_pages", "expected"),
    [
        (7, [7]),
        ("8", [8]),
        ([3, "2", "bad", 3], [2, 3]),
        (None, []),
        ({"page": 1}, []),
    ],
)
def test_normalize_pages(raw_pages: object, expected: list[int]) -> None:
    """Page metadata should normalize to a stable integer list."""

    assert normalize_pages(raw_pages) == expected


def write_fixture_chunks(parsed_root: Path, book_dir: str, chunk_id: str) -> None:
    """Write one minimal parsed-document chunks fixture."""

    book_path = parsed_root / book_dir
    book_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "chunks": [
            {
                "chunk_id": chunk_id,
                "content": f"Content for {book_dir}.",
                "metadata": {
                    "author": "Author",
                    "original_document": f"{book_dir}.pdf",
                    "pages": [1, "2"],
                    "section_summary": "Section summary.",
                    "source": "Fixture source.",
                    "word_count": 4,
                },
            }
        ],
        "total_chunks": 1,
    }
    (book_path / "chunks.json").write_text(json.dumps(payload), encoding="utf-8")


def test_build_records_exports_all_canonical_books(tmp_path: Path) -> None:
    """Exporter should preserve deterministic order and stable source IDs."""

    for index, book_dir in enumerate(CANONICAL_BOOK_DIRS):
        write_fixture_chunks(tmp_path, book_dir, f"chunk_{index}")

    records, metadata_by_source_id = build_records(tmp_path)

    assert len(records) == len(CANONICAL_BOOK_DIRS)
    assert len(metadata_by_source_id) == len(CANONICAL_BOOK_DIRS)
    assert records[0].idx == 0
    assert records[0].title.endswith("::chunk_0")
    assert records[0].title in metadata_by_source_id
    assert metadata_by_source_id[records[0].title].pages == [1, 2]


def test_export_corpus_writes_corpus_and_metadata(tmp_path: Path) -> None:
    """Exporter should write HippoRAG corpus JSON and metadata sidecar."""

    for index, book_dir in enumerate(CANONICAL_BOOK_DIRS):
        write_fixture_chunks(tmp_path, book_dir, f"chunk_{index}")

    corpus_path = tmp_path / "out" / "corpus.json"
    metadata_path = tmp_path / "out" / "metadata.json"

    export_corpus(tmp_path, corpus_path, metadata_path)

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert len(corpus) == len(CANONICAL_BOOK_DIRS)
    assert corpus[0] == {
        "title": corpus[0]["title"],
        "text": f"Content for {CANONICAL_BOOK_DIRS[0]}.",
        "idx": 0,
    }
    assert metadata["total_records"] == len(CANONICAL_BOOK_DIRS)
    assert corpus[0]["title"] in metadata["sources"]


def test_install_gemini_embedding_dimension_patch_passes_dimensions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The HippoRAG embedding patch should pass dimensions to the client call."""

    captured: dict[str, object] = {}

    class FakeEmbeddingsClient:
        """Fake OpenAI-compatible embeddings client for testing."""

        def create(
            self,
            *,
            input: list[str],
            model: str,
            dimensions: int,
        ) -> SimpleNamespace:
            """Capture call parameters and return one fake embedding."""

            captured["input"] = input
            captured["model"] = model
            captured["dimensions"] = dimensions
            return SimpleNamespace(data=[SimpleNamespace(embedding=[1.0, 0.0])])

    class FakeOpenAIEmbeddingModel:
        """Fake HippoRAG embedding model patched by the adapter."""

        def __init__(self) -> None:
            self.client = SimpleNamespace(embeddings=FakeEmbeddingsClient())
            self.embedding_model_name = "gemini-embedding-001"

    import sys

    hipporag_module = ModuleType("hipporag")
    embedding_model_module = ModuleType("hipporag.embedding_model")
    openai_module = ModuleType("hipporag.embedding_model.OpenAI")
    openai_module.OpenAIEmbeddingModel = FakeOpenAIEmbeddingModel

    monkeypatch.setitem(sys.modules, "hipporag", hipporag_module)
    monkeypatch.setitem(sys.modules, "hipporag.embedding_model", embedding_model_module)
    monkeypatch.setitem(sys.modules, "hipporag.embedding_model.OpenAI", openai_module)

    from evaluation.hipporag_comparison.hipporag_litellm import (
        install_gemini_embedding_dimension_patch,
    )

    install_gemini_embedding_dimension_patch(embedding_dimensions=1536)

    model = openai_module.OpenAIEmbeddingModel()
    embeddings = model.encode(["line one\nline two"])

    assert embeddings.shape == (1, 2)
    assert captured == {
        "input": ["line one line two"],
        "model": "gemini-embedding-001",
        "dimensions": 1536,
    }
```

------------------------------------------------------------------------

## Test Execution Log

- `uv run pytest tests/unit/test_hipporag_comparison.py -q`
  - **Result**: Pass, `9 passed`.
  - **Purpose**: Verified source ID slugging, page normalization, deterministic corpus export,
    metadata sidecar writing, and embedding `dimensions=1536` patch behavior without live API
    calls.
- `uv run ruff format --check evaluation/hipporag_comparison tests/unit/test_hipporag_comparison.py`
  - **Result**: Pass, all four files already formatted after one local formatting pass.
- `uv run ruff check evaluation/hipporag_comparison tests/unit/test_hipporag_comparison.py`
  - **Result**: Pass, all checks passed.
- `uv run python -m evaluation.hipporag_comparison.export_corpus`
  - **Result**: Pass.
  - **Output**: `.codex/benchmarks/hipporag/corpus/marketing_5books_corpus.json` and
    `.codex/benchmarks/hipporag/corpus/marketing_5books_metadata.json`.
  - **Record count**: 3,185 corpus records and 3,185 metadata sources.
- `bash scripts/setup_hipporag_env.sh`
  - **Result**: Pass.
  - **Verified**: `from hipporag import HippoRAG` succeeds and `litellm_version` is `1.83.14`.
  - **Caveat**: pip reports a dependency tension around `tokenizers` because LiteLLM `1.83.14`
    requires `tokenizers==0.22.2` while the pinned HippoRAG online path installs
    `transformers==4.45.2`, which requires `tokenizers<0.21`. Runtime import and adapter smoke
    still passed.
- `conda run -n brandmind-hipporag python -c "... build_hipporag(...).embedding_model.batch_encode(...) ..."`
  - **Result**: Pass.
  - **Output**: `adapter_embedding_dim 1536`.
- `make typecheck`
  - **Result**: Pass.
  - **Note**: One pre-existing long line in
    `src/core/src/core/brand_strategy/orchestrator/quality_gate.py` was wrapped to satisfy the
    project typecheck pipeline.
- `make test-unit`
  - **Result**: Blocked by unrelated missing optional/runtime test dependencies in the current
    environment.
  - **Errors**: `ModuleNotFoundError: No module named 'langchain_text_splitters'` from
    `tests/unit/test_section_finder.py` and `ModuleNotFoundError: No module named 'textual'` from
    `tests/unit/test_tui_widgets.py`.

------------------------------------------------------------------------

## Decision Log

- **2026-05-09**: Use a separate conda env `brandmind-hipporag` because HippoRAG's dependency
  pins conflict with the main Python 3.12 uv workspace.
- **2026-05-09**: Keep `litellm==1.83.14` despite HippoRAG's older pin because the user explicitly
  requires avoiding lower LiteLLM versions.
- **2026-05-09**: Use OpenAI-compatible LiteLLM endpoints instead of hosting a new vector DB or
  graph DB for HippoRAG. HippoRAG native storage remains local files/parquet/igraph.
- **2026-05-09**: Force `dimensions=1536` in the HippoRAG embedding adapter to align with
  BrandMind's configured embedding dimension.

------------------------------------------------------------------------

## Task Summary

Implemented the HippoRAG benchmark foundation. The tracked project now contains a reproducible
HippoRAG conda setup script, a project-owned LiteLLM adapter that forces Gemini embeddings to
`1536` dimensions, a deterministic five-book corpus exporter, and unit tests for adapter/exporter
behavior. The exporter produced the expected 3,185-record five-book corpus under ignored
`.codex/benchmarks/hipporag/corpus/`.

The foundation does not modify BrandMind's Milvus or FalkorDB services. The remaining benchmark
work is dataset generation/validation, BrandMind and HippoRAG runner implementation, and the
controlled reader/judge comparison layer.
