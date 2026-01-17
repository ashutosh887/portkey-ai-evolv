# Implementation Details - Tasks 1-4

This document consolidates all implementation details from Tasks 1-4.

---

## Task 1: Phase 1.1 & 1.2 — Database and Processing Service

### Phase 1.1: Database Initialization

**`scripts/init_db.py`**
- Imports fixed to use `PromptInstance`, `PromptFamily`, `Template` from `packages.storage.models`
- Running it creates `prompt_instances`, `prompt_families`, `templates`

**`packages/core/models.py`**
- Added: `PromptStructure`, `PromptVariables`, `PromptInstructions`, `PromptDNA`, `CanonicalTemplate`
- These are used by `dna_extractor`, `clustering`, `llm`, and `processing`

### Phase 1.2: Processing Service Integration

**`packages/storage/repositories.py`**
- `PromptRepository.create_from_dna(dna, original_text_override=None)` — create prompt from `PromptDNA`, optionally keep raw user text
- `PromptRepository.update_embedding(prompt_id, embedding)` — set `embedding_vector` for batch-fill
- `FamilyRepository.create_family(family_id, family_name, description, member_count, centroid_vector)` — create family row
- `FamilyRepository.create_template(family_id, template_text, slots, quality_score)` — create template row

**`packages/core/processing.py`**
- `LineageRepository` removed from constructor and imports
- `process_raw_prompt(raw_text, metadata)` — normalize → dedup by hash → extract DNA → embed → `create_from_dna(..., original_text_override=raw_text)`
- `process_batch(limit)` — load pending, fill missing embeddings, cluster (HDBSCAN), create families + templates, assign `family_id`
- `_model_to_dna(model)` helper to build `PromptDNA` from a `PromptInstance` ORM row
- `classify_new_prompt(prompt_dna)` updated to use `family_id` and `_model_to_dna` (no lineage yet)

**CLI**
- `genome add "prompt text"` — calls `process_raw_prompt` (for quick testing)
- `genome run [--limit 100]` — calls `process_batch(limit)`

**`packages/core/__init__.py`**
- Exports: `PromptDNA`, `CanonicalTemplate`, `ProcessingService`

### Files Modified
- `packages/core/models.py` - Added domain models
- `packages/core/processing.py` - Rewritten: no LineageRepository; process_raw_prompt; process_batch; _model_to_dna; classify_new_prompt fixed
- `packages/core/__init__.py` - Added exports
- `packages/storage/repositories.py` - Added create_from_dna, update_embedding; create_family, create_template
- `scripts/init_db.py` - Fixed imports
- `apps/cli/main.py` - Added `genome add "text"`; `genome run` implemented

---

## Task 2: Phase 2 — API Endpoints

### API Endpoints Implemented

#### Ingestion Endpoints
- **`POST /ingest`**
  - Accepts file upload (JSON, CSV, or TXT)
  - Parses file, extracts prompts, processes through `ProcessingService.process_raw_prompt()`
  - Returns: `{saved, duplicates, errors, total_rows}`
  - Handles multiple formats: `{"text": "..."}`, `{"prompt": "..."}`, `{"content": "..."}`, or plain text lines

- **`POST /ingest/portkey`**
  - Triggers Portkey ingestion for last 24 hours
  - Uses `PortKeyIngestor.run_ingestion()`
  - Returns: `{ingested, total_from_portkey}`
  - Requires `PORTKEY_API_KEY` in environment

#### Family Endpoints
- **`GET /families`**
  - List all families with pagination
  - Query params: `limit` (default: 20), `offset` (default: 0), `sort` (created_at, member_count, family_name)
  - Returns: `{families: [...], total, limit, offset}`

- **`GET /families/{family_id}`**
  - Get family details including members and template
  - Returns: `{family_id, family_name, description, member_count, created_at, members: [...], template: {...}}`
  - 404 if family not found

- **`GET /families/{family_id}/members`**
  - List all prompts in a family with pagination
  - Query params: `limit`, `offset`
  - Returns: `{members: [...], total, limit, offset}`

#### Template Endpoints
- **`GET /families/{family_id}/template`**
  - Get canonical template for a family
  - Returns: `{template_id, template_text, slots, template_version, quality_score, created_at}`
  - 404 if template not found

- **`POST /families/{family_id}/template/extract`**
  - Trigger template extraction using LLM
  - Returns: `{status, template_text, variables}` or `{status: "already_exists", ...}` if template exists

#### Prompt Endpoints
- **`GET /prompts`**
  - List prompts with pagination
  - Query params: `family_id` (optional filter), `limit`, `offset`
  - Returns: `{prompts: [...], total, limit, offset}`

- **`GET /prompts/{prompt_id}`**
  - Get full prompt details including DNA structure and family
  - Returns: `{prompt_id, original_text, normalized_text, family_id, created_at, dna: {...}, family: {...}}`
  - 404 if prompt not found

- **`GET /prompts/{prompt_id}/lineage`**
  - Get evolution chain (placeholder for Phase 5)
  - Returns: `{prompt_id, lineage: [], message: "Lineage tracking not yet implemented"}`

#### Processing Endpoints
- **`POST /process`**
  - Trigger batch processing of pending prompts
  - Query param: `limit` (default: 100, max: 1000)
  - Returns: `{status, processed, families_created, families_updated}`

- **`GET /process/status`**
  - Get processing queue status
  - Returns: `{pending_count, last_processed_at}`

#### Statistics Endpoint
- **`GET /stats`**
  - System-wide statistics
  - Returns: prompts (total, pending, processed), families (total, average_size), templates (extracted), duplicates_detected, last_ingestion

### Repository Enhancements
- **`PromptRepository`**: Added `count_all()`, `count_pending()`, `get_paginated(family_id, limit, offset)`
- **`FamilyRepository`**: Added `count_all()`, `get_template_by_family(family_id)`
- **`TemplateRepository`** (new class): `get_by_family(family_id)`, `count_all()`

### Files Modified
- `apps/api/main.py` - Complete rewrite: all Phase 2 endpoints implemented
- `packages/storage/repositories.py` - Added count methods, pagination, TemplateRepository
- `packages/storage/__init__.py` - Export TemplateRepository

---

## Task 3: Phase 3 — CLI Commands

### Ingestion Commands
- **`genome ingest <file> [--source file]`**
  - Ingests prompts from file (JSON, CSV, or TXT)
  - Uses `packages.ingestion.files.ingest_from_file()`
  - Processes through `ProcessingService.process_raw_prompt()`
  - Shows stats: saved, duplicates, errors

- **`genome ingest <file> --source portkey`**
  - Triggers Portkey ingestion for last 24 hours
  - Uses `PortKeyIngestor.run_ingestion()`
  - Shows progress and results
  - Requires `PORTKEY_API_KEY` in environment

### Processing Commands
- **`genome run [--limit N]`**
  - Process pending prompts
  - Calls `ProcessingService.process_batch()`
  - Shows: processed count, families created

### Family Commands
- **`genome families [--limit N] [--format table|json]`**
  - Lists all families in table format
  - Columns: ID, Name, Members, Created
  - Supports `--limit` and `--format json`
  - Sorted by creation date (newest first)

- **`genome family <family_id>`**
  - Shows family details
  - Displays: name, description, member count, created date
  - Lists member prompts (preview, up to 10)
  - Shows template if available

### Template Commands
- **`genome template <family_id> [--extract]`**
  - Displays canonical template
  - Shows variables and example values
  - If template not extracted and `--extract` flag provided, extracts template using LLM
  - Shows quality score if available

### Evolution Commands
- **`genome evolve <prompt_id>`**
  - Shows evolution chain (placeholder for Phase 5)
  - Displays prompt info and family assignment
  - Message: "Lineage tracking not yet implemented (Phase 5)"

### Statistics Command
- **`genome stats [--format table|json]`**
  - Displays comprehensive statistics
  - Format: table (default) or JSON
  - Includes all metrics: prompts (total, pending, processed), families (total, average size), templates (extracted count), last ingestion time

### Files Modified
- `apps/cli/main.py` - Complete implementation of all CLI commands

---

## Task 4: Phase 4 — LLM Integration

### Complete LLM Client
- **`LLMClient.extract_template()`**
  - Uses Portkey SDK (`portkey_ai.Portkey`) to call GPT-4/Claude
  - Formats prompt cluster for LLM with structured prompt
  - Parses JSON response (handles JSON extraction from text)
  - Handles errors gracefully with fallback

- **`LLMClient.generate_explanation()`**
  - Generates human-readable explanation using Portkey SDK
  - Returns explanation string
  - Handles errors with fallback

### Template Extraction Integration
- **Connected to processing pipeline**
  - `ProcessingService` uses real LLM by default (`use_mock_llm=False`)
  - Automatically falls back to `MockLLMClient` if:
    - `PORTKEY_API_KEY` not configured
    - `portkey-ai` package not available
    - LLM call fails after retries
  - Stores template in database
  - Handles failures gracefully

### Error Handling
- **Retry logic**
  - 3 attempts with exponential backoff (2^attempt seconds)
  - Logs warnings on retries
  - Logs errors on final failure

- **Fallback to mock**
  - If Portkey fails or unavailable, uses `MockLLMClient`
  - Logs warning when fallback is used
  - Processing continues without interruption

### Implementation Details
- **Portkey SDK Integration**
  - Uses `portkey_ai.Portkey` client
  - Supports models: `gpt-4o-mini`, `gpt-4`, `gpt-3.5-turbo`, `claude-3-haiku`, `claude-3-sonnet`
  - Default model: `gpt-4o-mini`
  - Wraps sync Portkey calls in `asyncio.to_thread()` for async compatibility

- **Template Extraction Prompt**
  - Structured prompt asking LLM to identify common structure, variables, and create canonical template
  - Output format: JSON with `template`, `variables`, `common_intent`, `explanation`

- **Explanation Prompt**
  - Concise 2-3 sentence explanation of why prompts form a family
  - Focuses on common intent, shared structure, similar use cases

### Files Modified
- `packages/llm/client.py` - Complete implementation: extract_template(), generate_explanation(), retry logic, fallback
- `packages/core/processing.py` - Added fallback methods, changed default to `use_mock_llm=False`
- `apps/api/main.py` - Changed to use real LLM by default (`use_mock_llm=False`)
- `apps/cli/main.py` - Changed to use real LLM by default, added fallback in template extraction

---

## Summary

### Completed Features
- ✅ Database models and schema
- ✅ DNA extraction (structure, variables, instructions)
- ✅ Embedding generation (sentence-transformers)
- ✅ Clustering (HDBSCAN)
- ✅ Processing service (single + batch)
- ✅ Repository pattern (CRUD operations)
- ✅ REST API endpoints (all Phase 2 endpoints)
- ✅ CLI commands (all Phase 3 commands)
- ✅ LLM integration (Portkey SDK with retry and fallback)
- ✅ Portkey ingestion worker
- ✅ Deduplication (SHA-256, SimHash)
- ✅ Web log generator (Next.js app)

### Not Yet Implemented
- ❌ Lineage tracking (Phase 5)
- ❌ Web dashboard (Phase 6)
- ❌ Evolution visualization (Phase 5)

---

## Testing Instructions

### Task 1
```bash
uv sync
uv run python scripts/init_db.py
uv run genome add "Summarize this document in 3 sentences"
uv run genome run
```

### Task 2
```bash
uv run uvicorn apps.api.main:app --reload
# Visit http://localhost:8000/docs
curl http://localhost:8000/stats
curl -X POST http://localhost:8000/ingest -F "file=@examples/prompt.csv"
curl -X POST http://localhost:8000/process
```

### Task 3
```bash
uv run genome ingest examples/prompt.csv
uv run genome run
uv run genome families
uv run genome family <family_id>
uv run genome template <family_id>
uv run genome stats
```

### Task 4
```bash
# Add PORTKEY_API_KEY to .env (optional, will use mock if not set)
uv run genome run
uv run genome template <family_id> --extract
```

---

## Configuration

### Environment Variables
- `DATABASE_URL` - Database connection string (default: `sqlite:///./data/genome.db`)
- `PORTKEY_API_KEY` - Portkey API key (for ingestion and LLM)
- `PORTKEY_VIRTUAL_KEY` - Portkey virtual key (optional)

### Default Behavior
- Real LLM used by default if `PORTKEY_API_KEY` configured
- Automatic fallback to MockLLMClient if LLM unavailable
- Processing continues without interruption on LLM failures
