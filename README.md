# Evolv

> Your prompts, but smarter every week.

Evolv treats prompts like genetic sequences—extracting their DNA, tracking mutations, and understanding lineage. Transform prompt sprawl into organized, versioned templates with automatic family detection and evolution tracking.

## What It Does

Evolv ingests prompts from production systems, extracts their structural DNA (variables, constraints, instructions), clusters them into semantic families, and tracks how they evolve over time. It provides:

- **Automatic DNA Extraction** – Parse structure, detect variables, extract instructions
- **Semantic Clustering** – Group similar prompts into families using embeddings
- **Template Synthesis** – LLM-powered canonical template extraction
- **Evolution Tracking** – Monitor mutations, track lineage, detect drift
- **Portkey Integration** – Ingest from observability logs, orchestrate LLM calls

## Quick Start

### Prerequisites

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) package manager

### Installation

```bash
uv sync
```

### Run the API

```bash
uv run uvicorn apps.api.main:app --reload
```

API available at `http://localhost:8000` with docs at `/docs`.

### Use the CLI

```bash
uv run genome ingest data/prompts.json  # Ingest prompts
uv run genome run                        # Process pending
uv run genome families                  # List families
uv run genome evolve <prompt_id>        # Show evolution chain
uv run genome stats                     # System statistics
```

### Run the Web App

```bash
cd apps/web
npm install
npm run dev
```

Visit `http://localhost:3000` for the dashboard and log generator.

## Architecture

Monorepo structure with:
- **apps/api** – FastAPI REST service
- **apps/cli** – Command-line interface
- **apps/web** – Next.js dashboard
- **packages/** – Core logic (ingestion, DNA extraction, clustering, storage)

## Environment Variables

Copy `.env.example` to `.env`:

```bash
PORTKEY_API_KEY=your_key_here
DATABASE_URL=sqlite:///./data/genome.db
```

## Why This Matters

Prompts are production infrastructure. They evolve, mutate, and accumulate technical debt. Evolv makes them observable, versioned, and governable.

---

**Built for AI Builders Challenge by [Portkey AI](https://github.com/Portkey-AI/).**
