# ML Core Engine - Module C

Semantic Intelligence Layer for prompt understanding at scale.

## Overview

This module is **OFFLINE / BATCH FIRST**. It does NOT serve user requests directly. It consumes a CSV file and produces semantic artifacts.

## Purpose

The ML Core Engine answers:
- What does this prompt mean?
- Which prompts are semantically equivalent?
- How should prompts be grouped into families?
- Which prompts are good examples of each family?

## Input Format

**Strict CSV format:**
- CSV has EXACTLY ONE column
- Column name: `prompt`
- Each row contains ONE raw prompt (string)

Example:
```csv
prompt
"Summarize this document in 200 words"
"Summarize the report in 100 words"
"Classify the sentiment of this review"
```

## Output Artifacts

1. **prompt_embeddings.json** - prompt_id → embedding vector
2. **prompt_clusters.json** - prompt_id → cluster_id, cluster_confidence
3. **cluster_centroids.json** - cluster_id → centroid_vector
4. **retrieval_index.faiss** - FAISS index for ANN retrieval
5. **reranked_examples.json** (optional) - Reranked results if enabled
6. **explanations.json** (optional) - LLM explanations if enabled

## Usage

### CLI Command

```bash
# Basic usage
genome ml-process prompts.csv

# With custom output directory
genome ml-process prompts.csv --output ./results

# With different embedding model
genome ml-process prompts.csv --embedding instructor-xl

# Enable optional LLM features
genome ml-process prompts.csv --rerank --explain
```

### Python API

```python
from packages.ml_core.pipeline import MLPipeline
from packages.ml_core.config import MLConfig
from pathlib import Path
import asyncio

# Create config
config = MLConfig(
    embedding_model="bge-large-en",
    enable_reranking=False,
    enable_explanations=False,
    output_dir="./output"
)

# Run pipeline
pipeline = MLPipeline(config)
asyncio.run(pipeline.run(Path("prompts.csv")))
```

## Pipeline Steps

### Step 0: Normalization
- Rule-based text preprocessing
- NO LLM

### Step 1: Semantic Embedding
- Convert prompts to vectors
- Models: bge-large-en, instructor-xl, text-embedding-3-large
- NO LLM

### Step 2: Clustering
- HDBSCAN (default) or K-means
- Groups semantically equivalent prompts
- NO LLM

### Step 3: Incremental Assignment
- Assign new prompts to existing clusters
- Nearest centroid with threshold
- NO LLM

### Step 4: FAISS Index
- Build ANN retrieval index
- Sub-10ms retrieval
- NO LLM

### Step 5: Reranking (Optional)
- LLM-based reranking via Portkey
- Only reranks top-k candidates
- GATED - requires `--rerank` flag

### Step 6: Explainability (Optional)
- LLM explanations via Portkey
- Explains cluster assignments
- GATED - requires `--explain` flag

## Configuration

Environment variables:
- `ML_EMBEDDING_MODEL` - Embedding model (default: bge-large-en)
- `ML_CLUSTERING_ALGORITHM` - hdbscan or kmeans (default: hdbscan)
- `ML_MIN_CLUSTER_SIZE` - Minimum cluster size (default: 2)
- `ML_SIMILARITY_THRESHOLD` - Threshold for incremental assignment (default: 0.75)
- `ML_ENABLE_RERANKING` - Enable reranking (default: false)
- `ML_ENABLE_EXPLANATIONS` - Enable explanations (default: false)
- `ML_OUTPUT_DIR` - Output directory (default: ./output)
- `ML_CACHE_DIR` - Cache directory (default: ./cache)
- `PORTKEY_API_KEY` - Required for LLM features
- `PORTKEY_VIRTUAL_KEY` - Optional Portkey virtual key
- `OPENAI_API_KEY` - Required for text-embedding-3-large model

## Design Philosophy

- **ML-first**: Embedding-centric approach
- **Deterministic**: Same input → same output
- **Multi-stage**: Clear separation of concerns
- **LLMs are assistants**: Only used when explicitly gated
- **NO LLMs in hot path**: Core pipeline is LLM-free

## Error Handling

- If embedding fails → abort batch
- If clustering fails → embeddings are preserved
- If LLM fails → skip optional steps, core outputs still produced

## Success Criteria

The module is correct if:
- ✅ CSV prompts are embedded
- ✅ Prompts are clustered semantically
- ✅ Cluster IDs are stable
- ✅ ANN retrieval works
- ✅ Optional LLM steps are gated and isolated
- ✅ Outputs are reproducible

