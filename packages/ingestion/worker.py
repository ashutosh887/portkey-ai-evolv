"""
Portkey Ingestion Worker

Runs the ingestion loop periodically (e.g., every 10 minutes).
Tracks the last ingestion time in a local state file to avoid partial duplicates or missing data.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from packages.ingestion.portkey import PortKeyIngestor
from packages.storage.database import get_db
from packages.storage.repositories import PromptRepository

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("worker")

# Load environment variables
load_dotenv()

STATE_FILE = Path("ingestion_state.json")

def load_state() -> datetime:
    """Load last run time from state file or default to 24h ago"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                last_run = datetime.fromisoformat(data["last_run_time"])
                logger.info(f"Resuming from state: {last_run}")
                return last_run
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
    
    # Default: 24 hours ago
    return datetime.utcnow() - timedelta(hours=24)

def save_state(last_run: datetime):
    """Save the last run time to state file"""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"last_run_time": last_run.isoformat()}, f)
    except Exception as e:
        logger.error(f"Failed to save state: {e}")

async def run_worker(interval_minutes: int = 10):
    """
    Main worker loop.
    
    Args:
        interval_minutes: How often to run ingestion (default: 10)
    """
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        logger.error("PORTKEY_API_KEY environment variable is missing")
        return

    ingestor = PortKeyIngestor(api_key=api_key)
    logger.info(f"Starting Portkey Ingestion Worker (Interval: {interval_minutes} min)")

    while True:
        try:
            # 1. Determine time window
            last_run_time = load_state()
            current_run_time = datetime.utcnow()
            
            # 2. Run ingestion
            logger.info(f"Running ingestion from {last_run_time} to now")
            instances = await ingestor.run_ingestion(time_min=last_run_time)
            
            # 3. Handle results (save to DB with deduplication)
            if instances:
                logger.info(f"Processing {len(instances)} logs with deduplication...")
                db_gen = get_db()
                db = next(db_gen)
                try:
                    from packages.ingestion.dedup import SimHashDeduplicator, hamming_distance
                    
                    repo = PromptRepository(db)
                    # SimHash with Hamming distance threshold of 3 bits (~98% similar)
                    deduplicator = SimHashDeduplicator(threshold=3)
                    
                    # Load existing simhashes from DB (not in-memory!)
                    existing_simhashes = repo.get_all_simhashes()
                    for prompt_id, fingerprint in existing_simhashes:
                        if fingerprint is not None:
                            deduplicator._fingerprints[prompt_id] = fingerprint
                    logger.info(f"Loaded {deduplicator.size()} simhashes from database")
                    
                    saved_count = 0
                    exact_dup_count = 0
                    near_dup_count = 0
                    
                    for instance in instances:
                        # Skip empty prompts
                        if not instance.normalized_text:
                            continue
                        
                        # 1. Check exact duplicate by hash (SHA256)
                        if repo.get_by_hash(instance.dedup_hash):
                            exact_dup_count += 1
                            continue
                        
                        # 2. Check near-duplicate by SimHash (Hamming distance)
                        # Use the pre-computed simhash from the instance (stored as hex string)
                        is_near_dup = False
                        matching_id = None
                        distance = None
                        
                        if instance.simhash is not None:
                            instance_simhash_int = int(instance.simhash, 16)
                            for pid, existing_fp in deduplicator._fingerprints.items():
                                existing_fp_int = int(existing_fp, 16) if isinstance(existing_fp, str) else existing_fp
                                d = hamming_distance(instance_simhash_int, existing_fp_int)
                                if d <= deduplicator.threshold:
                                    is_near_dup = True
                                    matching_id = pid
                                    distance = d
                                    break
                        
                        if is_near_dup:
                            near_dup_count += 1
                            logger.info(f"Near-duplicate (Hamming={distance}): '{instance.normalized_text[:50]}...' matches {matching_id}")
                            continue
                        
                        # 3. Save to DB (simhash is stored automatically)
                        repo.create_from_instance(instance)
                        # Also add to in-memory index for this batch
                        if instance.simhash is not None:
                            deduplicator._fingerprints[instance.prompt_id] = instance.simhash
                        saved_count += 1
                    
                    logger.info(f"Deduplication complete: {saved_count} saved, {exact_dup_count} exact duplicates, {near_dup_count} near-duplicates skipped")
                finally:
                    # properly close the generator-yielded session
                    try:
                        next(db_gen)
                    except StopIteration:
                        pass
            else:
                logger.info("No new logs found.")

            # 4. Update state only if successful
            save_state(current_run_time)
            
        except Exception as e:
            logger.error(f"Error in ingestion loop: {e}")
            # Don't update state on error, so we retry next time
        
        # 5. Sleep
        logger.info(f"Sleeping for {interval_minutes} minutes...")
        await asyncio.sleep(interval_minutes * 60)

if __name__ == "__main__":
    try:
        asyncio.run(run_worker(interval_minutes=10))
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
