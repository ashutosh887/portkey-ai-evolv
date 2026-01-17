import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity


def assign_to_cluster(
    embedding: List[float],
    centroids: Dict[int, List[float]],
    threshold: float = 0.75
) -> Tuple[Optional[int], float]:
    if not centroids:
        return None, 0.0
    
    embedding_array = np.array(embedding).reshape(1, -1)
    
    best_cluster = None
    best_similarity = -1.0
    
    for cluster_id, centroid in centroids.items():
        centroid_array = np.array(centroid).reshape(1, -1)
        similarity = cosine_similarity(embedding_array, centroid_array)[0][0]
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_cluster = cluster_id
    
    if best_similarity >= threshold:
        return best_cluster, float(best_similarity)
    else:
        return None, float(best_similarity)


def assign_batch(
    embeddings: Dict[str, List[float]],
    centroids: Dict[int, List[float]],
    threshold: float = 0.75
) -> Dict[str, Tuple[Optional[int], float]]:
    assignments = {}
    
    for prompt_id, embedding in embeddings.items():
        cluster_id, similarity = assign_to_cluster(embedding, centroids, threshold)
        assignments[prompt_id] = (cluster_id, similarity)
    
    return assignments
