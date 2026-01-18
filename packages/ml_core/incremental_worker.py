"""
Incremental Classification Worker

Uses EXISTING ML pipeline components:
- packages/ml_core/embedding.py - for embeddings
- packages/ml_core/config.py - for configuration

Runs every 10 minutes to assign new prompts to existing families:
1. Check if classified >= 500 (bootstrap)
2. Check if pending prompts >= batch_size
3. Embed new prompts using existing EmbeddingModel
4. Load family centroids from DB
5. Assign to nearest family (cosine similarity >= threshold)
6. Update DB
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from packages.ml_core.config import MLConfig
from packages.ml_core.embedding import EmbeddingModel
from packages.storage.database import get_db
from packages.storage.repositories import PromptRepository, FamilyRepository
from packages.ml_core.template_generator import TemplateGenerator

logger = logging.getLogger(__name__)


class IncrementalWorker:
    """
    Incremental classification worker using EXISTING ML pipeline.
    
    Assigns new prompts to existing families using cosine similarity
    with centroids computed from weekly full classification.
    """
    
    def __init__(
        self,
        config: Optional[MLConfig] = None,
        similarity_threshold: float = 0.60,  # Lowered from 0.85 for better matching
        batch_size: int = 500
    ):
        self.config = config or MLConfig.from_env()
        self.embedding_model = EmbeddingModel(
            model_name=self.config.embedding_model,
            cache_dir=self.config.cache_dir,
            portkey_api_key=self.config.portkey_api_key,
            portkey_virtual_key=self.config.portkey_virtual_key
        )
        self.threshold = similarity_threshold
        self.batch_size = batch_size
        logger.info(f"Initialized IncrementalWorker (model={self.config.embedding_model}, threshold={similarity_threshold}, batch={batch_size})")
    
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string using existing EmbeddingModel."""
        return self.embedding_model.embed(text)
    
    def find_nearest_family(
        self,
        embedding: List[float],
        centroids: Dict[str, List[float]]
    ) -> Tuple[Optional[str], float]:
        """
        Find the nearest family for an embedding.
        
        Args:
            embedding: Prompt embedding vector
            centroids: Dict of family_id -> centroid vector
        
        Returns:
            Tuple of (family_id or None, similarity score)
        """
        if not centroids:
            return None, 0.0
        
        embedding_arr = np.array([embedding])
        best_family = None
        best_similarity = -1.0
        
        for family_id, centroid in centroids.items():
            centroid_arr = np.array([centroid])
            similarity = cosine_similarity(embedding_arr, centroid_arr)[0][0]
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_family = family_id
        
        if best_similarity >= self.threshold:
            return best_family, best_similarity
        else:
            return None, best_similarity
    
    async def run_cycle(self) -> Dict:
        """
        Run one cycle of incremental classification.
        
        Returns:
            Dict with statistics about the run
        """
        stats = {
            "pending_count": 0,
            "processed": 0,
            "assigned": 0,
            "unclustered": 0,
            "skipped": False,
            "templates_updated": 0
        }
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            prompt_repo = PromptRepository(db)
            family_repo = FamilyRepository(db)
            
            # Step 0: Bootstrap check - if not enough classified, run full classification
            classified_count = prompt_repo.get_classified_count()
            total_count = len(prompt_repo.get_all())
            
            # Bootstrap threshold: 50 for testing (increase to 500 for production)
            BOOTSTRAP_THRESHOLD = 50
            if classified_count < BOOTSTRAP_THRESHOLD:
                print(f"\n🚀 Bootstrap mode: {classified_count}/{BOOTSTRAP_THRESHOLD} classified")
                print("Running full HDBSCAN classification...")
                
                # Import and run full classification
                from packages.ml_core.full_classifier import FullClassifier
                classifier = FullClassifier(config=self.config)
                full_stats = await classifier.run()
                
                stats["mode"] = "full_classification"
                stats["processed"] = full_stats.get("prompts_assigned", 0)
                stats["assigned"] = full_stats.get("prompts_assigned", 0)
                stats["unclustered"] = full_stats.get("unclustered", 0)
                stats["clusters_created"] = full_stats.get("clusters_created", 0)
                
                print(f"\n✅ Bootstrap classification complete!")
                print(f"   Clusters: {stats['clusters_created']}")
                print(f"   Assigned: {stats['assigned']}")
                print(f"   Unclustered: {stats['unclustered']}")
                
                logger.info(f"Bootstrap complete: {stats}")
                return stats
            
            # Incremental mode - enough prompts are classified
            print(f"\n📊 Incremental mode: {classified_count} classified prompts")
            
            # Step 1: Check pending count
            pending_count = prompt_repo.get_pending_count()
            stats["pending_count"] = pending_count
            print(f"   Pending prompts: {pending_count}")
            
            if pending_count < self.batch_size:
                print(f"   ⏭️  Not enough pending ({pending_count}/{self.batch_size}), skipping...")
                logger.info(f"Not enough pending prompts ({pending_count}/{self.batch_size}), skipping cycle")
                stats["skipped"] = True
                return stats
            
            # Step 2: Fetch batch of pending prompts
            print(f"   Fetching {self.batch_size} prompts for processing...")
            pending_prompts = prompt_repo.get_pending(limit=self.batch_size)
            print(f"   Fetched {len(pending_prompts)} prompts")
            logger.info(f"Processing {len(pending_prompts)} prompts")
            
            # Step 3: Load centroids from DB
            print(f"   Loading family centroids...")
            centroids = family_repo.get_all_centroids()
            print(f"   Loaded {len(centroids)} centroids")
            logger.info(f"Loaded {len(centroids)} family centroids")
            
            if not centroids:
                print("   ❌ No centroids found! Run full-classify first.")
                logger.warning("No family centroids found. Run full-classify first!")
                stats["unclustered"] = len(pending_prompts)
                return stats
            
            print(f"   Processing prompts...")
            
            # Step 4: Process each prompt
            for i, prompt in enumerate(pending_prompts):
                if not prompt.normalized_text:
                    continue
                
                print(f"   [{i+1}/{len(pending_prompts)}] Embedding prompt...")
                
                # Embed prompt
                embedding = self.embed_text(prompt.normalized_text)
                
                # Find nearest family
                family_id, similarity = self.find_nearest_family(embedding, centroids)
                
                # Update prompt
                prompt_repo.update_embedding_and_family(
                    prompt_id=prompt.prompt_id,
                    embedding=embedding,
                    family_id=family_id
                )
                
                if family_id:
                    stats["assigned"] += 1
                    print(f"   ✓ Assigned to family (similarity: {similarity:.2f})")
                else:
                    stats["unclustered"] += 1
                    print(f"   → No match (best similarity: {similarity:.2f})")
                
                stats["processed"] += 1
            
            # Update family member counts
            print(f"\n✅ Incremental classification complete!")
            print(f"   Processed: {stats['processed']}")
            print(f"   Assigned: {stats['assigned']}")
            print(f"   Unclustered: {stats['unclustered']}")
            
            family_repo.update_all_member_counts()
            
            # Step 5: Update templates for affected families
            if stats["assigned"] > 0:
                print("   Checking templates for updates...")
                template_generator = TemplateGenerator(db)
                affected_families = set()
                
                # Re-query recently updated prompts to find affected families
                # (Slightly inefficient but cleaner than tracking manually above)
                # Actually, we can just fetch all families that were modified?
                # For now let's use a simpler approach - just iterate all families
                # Or better, we should have tracked them. 
                # Let's rely on TemplateGenerator logic which is fast enough to check.
                # But to be safe, let's just run process_all_families() as it handles checks efficiently.
                # Or even better, let's process ONLY families that have > 2 members.
                
                updated_count = await template_generator.process_all_families()
                stats["templates_updated"] = updated_count
                if updated_count > 0:
                    print(f"   ✓ Updated {updated_count} templates")

            logger.info(f"Cycle complete: {stats}")
            return stats
            
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass


async def run_worker(interval_minutes: int = 10, batch_size: int = 500):
    """
    Main worker loop.
    
    Args:
        interval_minutes: How often to run classification (default: 10)
        batch_size: Minimum prompts to trigger processing (default: 500)
    """
    worker = IncrementalWorker(batch_size=batch_size)
    logger.info(f"Starting Incremental Classification Worker (interval={interval_minutes}min, batch={batch_size})")
    
    while True:
        try:
            stats = await worker.run_cycle()
            
            if not stats["skipped"]:
                logger.info(f"Processed: {stats['assigned']} assigned, {stats['unclustered']} unclustered")
            
        except Exception as e:
            logger.error(f"Error in classification cycle: {e}")
        
        # Sleep until next cycle
        logger.info(f"Sleeping for {interval_minutes} minutes...")
        await asyncio.sleep(interval_minutes * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())
