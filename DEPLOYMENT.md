# Deployment Guide

This guide covers deploying Evolv to various platforms.

---

## Quick Deploy Options

### Railway (Recommended for Hackathons)

1. **Connect Repository**
   - Go to [Railway](https://railway.app)
   - New Project → Deploy from GitHub
   - Select your repository

2. **Configure Environment**
   - Add environment variables from `.env.example`
   - Set `DATABASE_URL` (Railway provides Postgres, or use SQLite)

3. **Deploy**
   - Railway auto-detects Dockerfile
   - Or set build command: `uv sync --frozen`
   - Set start command: `uv run uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`

4. **Done!**
   - Get public URL
   - API available at `https://your-app.railway.app`

---

### Fly.io

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login & Launch**
   ```bash
   fly auth login
   fly launch
   ```

3. **Set Secrets**
   ```bash
   fly secrets set PORTKEY_API_KEY=your_key
   fly secrets set OPENAI_API_KEY=your_key
   ```

4. **Deploy**
   ```bash
   fly deploy
   ```

---

### Render

Render expects your app to **listen on the `PORT` environment variable**. If you use `--port 8000` or forget `$PORT`, you’ll see **"No open ports detected"** and the deploy will fail.

**Option A – Docker (recommended)**

- Connect the repo and use the **Docker** runtime.
- Use **Dockerfile path:** `infra/Dockerfile` (or `./infra/Dockerfile`).
- The Dockerfile is set up to run: `--port ${PORT:-8000}` so Render’s `PORT` is used.
- Set env vars: `DATABASE_URL`, `PORTKEY_API_KEY`, etc.
- If the first deploy has no DB: run a one-off or add an init step. For SQLite, ensure a writable disk (Render’s ephemeral filesystem is fine for `/app/data` if the Dockerfile creates it).

**Option B – Native (no Docker)**

- **Build Command:** `uv sync --frozen`
- **Start Command:** `uv run uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`  
  - Must use `$PORT`, not `8000`.
- **Root Directory:** leave blank or set to repo root.
- Add env vars from `.env.example`.

**Environment Variables**

- Add at least: `DATABASE_URL`, `PORTKEY_API_KEY` (and optionally `PORTKEY_VIRTUAL_KEY`).
- For SQLite: `DATABASE_URL=sqlite:///./data/genome.db` (ensure `/app/data` exists and is writable in your setup).

---

## Docker Deployment

### Build Image

```bash
docker build -f infra/Dockerfile -t evolv:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e PORTKEY_API_KEY=your_key \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  evolv:latest
```

### Docker Compose

```bash
cd infra
docker-compose up -d
```

---

## Environment Variables

Required variables (see `.env.example`):

- `PORTKEY_API_KEY` - Portkey API key
- `PORTKEY_VIRTUAL_KEY` - Portkey virtual key
- `OPENAI_API_KEY` - OpenAI API key (fallback)
- `DATABASE_URL` - Database connection string

Optional:
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)
- `LOG_LEVEL` - Logging level (default: INFO)

---

## Database Considerations

### SQLite (Default)

- Simple, no setup
- Works for demos
- Not ideal for production scale
- Single-writer limitation

### PostgreSQL (Production)

1. Update `DATABASE_URL`:
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ```

2. Install PostgreSQL driver:
   ```bash
   uv add psycopg2-binary
   ```

3. Update `packages/storage/database.py` if needed

---

## Health Checks

All platforms should check:
- `GET /health` - Should return `{"status": "ok"}`

---

## Monitoring

- Portkey dashboard for LLM calls
- Application logs via platform logging
- Database size monitoring (SQLite files)

---

## Troubleshooting

### Port Issues
- Ensure `API_HOST=0.0.0.0` (not `127.0.0.1`)
- Check platform-specific port requirements

### Database Locked
- SQLite: Ensure single process or use file locking
- Consider PostgreSQL for multi-instance

### Missing Dependencies
- Ensure `uv sync --frozen` runs during build
- Check `pyproject.toml` dependencies

---

## Production Checklist

- [ ] Environment variables configured
- [ ] Database initialized (`uv run python scripts/init_db.py`)
- [ ] Health check endpoint working
- [ ] Logging configured
- [ ] Error handling tested
- [ ] Rate limiting (if needed)
- [ ] CORS configured (if web dashboard)

---

**Ready to deploy!**
