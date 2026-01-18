from dataclasses import dataclass
from typing import Optional, Literal
import os


@dataclass
class MLConfig:
    # Changed default to MiniLM (80MB) instead of BGE-large (1.34GB) to avoid memory issues
    embedding_model: Literal["minilm", "bge-large-en", "instructor-xl", "text-embedding-3-large"] = "minilm"
    clustering_algorithm: Literal["hdbscan", "kmeans"] = "hdbscan"
    min_cluster_size: int = 2
    min_samples: int = 1
    cluster_selection_epsilon: float = 0.15
    k_clusters: Optional[int] = None
    similarity_threshold: float = 0.75
    faiss_index_type: Literal["IVF_FLAT", "HNSW"] = "IVF_FLAT"
    faiss_nlist: int = 100
    faiss_m: int = 32
    faiss_ef_construction: int = 200
    enable_reranking: bool = False
    enable_explanations: bool = False
    rerank_top_k: int = 8
    rerank_model: Literal["gpt-4o-mini", "claude-3-haiku", "gemini-1.5-flash"] = "gpt-4o-mini"
    explanation_model: Literal["gpt-4o-mini", "claude-3-haiku"] = "gpt-4o-mini"
    portkey_api_key: Optional[str] = None
    portkey_virtual_key: Optional[str] = None
    output_dir: str = "./output"
    cache_dir: str = "./cache"
    
    @classmethod
    def from_env(cls) -> "MLConfig":
        return cls(
            embedding_model=os.getenv("ML_EMBEDDING_MODEL", "minilm"),
            clustering_algorithm=os.getenv("ML_CLUSTERING_ALGORITHM", "hdbscan"),
            min_cluster_size=int(os.getenv("ML_MIN_CLUSTER_SIZE", "2")),
            similarity_threshold=float(os.getenv("ML_SIMILARITY_THRESHOLD", "0.75")),
            enable_reranking=os.getenv("ML_ENABLE_RERANKING", "false").lower() == "true",
            enable_explanations=os.getenv("ML_ENABLE_EXPLANATIONS", "false").lower() == "true",
            portkey_api_key=os.getenv("PORTKEY_API_KEY"),
            portkey_virtual_key=os.getenv("PORTKEY_VIRTUAL_KEY"),
            output_dir=os.getenv("ML_OUTPUT_DIR", "./output"),
            cache_dir=os.getenv("ML_CACHE_DIR", "./cache"),
        )
