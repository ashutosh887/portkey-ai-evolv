# 🛠️ Setup Guide

Quick setup instructions to get Evolv running locally.

---

## Prerequisites

- **Python 3.11+** - Check with `python --version`
- **UV** - Install from [astral-sh/uv](https://github.com/astral-sh/uv)

### Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

---

## Initial Setup

### 1. Clone & Navigate

```bash
cd evolv
```

### 2. Install Dependencies

```bash
uv sync
```

This will:
- Create a virtual environment (`.venv/`)
- Install all dependencies from `pyproject.toml`
- Set up the project in editable mode

### 3. Activate Virtual Environment

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Or use UV directly (no activation needed):
```bash
uv run <command>
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 5. Initialize Database

```bash
uv run python scripts/init_db.py
```

This creates the SQLite database and all tables.

---

## Verify Installation

### Test API

```bash
uv run uvicorn apps.api.main:app --reload
```

Visit:
- API: http://localhost:8000
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs

### Test CLI

```bash
uv run genome --help
```

You should see all available commands.

---

## Development Workflow

### Run API with Auto-reload

```bash
make run-api
# or
uv run uvicorn apps.api.main:app --reload
```

### Run Tests

```bash
make test
# or
uv run pytest
```

### Code Quality

```bash
# Format
make format

# Lint
make lint

# Type check
make type-check
```

---

## Project Structure

```
evolv/
├── apps/
│   ├── api/          # FastAPI application
│   └── cli/          # Typer CLI
├── packages/
│   ├── core/         # Domain models
│   ├── ingestion/    # Data ingestion
│   ├── dna_extractor/# DNA extraction
│   ├── clustering/   # Clustering engine
│   ├── llm/          # LLM client
│   └── storage/      # Database layer
├── infra/            # Docker & deployment
├── scripts/          # Utility scripts
└── data/             # Database & data files (gitignored)
```

---

## Next Steps

1. ✅ Setup complete
2. 🔄 Implement ingestion layer
3. 🧬 Implement DNA extraction
4. 🧪 Implement clustering
5. 🤖 Implement LLM template extraction
6. 📈 Implement evolution tracking
7. 🚀 Deploy!

---

## Troubleshooting

### UV not found
- Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Add to PATH if needed

### Import errors
- Ensure you're in the project root
- Run `uv sync` again
- Check virtual environment is activated

### Database errors
- Run `uv run python scripts/init_db.py`
- Check `data/` directory exists and is writable

### Port already in use
- Change port: `uvicorn apps.api.main:app --port 8001`
- Or kill process on port 8000

---

**Ready to build!** 🚀
