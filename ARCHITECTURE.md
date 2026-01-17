# Architecture Documentation

## System Overview

Evolv (Prompt Genome Project) is a monorepo-based system that ingests prompts from various sources, extracts their structural and semantic "DNA", clusters them into families, synthesizes canonical templates, and tracks their evolution over time.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EVOLV SYSTEM                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    INGESTION LAYER                            │ │
│  │  • Portkey Logs API                                            │ │
│  │  • File Uploads (JSON, CSV, TXT)                              │ │
│  │  • Git Repository Scanning                                      │ │
│  │  • Normalization & Deduplication                               │ │
│  └───────────────────────┬────────────────────────────────────────┘ │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                  DNA EXTRACTION ENGINE                         │ │
│  │  • Structural Parsing (system/user/assistant)                 │ │
│  │  • Variable Detection ({{var}}, {var}, $VAR, etc.)            │ │
│  │  • Instruction Extraction (tone, format, constraints)         │ │
│  │  • Embedding Generation (sentence-transformers/OpenAI)       │ │
│  └───────────────────────┬────────────────────────────────────────┘ │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                CLUSTERING ENGINE                               │ │
│  │  • Cosine Similarity Matrix                                    │ │
│  │  • HDBSCAN Clustering                                          │ │
│  │  • Confidence Scoring                                          │ │
│  │  • Family Assignment                                           │ │
│  └───────────────────────┬────────────────────────────────────────┘ │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              TEMPLATE SYNTHESIZER (LLM)                       │ │
│  │  • LLM-based Template Extraction                               │ │
│  │  • Variable Slot Identification                                │ │
│  │  • Explanation Generation                                      │ │
│  │  • Portkey Integration with Fallbacks                           │ │
│  └───────────────────────┬────────────────────────────────────────┘ │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                EVOLUTION TRACKER                               │ │
│  │  • New Prompt Classification                                    │ │
│  │  • Mutation Detection                                          │ │
│  │  • Lineage Graph Construction                                  │ │
│  │  • Drift Alerts                                                │ │
│  └───────────────────────┬────────────────────────────────────────┘ │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    STORAGE LAYER                               │ │
│  │  • SQLite Database                                             │ │
│  │  • Repository Pattern                                          │ │
│  │  • Prompt, Family, Lineage Models                             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   FastAPI REST    │  │   Typer CLI       │  │   Next.js    │  │
│  │   Endpoints       │  │   Commands         │  │   Log Gen    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              LOG GENERATION (Next.js App)                    │ │
│  │  • Manual prompt generation                                   │ │
│  │  • Auto-generation (configurable rate)                        │ │
│  │  • Real-time log display                                      │ │
│  │  • Portkey SDK integration                                    │ │
│  └───────────────────────┬──────────────────────────────────────┘ │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              PORTKEY OBSERVABILITY                             │ │
│  │  • Logs stored in Portkey                                     │ │
│  │  • Available via Portkey API                                  │ │
│  └───────────────────────┬──────────────────────────────────────┘ │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              EVOLV INGESTION                                  │ │
│  │  • Fetch logs from Portkey API                                │ │
│  │  • Process through Evolv pipeline                             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Prompt Ingestion Flow

```
┌─────────────┐
│   Source    │  (Portkey/File/Git)
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   Ingester      │
│  • Parse        │
│  • Normalize    │
│  • Deduplicate  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  DNA Extractor   │
│  • Structure     │
│  • Variables     │
│  • Instructions  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Embedding       │
│  Service         │
│  • Generate      │
│    embeddings    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Storage        │
│  • Save Prompt   │
│  • Queue for     │
│    processing    │
└─────────────────┘
```

### 2. Clustering & Family Detection Flow

```
┌─────────────────┐
│  Pending        │
│  Prompts         │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Load Prompts   │
│  with           │
│  Embeddings     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Similarity     │
│  Matrix         │
│  Computation    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  HDBSCAN        │
│  Clustering     │
│  • min_size=2   │
│  • epsilon=0.15 │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Family         │
│  Assignment     │
│  • Create new   │
│  • Assign to    │
│    existing     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Template       │
│  Synthesis      │
│  (LLM)          │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Update         │
│  Database       │
└─────────────────┘
```

### 3. Evolution Tracking Flow

```
┌─────────────────┐
│  New Prompt     │
│  Arrives        │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Extract DNA    │
│  & Embedding    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Load Existing  │
│  Families       │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Compute        │
│  Similarity     │
│  to Families    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Classify:      │
│  • exact_match   │
│  • variant       │
│  • new_family    │
└──────┬──────────┘
       │
       ├─── exact_match ───► Update Family
       │
       ├─── variant ───────► Create Lineage Link
       │
       └─── new_family ─────► Create New Family
```

### 4. Template Extraction Flow

```
┌─────────────────┐
│  Prompt Family  │
│  (Cluster)      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Format Prompts │
│  for LLM        │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  LLM Client     │
│  (Portkey)      │
│  • GPT-4        │
│  • Claude       │
│  • Fallback     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Parse LLM      │
│  Response       │
│  • Template     │
│  • Variables    │
│  • Explanation  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Save Template  │
│  to Family      │
└─────────────────┘
```

---

## Component Details

### 1. Ingestion Layer (`packages/ingestion/`)

**Responsibilities:**
- Parse data from multiple sources
- Normalize text (whitespace, encoding)
- Deduplicate using hash-based detection
- Extract metadata (source, timestamp, user_id)

**Key Functions:**
- `ingest_from_file()` - File-based ingestion
- `ingest_from_portkey()` - Portkey API ingestion
- `normalize_text()` - Text normalization
- `compute_hash()` - Deduplication hashing

**Data Flow:**
```
Raw Data → Parser → Normalizer → Hash Check → Metadata Extraction → PromptDNA
```

### 2. DNA Extraction (`packages/dna_extractor/`)

**Responsibilities:**
- Parse prompt structure (system/user/assistant)
- Detect variables ({{var}}, {var}, $VAR, etc.)
- Extract instructions (tone, format, constraints)
- Generate semantic embeddings

**Key Functions:**
- `extract_dna()` - Main extraction function
- `EmbeddingService.generate_embedding()` - Embedding generation
- `_extract_structure()` - Structural parsing
- `_detect_variables()` - Variable pattern matching
- `_extract_instructions()` - Instruction extraction

**Variable Patterns:**
- `{{variable}}` - Double braces
- `{variable}` - Single braces
- `$VARIABLE` - Dollar prefix
- `[PLACEHOLDER]` - Brackets
- `<input>` - Angle brackets
- `__SLOT__` - Double underscores

### 3. Clustering Engine (`packages/clustering/`)

**Responsibilities:**
- Compute similarity matrices
- Run HDBSCAN clustering
- Assign prompts to families
- Compute confidence scores

**Key Functions:**
- `cluster_prompts()` - Main clustering function
- `compute_similarity_matrix()` - Cosine similarity
- `compute_confidence()` - Confidence scoring
- `classify_new_prompt()` - New prompt classification
- `detect_mutation_type()` - Mutation detection

**Configuration:**
```python
CLUSTERING_CONFIG = {
    "min_cluster_size": 2,
    "min_samples": 1,
    "metric": "cosine",
    "cluster_selection_epsilon": 0.15,
}

CONFIDENCE_THRESHOLDS = {
    "auto_merge": 0.85,      # Auto-assign to family
    "suggest_merge": 0.70,   # Suggest for review
    "new_family": 0.50,      # Consider new family
}
```

### 4. LLM Client (`packages/llm/`)

**Responsibilities:**
- Template extraction via LLM
- Explanation generation
- Portkey integration with fallbacks
- Mock implementation for development

**Key Classes:**
- `LLMClient` - Production Portkey client
- `MockLLMClient` - Development mock

**Template Extraction Prompt:**
```
You are analyzing a cluster of similar prompts to extract a canonical template.

Here are {count} prompts that belong to the same family:
{prompts}

Your task:
1. Identify the COMMON STRUCTURE across all prompts
2. Identify VARIABLE PARTS (things that change between prompts)
3. Create a CANONICAL TEMPLATE using {{variable_name}} syntax
4. Explain WHY these prompts belong together
```

### 5. Storage Layer (`packages/storage/`)

**Responsibilities:**
- Database models (SQLAlchemy)
- Repository pattern for data access
- CRUD operations
- Query optimization

**Database Schema:**
- `prompts` - Prompt records with DNA JSON
- `families` - Family records with templates
- `lineage` - Evolution relationships
- `processing_log` - Batch processing tracking

**Repositories:**
- `PromptRepository` - Prompt CRUD
- `FamilyRepository` - Family CRUD
- `LineageRepository` - Lineage tracking

### 6. API Layer (`apps/api/`)

**Responsibilities:**
- REST API endpoints
- Request/response handling
- Authentication (future)
- Rate limiting (future)

**Endpoints (Planned):**
- `POST /ingest` - Upload prompts
- `GET /families` - List families
- `GET /families/:id` - Family details
- `GET /prompts/:id` - Prompt DNA
- `GET /prompts/:id/lineage` - Evolution chain
- `POST /process` - Trigger processing
- `GET /stats` - System statistics

### 7. CLI Layer (`apps/cli/`)

**Responsibilities:**
- Command-line interface
- Batch operations
- Demo and testing
- System administration

**Commands:**
- `genome ingest <file>` - Ingest prompts
- `genome run` - Process pending
- `genome families` - List families
- `genome family <id>` - Family details
- `genome template <id>` - Show template
- `genome evolve <id>` - Evolution chain
- `genome stats` - Statistics

### 8. Web Application (`apps/web/`)

**Responsibilities:**
- Generate prompt logs via Portkey
- Real-time log display
- Auto-generation at configurable rates
- Integration with Portkey SDK

**Features:**
- Manual log generation
- Auto-generation (0.1 to 5 logs/second)
- Recent logs display (latest 10)
- Model selection (GPT-3.5, GPT-4, GPT-4 Turbo)
- Sample prompts for testing

**Flow:**
```
User Input → Portkey SDK → Portkey Observability → Evolv Ingestion
```

---

## Processing Pipeline

### Batch Processing Flow

```
1. Ingest Prompts
   ↓
2. Extract DNA (structure, variables, instructions)
   ↓
3. Generate Embeddings
   ↓
4. Store in Database (pending processing)
   ↓
5. Load Pending Prompts (batch)
   ↓
6. Compute Similarity Matrix
   ↓
7. Run HDBSCAN Clustering
   ↓
8. Assign to Families (create new or merge)
   ↓
9. Extract Templates (LLM)
   ↓
10. Update Database
    ↓
11. Log Processing Complete
```

### Incremental Processing

For new prompts arriving after initial processing:

```
1. New Prompt Arrives
   ↓
2. Extract DNA & Embedding
   ↓
3. Check Hash (deduplication)
   ↓
4. Load Existing Families
   ↓
5. Compute Similarity to Families
   ↓
6. Classify:
   - exact_match → Update family
   - variant → Create lineage link
   - new_family → Create new family
   ↓
7. Update Database
```

---

## Technology Stack

### Core Technologies
- **Python 3.11+** - Backend language
- **FastAPI** - Web framework
- **Typer** - CLI framework
- **SQLAlchemy** - ORM
- **SQLite** - Database (upgradeable to PostgreSQL)
- **Next.js 14** - Web application framework
- **TypeScript** - Type-safe frontend
- **React** - UI library
- **Tailwind CSS** - Styling

### ML/AI Libraries
- **sentence-transformers** - Embeddings (local)
- **scikit-learn** - Similarity computation
- **hdbscan** - Clustering algorithm
- **numpy** - Numerical operations

### Infrastructure
- **UV** - Python package manager
- **npm/yarn/pnpm** - Node.js package manager
- **Docker** - Containerization
- **Portkey** - LLM gateway and observability

---

## Data Models

### PromptDNA
```python
{
    "id": "pg-12345",
    "raw_text": "...",
    "hash": "sha256...",
    "structure": {
        "system_message": "...",
        "user_message": "...",
        "total_tokens": 150
    },
    "variables": {
        "detected": ["{{name}}", "{{input}}"],
        "slots": 2
    },
    "instructions": {
        "tone": ["professional"],
        "format": "JSON",
        "constraints": ["be concise"]
    },
    "embedding": [0.1, 0.2, ...],
    "family_id": "family-123",
    "parent_id": "pg-10001"
}
```

### PromptFamily
```python
{
    "id": "family-123",
    "name": "Customer Support Summarizer",
    "description": "...",
    "canonical_template": {
        "text": "Summarize {{input}} in {{format}}",
        "variables": ["input", "format"],
        "example_values": {...}
    },
    "members": ["pg-12345", "pg-12346"],
    "member_count": 2,
    "statistics": {
        "avg_similarity": 0.92,
        "mutation_count": 5
    }
}
```

---

## Deployment Architecture

### Development
```
Local Machine
├── Python 3.11
├── UV package manager
├── SQLite database
└── FastAPI dev server
```

### Production (Docker)
```
Container
├── Python 3.11-slim
├── UV (installed)
├── SQLite (or PostgreSQL)
├── FastAPI (uvicorn)
└── Environment variables
```

### Recommended Platforms
- **Railway** - One-click deploy
- **Fly.io** - Global edge
- **Render** - Simple Docker

---

## Security Considerations

1. **API Keys** - Stored in environment variables
2. **Database** - SQLite file permissions
3. **Input Validation** - Pydantic models
4. **Rate Limiting** - Future implementation
5. **Authentication** - Future implementation

---

## Performance Considerations

1. **Embedding Generation** - Batch processing
2. **Clustering** - Incremental updates
3. **Database** - Indexed queries
4. **Caching** - Future implementation
5. **Async Operations** - FastAPI async/await

---

## Future Enhancements

1. **Web Dashboard** - Visualization UI
2. **Real-time Processing** - WebSocket updates
3. **Advanced Analytics** - Usage patterns
4. **Export Functionality** - Template sharing
5. **Multi-modal Support** - Image + text prompts
6. **Collaboration Features** - Team workspaces

---

**Last Updated:** 2026-01-17
