from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import tempfile
import os
from datetime import datetime, timedelta, timezone


def utcnow():
    """Get current UTC datetime (compatible with Python 3.11+)"""
    return datetime.now(timezone.utc)

from packages.storage.database import get_db
from packages.storage.repositories import PromptRepository, FamilyRepository, TemplateRepository, LineageRepository
from packages.storage.models import PromptInstance
from packages.core.processing import ProcessingService
from packages.ingestion.files import ingest_from_file
from packages.ingestion.portkey import PortKeyIngestor
from packages.core.processing import _model_to_dna

app = FastAPI(
    title="Evolv API",
    description="Prompt lineage, clustering, and evolution tracking",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "evolv"}


@app.get("/")
async def root():
    return {
        "message": "Evolv API - Your prompts, but smarter every week",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.post("/ingest")
async def ingest_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    prompt_repo = PromptRepository(db)
    family_repo = FamilyRepository(db)
    lineage_repo = LineageRepository(db)
    service = ProcessingService(prompt_repo=prompt_repo, family_repo=family_repo, lineage_repo=lineage_repo, use_mock_llm=False)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        raw_data = await ingest_from_file(tmp_path)
        
        saved = 0
        duplicates = 0
        errors = []
        
        for item in raw_data:
            try:
                text = item.get("text") or item.get("prompt") or item.get("content") or str(item)
                if not text or not isinstance(text, str):
                    continue
                
                dna = await service.process_raw_prompt(text, metadata={"source": "file", "filename": file.filename})
                saved += 1
            except Exception as e:
                errors.append(str(e))
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    duplicates += 1
        
        return {
            "status": "success",
            "saved": saved,
            "duplicates": duplicates,
            "errors": len(errors),
            "total_rows": len(raw_data),
        }
    finally:
        os.unlink(tmp_path)


@app.post("/ingest/portkey")
async def ingest_portkey(
    db: Session = Depends(get_db),
):
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="PORTKEY_API_KEY not configured")
    
    try:
        ingestor = PortKeyIngestor(api_key=api_key)
        time_min = utcnow() - timedelta(days=1)
        instances = await ingestor.run_ingestion(time_min=time_min)
        
        prompt_repo = PromptRepository(db)
        saved = 0
        duplicates = 0
        for instance in instances:
            try:
                prompt_repo.create_from_instance(instance)
                saved += 1
            except Exception as e:
                # Check if it's a duplicate error
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    duplicates += 1
                # Log other errors but continue processing
                import logging
                logging.warning(f"Failed to ingest instance: {str(e)}")
        
        return {
            "status": "success",
            "ingested": saved,
            "total_from_portkey": len(instances),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portkey ingestion failed: {str(e)}")


@app.get("/families")
async def list_families(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("created_at", regex="^(created_at|member_count|family_name)$"),
    db: Session = Depends(get_db),
):
    family_repo = FamilyRepository(db)
    families = family_repo.get_all()
    
    if sort == "member_count":
        families = sorted(families, key=lambda f: f.member_count, reverse=True)
    elif sort == "family_name":
        families = sorted(families, key=lambda f: f.family_name)
    else:
        families = sorted(families, key=lambda f: f.created_at, reverse=True)
    
    total = len(families)
    families = families[offset:offset + limit]
    
    return {
        "families": [
            {
                "family_id": f.family_id,
                "family_name": f.family_name,
                "description": f.description,
                "member_count": f.member_count,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in families
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/families/{family_id}")
async def get_family(
    family_id: str,
    db: Session = Depends(get_db),
):
    family_repo = FamilyRepository(db)
    template_repo = TemplateRepository(db)
    prompt_repo = PromptRepository(db)
    
    family = family_repo.get_by_id(family_id)
    if not family:
        raise HTTPException(status_code=404, detail=f"Family {family_id} not found")
    
    members = prompt_repo.get_by_family(family_id)
    template = template_repo.get_by_family(family_id)
    
    return {
        "family_id": family.family_id,
        "family_name": family.family_name,
        "description": family.description,
        "member_count": family.member_count,
        "created_at": family.created_at.isoformat() if family.created_at else None,
        "members": [
            {
                "prompt_id": m.prompt_id,
                "original_text": m.original_text,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "lineage": {
                    "has_lineage": False,
                },
            }
            for m in members
        ],
        "template": {
            "template_id": template.template_id,
            "template_text": template.template_text,
            "slots": template.slots,
            "template_version": template.template_version,
            "quality_score": template.quality_score,
        } if template else None,
    }


@app.get("/families/{family_id}/members")
async def get_family_members(
    family_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    family_repo = FamilyRepository(db)
    prompt_repo = PromptRepository(db)
    
    family = family_repo.get_by_id(family_id)
    if not family:
        raise HTTPException(status_code=404, detail=f"Family {family_id} not found")
    
    all_members = prompt_repo.get_by_family(family_id)
    total = len(all_members)
    members = all_members[offset:offset + limit]
    
    return {
        "members": [
            {
                "prompt_id": m.prompt_id,
                "original_text": m.original_text,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in members
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/families/{family_id}/template")
async def get_template(
    family_id: str,
    db: Session = Depends(get_db),
):
    family_repo = FamilyRepository(db)
    template_repo = TemplateRepository(db)
    
    family = family_repo.get_by_id(family_id)
    if not family:
        raise HTTPException(status_code=404, detail=f"Family {family_id} not found")
    
    template = template_repo.get_by_family(family_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template for family {family_id} not found")
    
    return {
        "template_id": template.template_id,
        "family_id": template.family_id,
        "template_text": template.template_text,
        "slots": template.slots,
        "template_version": template.template_version,
        "quality_score": template.quality_score,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    }


@app.post("/families/{family_id}/template/extract")
async def extract_template(
    family_id: str,
    db: Session = Depends(get_db),
):
    family_repo = FamilyRepository(db)
    template_repo = TemplateRepository(db)
    prompt_repo = PromptRepository(db)
    
    family = family_repo.get_by_id(family_id)
    if not family:
        raise HTTPException(status_code=404, detail=f"Family {family_id} not found")
    
    existing = template_repo.get_by_family(family_id)
    if existing:
        return {
            "status": "already_exists",
            "template_id": existing.template_id,
            "message": "Template already extracted for this family",
        }
    
    members = prompt_repo.get_by_family(family_id)
    if not members:
        raise HTTPException(status_code=400, detail="Family has no members")
    
    prompt_dnas = [_model_to_dna(m) for m in members]
    
    from packages.llm import LLMClient
    try:
        llm_client = LLMClient()
        template = await llm_client.extract_template(prompt_dnas)
    except Exception as e:
        import logging
        logging.warning(f"LLMClient failed, falling back to MockLLMClient: {str(e)}")
        from packages.llm import MockLLMClient
        llm_client = MockLLMClient()
        template = await llm_client.extract_template(prompt_dnas)
    
    try:
        created_template = template_repo.create_template(
            family_id=family_id,
            template_text=template.text,
            slots={"variables": template.variables, "example_values": template.example_values},
            quality_score=None,
        )
        
        return {
            "status": "success",
            "template_id": created_template.template_id if hasattr(created_template, 'template_id') else None,
            "template_text": template.text,
            "variables": template.variables,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save template: {str(e)}")


@app.get("/prompts")
async def list_prompts(
    family_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    prompt_repo = PromptRepository(db)
    prompts = prompt_repo.get_paginated(family_id=family_id, limit=limit, offset=offset)
    
    total = prompt_repo.count_all() if not family_id else len(prompt_repo.get_by_family(family_id))
    
    return {
        "prompts": [
            {
                "prompt_id": p.prompt_id,
                "original_text": p.original_text,
                "normalized_text": p.normalized_text,
                "family_id": p.family_id,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "dna": None,  # Will be populated in detail endpoint
                "lineage": {
                    "has_lineage": False,
                },
            }
            for p in prompts
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/prompts/{prompt_id}")
async def get_prompt(
    prompt_id: str,
    db: Session = Depends(get_db),
):
    prompt_repo = PromptRepository(db)
    family_repo = FamilyRepository(db)
    lineage_repo = LineageRepository(db)
    
    prompt = prompt_repo.get_by_id(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
    
    dna = _model_to_dna(prompt)
    
    family = None
    if prompt.family_id:
        family = family_repo.get_by_id(prompt.family_id)
    
    chain = lineage_repo.get_lineage_chain(prompt_id)
    ancestors = [c for c in chain if c.get("direction") == "ancestor"]
    descendants = [c for c in chain if c.get("direction") == "descendant"]
    
    return {
        "prompt_id": prompt.prompt_id,
        "original_text": prompt.original_text,
        "normalized_text": prompt.normalized_text,
        "family_id": prompt.family_id,
        "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
        "dna": {
            "id": dna.id,
            "structure": {
                "system_message": dna.structure.system_message,
                "user_message": dna.structure.user_message,
                "total_tokens": dna.structure.total_tokens,
            },
            "variables": {
                "detected": dna.variables.detected,
                "slots": dna.variables.slots,
            },
            "instructions": {
                "tone": dna.instructions.tone,
                "format": dna.instructions.format,
                "constraints": dna.instructions.constraints,
            },
        },
        "family": {
            "family_id": family.family_id,
            "family_name": family.family_name,
        } if family else None,
        "lineage": {
            "has_lineage": len(chain) > 1,
            "ancestors": len(ancestors),
            "descendants": len(descendants),
            "total_links": len(chain) - 1,
        },
    }


@app.get("/prompts/{prompt_id}/lineage")
async def get_prompt_lineage(
    prompt_id: str,
    db: Session = Depends(get_db),
):
    prompt_repo = PromptRepository(db)
    lineage_repo = LineageRepository(db)
    
    prompt = prompt_repo.get_by_id(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
    
    chain = lineage_repo.get_lineage_chain(prompt_id)
    
    return {
        "prompt_id": prompt_id,
        "lineage": chain,
        "total_links": len(chain) - 1,
    }


@app.post("/process")
async def process_pending(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    prompt_repo = PromptRepository(db)
    family_repo = FamilyRepository(db)
    lineage_repo = LineageRepository(db)
    service = ProcessingService(prompt_repo=prompt_repo, family_repo=family_repo, lineage_repo=lineage_repo, use_mock_llm=False)
    
    result = await service.process_batch(limit=limit)
    
    return {
        "status": "success",
        "processed": result["processed"],
        "families_created": result["families_created"],
        "families_updated": result["families_updated"],
    }


@app.get("/process/status")
async def get_process_status(
    db: Session = Depends(get_db),
):
    prompt_repo = PromptRepository(db)
    pending_count = prompt_repo.count_pending()
    
    latest = (
        db.query(PromptInstance)
        .filter(PromptInstance.family_id.isnot(None))
        .order_by(PromptInstance.updated_at.desc())
        .first()
    )
    
    return {
        "pending_count": pending_count,
        "last_processed_at": latest.updated_at.isoformat() if latest and latest.updated_at else None,
    }


@app.get("/templates")
async def list_templates(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    template_repo = TemplateRepository(db)
    family_repo = FamilyRepository(db)
    
    templates = template_repo.get_all(limit=limit, offset=offset)
    total = template_repo.count_all()
    
    # Enrich with family names
    result = []
    for t in templates:
        family = family_repo.get_by_id(t.family_id)
        result.append({
            "template_id": t.template_id,
            "family_id": t.family_id,
            "family_name": family.family_name if family else None,
            "template_text": t.template_text,
            "slots": t.slots,
            "template_version": t.template_version,
            "quality_score": t.quality_score,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    
    return {
        "templates": result,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/stats")
async def stats(
    db: Session = Depends(get_db),
):
    prompt_repo = PromptRepository(db)
    family_repo = FamilyRepository(db)
    template_repo = TemplateRepository(db)
    
    total_prompts = prompt_repo.count_all()
    pending_prompts = prompt_repo.count_pending()
    total_families = family_repo.count_all()
    total_templates = template_repo.count_all()
    
    families = family_repo.get_all()
    avg_family_size = sum(f.member_count for f in families) / len(families) if families else 0
    
    latest_prompts = prompt_repo.get_latest(limit=1)
    last_ingestion = latest_prompts[0].created_at if latest_prompts and len(latest_prompts) > 0 else None
    
    return {
        "prompts": {
            "total": total_prompts,
            "pending": pending_prompts,
            "processed": total_prompts - pending_prompts,
        },
        "families": {
            "total": total_families,
            "average_size": round(avg_family_size, 2),
        },
        "templates": {
            "extracted": total_templates,
        },
        "duplicates_detected": "TBD",
        "last_ingestion": last_ingestion.isoformat() if last_ingestion else None,
    }
