# Evolv

> **Your prompts, but smarter every week.**

---

## What This Is

Evolv (The Prompt Genome Project) ingests real-world prompts from production systems,
extracts their "DNA" (structure, variables, constraints), clusters them into prompt families,
and tracks how they evolve over time.

**Transform prompt sprawl into:**
- Canonical templates with automatic extraction
- Clear lineage and evolution tracking
- Explainable grouping with confidence scores
- Continuous, incremental processing
- Deep integration with Portkey observability

---

## Key Capabilities

- **Prompt DNA Extraction** – Structural parsing, variable detection, instruction extraction
- **Automatic Family Detection** – HDBSCAN-based semantic clustering
- **Template Synthesis** – LLM-powered canonical template extraction
- **Evolution Tracking** – Mutation detection, drift alerts, lineage graphs
- **Full Explainability** – Every grouping has reasoning and confidence scores
- **Continuous Processing** – Incremental updates, no full reprocessing
- **Portkey Integration** – Ingest from logs, trace all LLM calls

---

## Architecture Overview

```
evolv/
├── apps/
│   ├── api/          # FastAPI service (deployable)
│   └── cli/          # Typer CLI (demo + operations)
│
├── packages/
│   ├── core/         # Domain models & business logic
│   ├── ingestion/    # Portkey logs, file uploads, git scanning
│   ├── dna_extractor/# Prompt DNA extraction engine
│   ├── clustering/   # Similarity computation & HDBSCAN
│   ├── llm/          # Portkey abstraction & LLM orchestration
│   └── storage/      # SQLite & repository pattern
│
├── infra/            # Docker, deployment configs
└── scripts/          # One-off jobs & utilities
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Install dependencies
uv sync
```

### Run the API

```bash
uv run uvicorn apps.api.main:app --reload
```

API will be available at `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

### Use the CLI

```bash
# Ingest prompts from a file
uv run genome ingest data/prompts.json

# Process pending prompts
uv run genome run

# List all prompt families
uv run genome families

# Show family details
uv run genome family <family_id>

# Show canonical template
uv run genome template <family_id>

# Show evolution chain
uv run genome evolve <prompt_id>

# System statistics
uv run genome stats
```

---

## Development

### Project Structure

- **apps/api** – FastAPI application with REST endpoints
- **apps/cli** – Command-line interface for operations
- **packages/core** – Shared domain models and types
- **packages/ingestion** – Data ingestion from various sources
- **packages/dna_extractor** – Prompt structure analysis
- **packages/clustering** – Semantic similarity and clustering
- **packages/llm** – LLM calls via Portkey with fallbacks
- **packages/storage** – Database layer and repositories

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Format code
uv run black .

# Lint
uv run ruff check .

# Type check
uv run mypy .
```

---

## Deployment

The API is designed to be deployed as a single service.

### Docker

```bash
# Build
docker build -f infra/Dockerfile -t evolv .

# Run
docker run -p 8000:8000 evolv
```

The Dockerfile uses UV for dependency management and runs the API with `uv run`.

### Recommended Platforms

- **Railway** – One-click deploy, SQLite support
- **Fly.io** – Global edge deployment
- **Render** – Simple Docker deploys

See `infra/` directory for deployment configurations.

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Portkey API
PORTKEY_API_KEY=your_key_here
PORTKEY_VIRTUAL_KEY=your_virtual_key

# OpenAI (fallback)
OPENAI_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///./data/genome.db
```

---

## Why This Matters

Prompts are now production infrastructure. They evolve, mutate, and accumulate technical debt just like code.

**Evolv makes them:**
- Observable (see what you're actually using)
- Versioned (track changes over time)
- Governable (detect drift, enforce standards)
- Optimizable (find duplicates, extract templates)

---

## Roadmap

- [x] Project skeleton
- [ ] Ingestion layer (Portkey, files, git)
- [ ] DNA extraction engine
- [ ] Clustering & family detection
- [ ] Template synthesis (LLM)
- [ ] Evolution tracking
- [ ] REST API endpoints
- [ ] CLI interface
- [ ] Web dashboard (optional)
- [ ] Production deployment

---

## License

MIT

---

**Built for AI Builders Challenge by [Portkey AI](https://github.com/Portkey-AI/).**
