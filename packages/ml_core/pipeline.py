import csv
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

from packages.ml_core.config import MLConfig
from packages.ml_core.normalization import normalize_and_id
from packages.ml_core.embedding import create_embeddings
from packages.ml_core.clustering import cluster_hdbscan, cluster_kmeans, compute_cluster_centroids
from packages.ml_core.retrieval import FAISSIndex
from packages.ml_core.reranking import Reranker
from packages.ml_core.explainability import Explainer


class MLPipeline:
    def __init__(self, config: Optional[MLConfig] = None):
        self.config = config or MLConfig.from_env()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.reranker = None
        self.explainer = None
        
        if self.config.enable_reranking:
            self.reranker = Reranker(
                api_key=self.config.portkey_api_key,
                virtual_key=self.config.portkey_virtual_key,
                model=self.config.rerank_model
            )
        
        if self.config.enable_explanations:
            self.explainer = Explainer(
                api_key=self.config.portkey_api_key,
                virtual_key=self.config.portkey_virtual_key,
                model=self.config.explanation_model
            )
    
    def load_csv(self, csv_path: Path) -> Dict[str, str]:
        prompts = {}
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if 'prompt' not in reader.fieldnames:
                raise ValueError("CSV must have exactly one column named 'prompt'")
            
            for row in reader:
                raw_text = row['prompt'].strip()
                if raw_text:
                    normalized, prompt_id = normalize_and_id(raw_text)
                    prompts[prompt_id] = normalized
        
        return prompts
    
    def step_0_normalize(self, csv_path: Path) -> Dict[str, str]:
        return self.load_csv(csv_path)
    
    def step_1_embed(self, prompts: Dict[str, str]) -> Dict[str, List[float]]:
        return create_embeddings(
            prompts,
            model_name=self.config.embedding_model,
            cache_dir=self.config.cache_dir,
            portkey_api_key=self.config.portkey_api_key,
            portkey_virtual_key=self.config.portkey_virtual_key
        )
    
    def step_2_cluster(
        self,
        embeddings: Dict[str, List[float]]
    ) -> Tuple[Dict[str, int], Dict[int, List[str]], Dict[str, float]]:
        if self.config.clustering_algorithm == "hdbscan":
            return cluster_hdbscan(
                embeddings,
                min_cluster_size=self.config.min_cluster_size,
                min_samples=self.config.min_samples,
                cluster_selection_epsilon=self.config.cluster_selection_epsilon
            )
        else:
            if self.config.k_clusters is None:
                raise ValueError("k_clusters must be set for k-means clustering")
            return cluster_kmeans(embeddings, k=self.config.k_clusters)
    
    def step_3_incremental(
        self,
        new_embeddings: Dict[str, List[float]],
        centroids: Dict[int, List[float]]
    ) -> Dict[str, Tuple[Optional[int], float]]:
        from packages.ml_core.incremental import assign_batch
        return assign_batch(
            new_embeddings,
            centroids,
            threshold=self.config.similarity_threshold
        )
    
    def step_4_build_index(
        self,
        embeddings: Dict[str, List[float]]
    ) -> FAISSIndex:
        if not embeddings:
            raise ValueError("No embeddings to index")
        
        first_emb = next(iter(embeddings.values()))
        dimension = len(first_emb)
        
        num_vectors = len(embeddings)
        adjusted_nlist = min(self.config.faiss_nlist, max(1, num_vectors))
        
        if self.config.faiss_index_type == "IVF_FLAT" and num_vectors < 10:
            index_type = "HNSW"
        else:
            index_type = self.config.faiss_index_type
        
        index = FAISSIndex(
            dimension=dimension,
            index_type=index_type,
            nlist=adjusted_nlist,
            m=self.config.faiss_m,
            ef_construction=self.config.faiss_ef_construction
        )
        
        index.add_batch(embeddings)
        
        return index
    
    def step_5_rerank(
        self,
        query: str,
        candidates: List[Tuple[str, str]]
    ) -> List[Tuple[str, float]]:
        if not self.reranker:
            return [(pid, 1.0) for pid, _ in candidates]
        
        return self.reranker.rerank(query, candidates, top_k=self.config.rerank_top_k)
    
    def step_6_explain(
        self,
        prompt: str,
        prompt_id: str,
        cluster_id: int,
        cluster_members: List[str],
        similarity_score: float
    ) -> str:
        if not self.explainer:
            return ""
        
        return self.explainer.explain_cluster_assignment(
            prompt, prompt_id, cluster_id, cluster_members, similarity_score
        )
    
    def save_artifacts(
        self,
        embeddings: Dict[str, List[float]],
        prompt_to_cluster: Dict[str, int],
        cluster_to_prompts: Dict[int, List[str]],
        prompt_to_confidence: Dict[str, float],
        centroids: Dict[int, List[float]],
        index: FAISSIndex,
        prompts: Dict[str, str],
        reranked_examples: Optional[Dict[str, List[Dict]]] = None,
        explanations: Optional[Dict[str, str]] = None
    ):
        import numpy as np
        
        embeddings_output = [
            {
                "prompt_id": pid,
                "embedding": [float(x) for x in emb] if isinstance(emb, (list, np.ndarray)) else emb
            }
            for pid, emb in embeddings.items()
        ]
        with open(self.output_dir / "prompt_embeddings.json", 'w') as f:
            json.dump(embeddings_output, f, indent=2)
        
        clusters_output = [
            {
                "prompt_id": pid,
                "cluster_id": int(cid) if isinstance(cid, (np.integer, np.int64)) else int(cid),
                "cluster_confidence": float(prompt_to_confidence.get(pid, 0.0))
            }
            for pid, cid in prompt_to_cluster.items()
        ]
        with open(self.output_dir / "prompt_clusters.json", 'w') as f:
            json.dump(clusters_output, f, indent=2)
        
        centroids_output = [
            {
                "cluster_id": int(cid) if isinstance(cid, (np.integer, np.int64)) else int(cid),
                "centroid_vector": [float(x) for x in centroid]
            }
            for cid, centroid in centroids.items()
        ]
        with open(self.output_dir / "cluster_centroids.json", 'w') as f:
            json.dump(centroids_output, f, indent=2)
        
        index.save(self.output_dir / "retrieval_index.faiss")
        
        if reranked_examples:
            reranked_output = {
                pid: [
                    {
                        "prompt_id": item["prompt_id"],
                        "score": float(item["score"])
                    }
                    for item in items
                ]
                for pid, items in reranked_examples.items()
            }
            with open(self.output_dir / "reranked_examples.json", 'w') as f:
                json.dump(reranked_output, f, indent=2)
        
        if explanations:
            with open(self.output_dir / "explanations.json", 'w') as f:
                json.dump(explanations, f, indent=2)
    
    async def run(self, csv_path: Path):
        print(f"Loading CSV from {csv_path}...")
        prompts = self.step_0_normalize(csv_path)
        print(f"✓ Normalized {len(prompts)} prompts")
        
        print("Generating embeddings...")
        embeddings = self.step_1_embed(prompts)
        print(f"✓ Generated {len(embeddings)} embeddings")
        
        print("Clustering prompts...")
        prompt_to_cluster, cluster_to_prompts, prompt_to_confidence = self.step_2_cluster(embeddings)
        print(f"✓ Created {len(cluster_to_prompts)} clusters")
        
        print("Computing cluster centroids...")
        centroids = compute_cluster_centroids(embeddings, cluster_to_prompts)
        print(f"✓ Computed {len(centroids)} centroids")
        
        print("Building FAISS index...")
        index = self.step_4_build_index(embeddings)
        print("✓ FAISS index built")
        
        reranked_examples = None
        if self.config.enable_reranking and self.reranker:
            print("Reranking examples...")
            reranked_examples = {}
            sample_prompts = list(prompts.items())[:5]
            for query_id, query_text in sample_prompts:
                query_emb = embeddings[query_id]
                top_k_results = index.search(query_emb, k=self.config.rerank_top_k)
                
                candidates = [(pid, prompts.get(pid, "")) for pid, _ in top_k_results]
                
                reranked = self.step_5_rerank(query_text, candidates)
                reranked_examples[query_id] = [
                    {"prompt_id": pid, "score": score}
                    for pid, score in reranked
                ]
            print("✓ Reranking complete")
        
        explanations = None
        if self.config.enable_explanations and self.explainer:
            print("Generating explanations...")
            explanations = {}
            for prompt_id, cluster_id in list(prompt_to_cluster.items())[:10]:
                if cluster_id != -1:
                    prompt_text = prompts.get(prompt_id, "")
                    cluster_members = [
                        prompts.get(pid, "") for pid in cluster_to_prompts.get(cluster_id, [])
                        if pid != prompt_id
                    ][:5]
                    confidence = prompt_to_confidence.get(prompt_id, 0.0)
                    
                    explanation = self.step_6_explain(
                        prompt_text, prompt_id, cluster_id, cluster_members, confidence
                    )
                    explanations[prompt_id] = explanation
            print("✓ Explanations generated")
        
        print("Saving artifacts...")
        self.save_artifacts(
            embeddings,
            prompt_to_cluster,
            cluster_to_prompts,
            prompt_to_confidence,
            centroids,
            index,
            prompts,
            reranked_examples,
            explanations
        )
        print("✓ All artifacts saved to", self.output_dir)
        
        print("\n✅ Pipeline complete!")
        print(f"  - Prompts processed: {len(prompts)}")
        print(f"  - Clusters created: {len(cluster_to_prompts)}")
        print(f"  - Output directory: {self.output_dir}")


def run_pipeline(csv_path: str, config: Optional[MLConfig] = None):
    pipeline = MLPipeline(config)
    asyncio.run(pipeline.run(Path(csv_path)))
