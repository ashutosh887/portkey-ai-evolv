# ML Pipeline Integration - Final Architecture

## Two-Job Hybrid Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    WEEKLY: Full Classification                   │
│                    (genome full-classify)                        │
│                                                                  │
│  Schedule: Every Sunday midnight (or manual trigger)             │
│                                                                  │
│  1. Load ALL prompts from DB                                     │
│  2. Embed all prompts (skip if embedding exists)                 │
│  3. Run HDBSCAN clustering on all embeddings                     │
│  4. Create/Update PromptFamily records                           │
│  5. Update centroids                                             │
│  6. Re-assign ALL prompts to new clusters                        │
│                                                                  │
│  Output: Accurate families with fresh centroids                  │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                 DAILY: Incremental Assignment                    │
│                 (genome classify-worker)                         │
│                                                                  │
│  Schedule: Every 10 min, runs if pending >= 500                  │
│                                                                  │
│  1. Count pending prompts (family_id IS NULL)                    │
│  2. If count < 500 → skip                                        │
│  3. Fetch 500 oldest unprocessed prompts                         │
│  4. Embed each prompt                                            │
│  5. Load centroids from DB                                       │
│  6. For each prompt:                                             │
│     - Find nearest centroid (cosine similarity)                  │
│     - If similarity >= 0.85 → assign to that family              │
│     - Else → assign to "Unclustered" family                      │
│  7. Update DB                                                    │
│                                                                  │
│  Output: Quick assignment using accurate centroids               │
└──────────────────────────────────────────────────────────────────┘
```

---

## Why Two Jobs?

| Job | Algorithm | Purpose | Cost |
|-----|-----------|---------|------|
| **Weekly Full** | HDBSCAN | Accurate clustering, discovers new patterns | High (all data) |
| **Daily Incremental** | Cosine similarity | Fast assignment to existing clusters | Low (per prompt) |

---

## Data Flow Diagram

```
                    ┌─────────────┐
                    │   PortKey   │
                    │    Logs     │
                    └──────┬──────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  INGESTION WORKER (existing)                                     │
│  Dedup → Normalize → Store in prompt_instances                   │
└──────────────────────────────────────────────────────────────────┘
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
┌─────────────────────────┐   ┌─────────────────────────┐
│  INCREMENTAL WORKER     │   │  WEEKLY FULL CLUSTER    │
│  (every 10 min)         │   │  (every Sunday)         │
│                         │   │                         │
│  Embed → Assign to      │   │  Embed ALL → HDBSCAN    │
│  nearest centroid       │   │  → Update families      │
└─────────────────────────┘   └─────────────────────────┘
              ↓                         ↓
              └────────────┬────────────┘
                           ↓
                    ┌─────────────┐
                    │  Database   │
                    │  - prompts  │
                    │  - families │
                    │  - centroids│
                    └─────────────┘
```

---

## Implementation Tasks

### Job 1: Weekly Full Classification
- [ ] Create `packages/ml_core/full_classifier.py`
- [ ] Use existing ML pipeline (embed + HDBSCAN)
- [ ] Store embeddings in `embedding_vector` column
- [ ] Create PromptFamily records from clusters
- [ ] Store centroids in `centroid_vector` column
- [ ] Update `family_id` on all prompts
- [ ] CLI: `genome full-classify`

### Job 2: Incremental Assignment Worker
- [ ] Create `packages/ml_core/incremental_worker.py`
- [ ] Check pending count >= 500
- [ ] Embed new prompts only
- [ ] Load centroids from DB
- [ ] Assign via cosine similarity
- [ ] Handle "unclustered" prompts (similarity < 0.85)
- [ ] CLI: `genome classify-worker --interval 10`

### Repository Updates
- [ ] `get_pending_count()` - count unclassified
- [ ] `get_all_centroids()` - family_id → centroid
- [ ] `create_family(name, centroid, members)` - new family
- [ ] `update_embedding_and_family(prompt_id, vector, family_id)`
- [ ] `get_all_embeddings()` - for weekly job

---

## CLI Commands

```bash
# Weekly full classification (manual or cron)
genome full-classify

# Start incremental worker (runs every 10 min)
genome classify-worker --interval 10 --batch-size 500
```

---

## Trade-offs Accepted

| Trade-off | Mitigation |
|-----------|------------|
| Weekly clusters may be stale by day 7 | Run full classify more often if needed |
| New prompts may be "unclustered" initially | Weekly job will cluster them properly |
| First run needs bootstrap | Run `full-classify` before starting incremental |

---

## Future Scaling: Kafka

When traffic > 100K prompts/day:

```python
# Producer (ingestion worker)
producer.send('prompts.new', prompt_id)

# Consumer (incremental worker)  
for message in consumer:
    prompt = repo.get_by_id(message.value)
    embedding = model.encode(prompt.normalized_text)
    family_id = find_nearest_family(embedding, centroids)
    repo.update(prompt.prompt_id, embedding, family_id)
```

Same logic, different trigger mechanism.
