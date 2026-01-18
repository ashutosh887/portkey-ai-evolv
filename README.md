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
- Node.js 18+ (for web app)

### Installation

```bash
# Install Python dependencies
uv sync

# Install web app dependencies
cd apps/web
npm install
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
npm run dev
```

Visit `http://localhost:3000` for the dashboard and log generator.

## Architecture

Monorepo structure with:
- **apps/api** – FastAPI REST service
- **apps/cli** – Command-line interface
- **apps/web** – Next.js dashboard and log generator
- **packages/** – Core logic (ingestion, DNA extraction, clustering, storage)

## Environment Variables

### Backend (API/CLI)

Copy `.env.example` to `.env`:

```bash
PORTKEY_API_KEY=your_key_here
DATABASE_URL=sqlite:///./data/genome.db
```

### Web App

Copy `apps/web/.env.example` to `apps/web/.env.local`:

```bash
NEXT_PUBLIC_PORTKEY_API_KEY=your_portkey_api_key
NEXT_PUBLIC_PORTKEY_PROVIDER=your_provider_id  # Optional
NEXT_PUBLIC_MOCK_MODE=false
NEXT_PUBLIC_API_URL=http://localhost:8000  # Default
```

## Web App Features

The web application provides:

- **Dashboard** – Overview of prompts, families, and templates
- **Log Generator** – Generate prompt logs for Portkey observability
- **Family Explorer** – Browse and analyze prompt families
- **Prompt Details** – View DNA structure and evolution lineage

Logs generated are automatically sent to Portkey observability and can be ingested by the Evolv system.

## Why This Matters

Prompts are production infrastructure. They evolve, mutate, and accumulate technical debt. Evolv makes them observable, versioned, and governable.

## Team

This project was built by Team 1 at [Portkey AI Builder Challenge](https://hackculture.io/hackathons/portkey-ai-builder-challenge):

- **[Ashutosh Jha](https://github.com/ashutosh887)**
- **[Dhanush U](https://github.com/Dhanush834)**
- **[Ravjot Singh](https://github.com/ravjot07)**

---

**Built for AI Builders Challenge by [Portkey AI](https://github.com/Portkey-AI/).**
