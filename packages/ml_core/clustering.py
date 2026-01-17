import numpy as np
from typing import Dict, List, Tuple, Optional
import hdbscan
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity


def cluster_hdbscan(
    embeddings: Dict[str, List[float]],
    min_cluster_size: int = 2,
    min_samples: int = 1,
    cluster_selection_epsilon: float = 0.15
) -> Tuple[Dict[str, int], Dict[int, List[str]], Dict[str, float]]:
    if len(embeddings) < 2:
        return {}, {}, {}
    
    prompt_ids = list(embeddings.keys())
    embedding_matrix = np.array([embeddings[pid] for pid in prompt_ids])
    
    from sklearn.preprocessing import normalize
    embedding_matrix_normalized = normalize(embedding_matrix, norm='l2')
    
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='euclidean',
        cluster_selection_epsilon=cluster_selection_epsilon,
    )
    
    cluster_labels = clusterer.fit_predict(embedding_matrix_normalized)
    
    prompt_to_cluster: Dict[str, int] = {}
    cluster_to_prompts: Dict[int, List[str]] = {}
    prompt_to_confidence: Dict[str, float] = {}
    
    probabilities = clusterer.probabilities_
    
    for idx, (prompt_id, label) in enumerate(zip(prompt_ids, cluster_labels)):
        if label != -1:
            prompt_to_cluster[prompt_id] = int(label)
            if label not in cluster_to_prompts:
                cluster_to_prompts[label] = []
            cluster_to_prompts[label].append(prompt_id)
            
            if probabilities is not None and len(probabilities) > idx:
                prompt_to_confidence[prompt_id] = float(probabilities[idx])
            else:
                cluster_embeddings = embedding_matrix_normalized[cluster_labels == label]
                centroid = np.mean(cluster_embeddings, axis=0)
                similarity = cosine_similarity([embedding_matrix_normalized[idx]], [centroid])[0][0]
                prompt_to_confidence[prompt_id] = float(similarity)
        else:
            prompt_to_cluster[prompt_id] = -1
            prompt_to_confidence[prompt_id] = 0.0
    
    return prompt_to_cluster, cluster_to_prompts, prompt_to_confidence


def cluster_kmeans(
    embeddings: Dict[str, List[float]],
    k: int
) -> Tuple[Dict[str, int], Dict[int, List[str]], Dict[str, float]]:
    if len(embeddings) < k:
        return cluster_hdbscan(embeddings)
    
    prompt_ids = list(embeddings.keys())
    embedding_matrix = np.array([embeddings[pid] for pid in prompt_ids])
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(embedding_matrix)
    
    prompt_to_cluster: Dict[str, int] = {}
    cluster_to_prompts: Dict[int, List[str]] = {}
    prompt_to_confidence: Dict[str, float] = {}
    
    for idx, (prompt_id, label) in enumerate(zip(prompt_ids, cluster_labels)):
        prompt_to_cluster[prompt_id] = int(label)
        if label not in cluster_to_prompts:
            cluster_to_prompts[label] = []
        cluster_to_prompts[label].append(prompt_id)
        
        centroid = kmeans.cluster_centers_[label]
        distance = np.linalg.norm(embedding_matrix[idx] - centroid)
        max_distance = np.max([np.linalg.norm(emb - centroid) for emb in embedding_matrix[cluster_labels == label]])
        confidence = 1.0 - (distance / max_distance) if max_distance > 0 else 1.0
        prompt_to_confidence[prompt_id] = float(max(0.0, min(1.0, confidence)))
    
    return prompt_to_cluster, cluster_to_prompts, prompt_to_confidence


def compute_cluster_centroids(
    embeddings: Dict[str, List[float]],
    cluster_to_prompts: Dict[int, List[str]]
) -> Dict[int, List[float]]:
    centroids = {}
    
    for cluster_id, prompt_ids in cluster_to_prompts.items():
        if cluster_id == -1:
            continue
        
        cluster_embeddings = [embeddings[pid] for pid in prompt_ids if pid in embeddings]
        if cluster_embeddings:
            centroid = np.mean(cluster_embeddings, axis=0).tolist()
            centroids[cluster_id] = centroid
    
    return centroids
