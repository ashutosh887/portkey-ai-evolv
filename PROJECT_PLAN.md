# 📋 Project Plan & Status

High-level plan for building Evolv (Prompt Genome Project).

---

## ✅ Phase 1: Foundation (COMPLETE)

- [x] Monorepo structure
- [x] UV package management
- [x] FastAPI skeleton
- [x] CLI skeleton
- [x] Domain models (PromptDNA, PromptFamily)
- [x] Database schema
- [x] Docker setup
- [x] Documentation

---

## 🔄 Phase 2: Core Intelligence (NEXT)

### Ingestion Layer
- [ ] Portkey API client
- [ ] File ingestion (JSON, CSV, TXT) ✅ Basic structure
- [ ] Git repository scanning
- [ ] Deduplication logic
- [ ] Normalization

### DNA Extraction
- [ ] Enhanced structural parsing ✅ Basic version
- [ ] Variable detection ✅ Basic version
- [ ] Instruction extraction (LLM-enhanced)
- [ ] Format detection
- [ ] Embedding generation (OpenAI/sentence-transformers)

### Clustering
- [ ] Embedding generation for prompts
- [ ] Similarity matrix computation ✅ Structure
- [ ] HDBSCAN clustering ✅ Structure
- [ ] Confidence scoring ✅ Structure
- [ ] Family assignment logic

### Template Synthesis
- [ ] Portkey client integration
- [ ] Template extraction prompt
- [ ] LLM call with fallbacks
- [ ] Template parsing & validation
- [ ] Explanation generation

### Evolution Tracking
- [ ] New prompt classification
- [ ] Family matching logic
- [ ] Mutation detection
- [ ] Lineage graph construction
- [ ] Drift detection

---

## 🚀 Phase 3: API & Interface

### REST API
- [ ] `POST /ingest` - Upload prompts
- [ ] `GET /families` - List families
- [ ] `GET /families/:id` - Family details
- [ ] `GET /prompts/:id` - Prompt DNA
- [ ] `GET /prompts/:id/lineage` - Evolution chain
- [ ] `POST /process` - Trigger processing
- [ ] `GET /stats` - Statistics ✅ Basic

### CLI Enhancement
- [ ] Implement all commands
- [ ] Progress indicators
- [ ] Rich output formatting
- [ ] Error handling

### Storage Layer
- [ ] Repository pattern implementation
- [ ] CRUD operations
- [ ] Query optimization
- [ ] Migration system

---

## 🎨 Phase 4: Polish (Optional)

### Web Dashboard
- [ ] Family list view
- [ ] Family detail view
- [ ] Evolution graph visualization
- [ ] Template viewer

### Advanced Features
- [ ] Batch processing scheduler
- [ ] Incremental updates
- [ ] Alert system
- [ ] Export functionality

---

## 🏗️ Architecture Decisions

### ✅ Made
- **Python 3.11+** - Best for ML/clustering
- **UV** - Fast, modern package manager
- **FastAPI** - Modern async API framework
- **SQLite** - Simple, sufficient for demo
- **Monorepo** - Clean separation, easy refactoring

### 🔄 To Decide
- **Embedding model** - OpenAI vs sentence-transformers
- **Portkey SDK version** - Check latest
- **Visualization library** - Plotly vs D3.js
- **Deployment platform** - Railway vs Fly.io

---

## 📊 Success Metrics

### Demo Targets
- Process 1,000+ prompts
- Detect 50+ families
- Extract templates with >90% accuracy
- Show evolution chains
- Full Portkey integration visible

### Technical Targets
- API response time <200ms
- Processing 100 prompts in <5 minutes
- Zero data loss
- Full error recovery

---

## 🚨 Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Embedding API fails | Fallback to sentence-transformers |
| LLM extraction fails | Regex-based fallback |
| Clustering too slow | Batch processing, caching |
| Demo database corrupt | Backup, regeneration script |
| Portkey API issues | Mock data for demo |

---

## 📅 Timeline Estimate

- **Day 1**: Ingestion + DNA extraction (4-6 hours)
- **Day 2**: Clustering + Template synthesis (6-8 hours)
- **Day 3**: Evolution tracking + API (4-6 hours)
- **Day 4**: CLI + Testing + Polish (4-6 hours)
- **Day 5**: Demo prep + Deployment (2-4 hours)

**Total: 20-30 hours** (comfortable for hackathon)

---

## 🎯 Next Immediate Steps

1. **Install & Verify**
   ```bash
   uv sync
   uv run python scripts/init_db.py
   uv run uvicorn apps.api.main:app --reload
   ```

2. **Start with Ingestion**
   - Implement file ingestion fully
   - Test with sample data
   - Add to API endpoint

3. **DNA Extraction**
   - Enhance extractor
   - Add embedding generation
   - Test on diverse prompts

4. **Iterate!**

---

**You're ready to build!** 🚀
