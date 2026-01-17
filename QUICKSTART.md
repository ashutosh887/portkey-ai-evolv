# ⚡ Quick Start

Get Evolv running in 2 minutes.

---

## 1. Install Dependencies

```bash
uv sync
```

## 2. Setup Environment

```bash
cp .env.example .env
# Edit .env with your API keys (optional for now)
```

## 3. Initialize Database

```bash
uv run python scripts/init_db.py
```

## 4. Start API

```bash
uv run uvicorn apps.api.main:app --reload
```

Visit: http://localhost:8000/docs

## 5. Test CLI

```bash
uv run genome --help
```

---

## 🎯 What's Next?

1. **Implement ingestion** - Start with `packages/ingestion/files.py`
2. **Enhance DNA extraction** - Work on `packages/dna_extractor/extractor.py`
3. **Add clustering** - Complete `packages/clustering/engine.py`
4. **Build API endpoints** - Add routes in `apps/api/main.py`

See `PROJECT_PLAN.md` for full roadmap.

---

## 📚 Documentation

- `README.md` - Project overview
- `SETUP.md` - Detailed setup guide
- `DEPLOYMENT.md` - Deployment instructions
- `PROJECT_PLAN.md` - Development roadmap

---

**Ready to code!** 🚀
