"""
FastAPI application for Evolv - Prompt Genome Project
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Evolv API",
    description="Prompt lineage, clustering, and evolution tracking",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for web dashboard (if added later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "evolv"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Evolv API - Your prompts, but smarter every week",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/stats")
async def stats():
    """System-wide statistics"""
    # TODO: Implement actual statistics
    return {
        "prompts": 0,
        "families": 0,
        "duplicates_detected": "TBD",
        "templates_extracted": 0,
    }
