"""
Full Classifier - Weekly HDBSCAN Clustering Job

Uses EXISTING ML pipeline components:
- packages/ml_core/embedding.py - for embeddings
- packages/ml_core/clustering.py - for HDBSCAN clustering

Integrates with DB:
1. Load all prompts from DB
2. Embed using existing create_embeddings()
3. Cluster using existing cluster_hdbscan()
4. Save results back to DB
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

from packages.ml_core.config import MLConfig
from packages.ml_core.embedding import create_embeddings
from packages.ml_core.clustering import cluster_hdbscan, compute_cluster_centroids
from packages.storage.database import get_db
from packages.storage.repositories import PromptRepository, FamilyRepository
from packages.ml_core.template_generator import TemplateGenerator

logger = logging.getLogger(__name__)


def generate_family_name(sample_prompts: List[str], cluster_id: int) -> str:
    """
    Generate a meaningful family name using LLM based on sample prompts from the cluster.
    
    Args:
        sample_prompts: List of sample prompts from the cluster
        cluster_id: Cluster ID (used as fallback)
    
    Returns:
        A short, descriptive family name
    """
    import httpx
    
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key or not sample_prompts:
        return f"Cluster-{cluster_id}"
    
    try:
        # Take first 3 prompts as samples
        samples = sample_prompts[:3]
        samples_text = "\n".join([f"- {p[:100]}..." if len(p) > 100 else f"- {p}" for p in samples])
        
        prompt = f"""Based on these sample prompts from a cluster, generate a SHORT (2-4 words) category name that describes what these prompts have in common.

Sample prompts:
{samples_text}

Requirements:
- 2-4 words maximum
- Descriptive and semantic (e.g., "Code Generation", "Email Writing", "Data Analysis")
- Title case
- No quotes or punctuation

Category name:"""

        response = httpx.post(
            "https://api.portkey.ai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "x-portkey-api-key": api_key,
                "x-portkey-provider": "@openai",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 20,
                "temperature": 0.3,
            },
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            name = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if name and len(name) < 50:
                return name
    except Exception as e:
        logger.warning(f"LLM naming failed for cluster {cluster_id}: {e}")
    
    return f"Cluster-{cluster_id}"


class FullClassifier:
    """
    Weekly full classification job using EXISTING ML pipeline.
    
    This job:
    - Loads ALL prompts from database
    - Uses existing create_embeddings() function
    - Uses existing cluster_hdbscan() function
    - Creates/updates PromptFamily records in DB
    """
    
    def __init__(self, config: Optional[MLConfig] = None):
        self.config = config or MLConfig.from_env()
        logger.info(f"Using embedding model: {self.config.embedding_model}")
    
    async def run(self) -> Dict:
        """
        Run full classification pipeline.
        
        Returns:
            Dict with statistics about the run
        """
        logger.info("Starting Full Classification Job...")
        stats = {
            "total_prompts": 0,
            "embedded": 0,
            "clusters_created": 0,
            "prompts_assigned": 0,
            "unclustered": 0
        }
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            prompt_repo = PromptRepository(db)
            family_repo = FamilyRepository(db)
            
            # Step 1: Load all prompts from DB
            all_prompts = prompt_repo.get_all()
            stats["total_prompts"] = len(all_prompts)
            logger.info(f"Loaded {len(all_prompts)} prompts from database")
            
            if len(all_prompts) < 2:
                logger.warning("Not enough prompts for clustering (need at least 2)")
                return stats
            
            # Step 2: Build prompts dict for existing pipeline
            # Format: {prompt_id: normalized_text}
            prompts_dict: Dict[str, str] = {}
            existing_embeddings: Dict[str, List[float]] = {}
            
            for prompt in all_prompts:
                if prompt.normalized_text:
                    prompts_dict[prompt.prompt_id] = prompt.normalized_text
                    # Check if already embedded
                    if prompt.embedding_vector:
                        existing_embeddings[prompt.prompt_id] = prompt.embedding_vector
            
            logger.info(f"Found {len(existing_embeddings)} existing embeddings")
            
            # Step 3: Embed prompts using EXISTING create_embeddings()
            # Only embed prompts that don't have embeddings yet
            prompts_to_embed = {
                pid: text for pid, text in prompts_dict.items()
                if pid not in existing_embeddings
            }
            
            if prompts_to_embed:
                logger.info(f"Embedding {len(prompts_to_embed)} new prompts using {self.config.embedding_model}...")
                new_embeddings = create_embeddings(
                    prompts_to_embed,
                    model_name=self.config.embedding_model,
                    cache_dir=self.config.cache_dir,
                    portkey_api_key=self.config.portkey_api_key,
                    portkey_virtual_key=self.config.portkey_virtual_key
                )
                
                # Save new embeddings to DB
                for prompt_id, embedding in new_embeddings.items():
                    prompt_repo.update_embedding(prompt_id, embedding)
                    stats["embedded"] += 1
                
                # Merge embeddings
                all_embeddings = {**existing_embeddings, **new_embeddings}
            else:
                all_embeddings = existing_embeddings
                logger.info("All prompts already embedded, using existing embeddings")
            
            logger.info(f"Total embeddings: {len(all_embeddings)}")
            print(f"✓ Embeddings ready: {len(all_embeddings)}")
            
            # Step 4: Cluster using EXISTING cluster_hdbscan()
            print("Starting HDBSCAN clustering...")
            logger.info("Running HDBSCAN clustering...")
            prompt_to_cluster, cluster_to_prompts, prompt_to_confidence = cluster_hdbscan(
                all_embeddings,
                min_cluster_size=self.config.min_cluster_size,
                min_samples=self.config.min_samples,
                cluster_selection_epsilon=self.config.cluster_selection_epsilon
            )
            
            num_clusters = len([c for c in cluster_to_prompts.keys() if c != -1])
            logger.info(f"Found {num_clusters} clusters")
            print(f"✓ HDBSCAN complete: {num_clusters} clusters found")
            
            # Step 5: Compute centroids using EXISTING function
            print("Computing centroids...")
            centroids = compute_cluster_centroids(all_embeddings, cluster_to_prompts)
            print(f"✓ Centroids computed: {len(centroids)}")
            
            # Step 6: Create/Update PromptFamily records in DB
            print("Creating PromptFamily records...")
            cluster_id_to_family_id: Dict[int, str] = {}
            
            for cluster_id, member_ids in cluster_to_prompts.items():
                if cluster_id == -1:
                    # Noise points
                    stats["unclustered"] = len(member_ids)
                    continue
                
                # Get sample prompts from this cluster for LLM naming
                sample_prompts = []
                for pid in member_ids[:5]:  # Take up to 5 samples
                    prompt = prompt_repo.get_by_id(pid)
                    if prompt and prompt.normalized_text:
                        sample_prompts.append(prompt.normalized_text)
                
                # Generate meaningful name using LLM
                family_name = generate_family_name(sample_prompts, cluster_id)
                print(f"  Creating family '{family_name}' ({len(member_ids)} members)...")
                
                # Create or update family in DB
                family_id = family_repo.create_or_update_family(
                    cluster_id=cluster_id,
                    centroid=centroids.get(cluster_id),
                    member_count=len(member_ids),
                    family_name=family_name
                )
                cluster_id_to_family_id[cluster_id] = family_id
                stats["clusters_created"] += 1
            
            print(f"✓ Created {len(cluster_id_to_family_id)} families")
            
            # Step 7: Update prompt family assignments in DB
            print(f"Assigning {len(prompt_to_cluster)} prompts to families...")
            assigned = 0
            for prompt_id, cluster_id in prompt_to_cluster.items():
                if cluster_id == -1:
                    prompt_repo.update_family(prompt_id, None)
                else:
                    family_id = cluster_id_to_family_id.get(cluster_id)
                    if family_id:
                        prompt_repo.update_family(prompt_id, family_id)
                        stats["prompts_assigned"] += 1
                        assigned += 1
                        if assigned % 10 == 0:
                            print(f"  Assigned {assigned} prompts...")
            
            print(f"✓ Assigned {stats['prompts_assigned']} prompts to families")
            
            # Step 8: Generate/Update Templates
            print("Generating templates for families...")
            try:
                template_generator = TemplateGenerator(db)
                updated_count = await template_generator.process_all_families()
                print(f"✓ Templates processed: {updated_count} created/updated")
            except Exception as e:
                logger.error(f"Template generation failed: {e}")
                print(f"❌ Template generation failed: {e}")

            logger.info(f"Classification complete: {stats}")
            return stats
            
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass


def run_full_classification():
    """Entry point for CLI command."""
    logging.basicConfig(level=logging.INFO)
    classifier = FullClassifier()
    return asyncio.run(classifier.run())
