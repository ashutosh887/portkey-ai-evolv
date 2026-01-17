"""
Clustering engine using HDBSCAN
"""

import numpy as np
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
import hdbscan

from packages.core.models import PromptDNA


CLUSTERING_CONFIG = {
    "min_cluster_size": 2,
    "min_samples": 1,
    "metric": "cosine",
    "cluster_selection_epsilon": 0.15,
}

CONFIDENCE_THRESHOLDS = {
    "auto_merge": 0.85,
    "suggest_merge": 0.70,
    "new_family": 0.50,
}


def compute_similarity_matrix(embeddings: List[List[float]]) -> np.ndarray:
    """Compute cosine similarity matrix"""
    embeddings_array = np.array(embeddings)
    return cosine_similarity(embeddings_array)


def cluster_prompts(prompt_dnas: List[PromptDNA]) -> dict[int, List[str]]:
    """
    Cluster prompts using HDBSCAN
    
    Args:
        prompt_dnas: List of PromptDNA objects with embeddings
    
    Returns:
        Dictionary mapping cluster_id -> list of prompt IDs
    """
    if len(prompt_dnas) < 2:
        return {}
    
    # Extract embeddings
    embeddings = [dna.embedding for dna in prompt_dnas if dna.embedding]
    
    if len(embeddings) < 2:
        return {}
    
    embeddings_array = np.array(embeddings)
    
    # Run HDBSCAN
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=CLUSTERING_CONFIG["min_cluster_size"],
        min_samples=CLUSTERING_CONFIG["min_samples"],
        metric=CLUSTERING_CONFIG["metric"],
        cluster_selection_epsilon=CLUSTERING_CONFIG["cluster_selection_epsilon"],
    )
    
    cluster_labels = clusterer.fit_predict(embeddings_array)
    
    # Group prompts by cluster
    clusters: dict[int, List[str]] = {}
    for idx, label in enumerate(cluster_labels):
        if label != -1:  # -1 means noise/outlier
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(prompt_dnas[idx].id)
    
    return clusters


def compute_confidence(prompt_dna: PromptDNA, family_embeddings: List[List[float]]) -> float:
    """
    Compute confidence score for assigning a prompt to a family
    
    Args:
        prompt_dna: The prompt to classify
        family_embeddings: Embeddings of existing family members
    
    Returns:
        Confidence score (0.0 to 1.0)
    """
    if not prompt_dna.embedding or not family_embeddings:
        return 0.0
    
    # Compute average similarity to family members
    similarities = [
        cosine_similarity([prompt_dna.embedding], [emb])[0][0]
        for emb in family_embeddings
    ]
    
    return float(np.mean(similarities))
