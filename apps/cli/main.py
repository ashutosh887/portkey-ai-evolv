import typer
from pathlib import Path
import asyncio
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

app = typer.Typer(
    name="genome",
    help="Evolv CLI - Your prompts, but smarter every week",
    add_completion=False,
)


@app.command()
def add(
    text: str = typer.Argument(..., help="Prompt text to add (will be normalized, embedded, and stored)"),
):
    from packages.storage.database import get_db
    from packages.storage.repositories import PromptRepository, FamilyRepository
    from packages.core import ProcessingService

    db_gen = get_db()
    db = next(db_gen)
    try:
        from packages.storage.repositories import LineageRepository
        prompt_repo = PromptRepository(db)
        family_repo = FamilyRepository(db)
        lineage_repo = LineageRepository(db)
        service = ProcessingService(prompt_repo=prompt_repo, family_repo=family_repo, lineage_repo=lineage_repo, use_mock_llm=False)
        dna = asyncio.run(service.process_raw_prompt(text))
        typer.echo(f"Added prompt id={dna.id}")
        typer.echo("✅ Done. Run 'genome run' to cluster into families.")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.command()
def ingest(
    file: str = typer.Argument(..., help="Path to file containing prompts"),
    source: str = typer.Option("file", help="Source type: file, portkey"),
):
    if source == "portkey":
        api_key = os.getenv("PORTKEY_API_KEY")
        if not api_key:
            typer.echo("❌ Error: PORTKEY_API_KEY not configured", err=True)
            raise typer.Exit(1)
        
        from packages.storage.database import get_db
        from packages.storage.repositories import PromptRepository
        from packages.ingestion.portkey import PortKeyIngestor
        
        typer.echo("🚀 Starting Portkey ingestion...")
        db_gen = get_db()
        db = next(db_gen)
        try:
            prompt_repo = PromptRepository(db)
            ingestor = PortKeyIngestor(api_key=api_key)
            time_min = datetime.utcnow() - timedelta(days=1)
            instances = asyncio.run(ingestor.run_ingestion(time_min=time_min))
            
            saved = 0
            duplicates = 0
            for instance in instances:
                try:
                    prompt_repo.create_from_instance(instance)
                    saved += 1
                except Exception:
                    duplicates += 1
            
            typer.echo(f"✅ Ingestion complete: {saved} saved, {duplicates} duplicates skipped")
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
    else:
        from packages.storage.database import get_db
        from packages.storage.repositories import PromptRepository, FamilyRepository
        from packages.core import ProcessingService
        from packages.ingestion.files import ingest_from_file
        
        file_path = Path(file)
        if not file_path.exists():
            typer.echo(f"❌ Error: File not found: {file}", err=True)
            raise typer.Exit(1)
        
        typer.echo(f"📂 Ingesting prompts from: {file}")
        db_gen = get_db()
        db = next(db_gen)
        try:
            from packages.storage.repositories import LineageRepository
            prompt_repo = PromptRepository(db)
            family_repo = FamilyRepository(db)
            lineage_repo = LineageRepository(db)
            service = ProcessingService(prompt_repo=prompt_repo, family_repo=family_repo, lineage_repo=lineage_repo, use_mock_llm=False)
            
            raw_data = asyncio.run(ingest_from_file(str(file_path)))
            
            saved = 0
            duplicates = 0
            errors = 0
            
            for item in raw_data:
                try:
                    text = item.get("text") or item.get("prompt") or item.get("content") or str(item)
                    if not text or not isinstance(text, str):
                        continue
                    
                    dna = asyncio.run(service.process_raw_prompt(text, metadata={"source": "file", "filename": file}))
                    saved += 1
                except Exception as e:
                    errors += 1
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        duplicates += 1
            
            typer.echo(f"✅ Ingestion complete: {saved} saved, {duplicates} duplicates, {errors} errors")
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass


@app.command()
def prompts(limit: int = 20):
    from packages.storage.database import get_db
    from packages.storage.repositories import PromptRepository
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        repo = PromptRepository(db)
        prompts = repo.get_latest(limit=limit)
        
        if not prompts:
            typer.echo("No prompts found in database.")
            return

        typer.echo(f"Found {len(prompts)} prompts:")
        typer.echo("-" * 50)
        for p in prompts:
            typer.echo(f"ID: {p.prompt_id}")
            typer.echo(f"Created: {p.created_at}")
            typer.echo(f"Text: {p.original_text[:100]}...")
            typer.echo("-" * 50)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.command()
def run(limit: int = typer.Option(100, "--limit", "-l", help="Max pending prompts to process")):
    from packages.storage.database import get_db
    from packages.storage.repositories import PromptRepository, FamilyRepository
    from packages.core import ProcessingService

    typer.echo("Processing pending prompts...")
    db_gen = get_db()
    db = next(db_gen)
    try:
        from packages.storage.repositories import LineageRepository
        prompt_repo = PromptRepository(db)
        family_repo = FamilyRepository(db)
        lineage_repo = LineageRepository(db)
        service = ProcessingService(prompt_repo=prompt_repo, family_repo=family_repo, lineage_repo=lineage_repo, use_mock_llm=False)
        result = asyncio.run(service.process_batch(limit=limit))
        typer.echo(f"  Processed: {result['processed']}")
        typer.echo(f"  Families created: {result['families_created']}")
        typer.echo("✅ Processing complete")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.command()
def families(
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of families to show"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table or json"),
):
    from packages.storage.database import get_db
    from packages.storage.repositories import FamilyRepository
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        family_repo = FamilyRepository(db)
        all_families = family_repo.get_all()
        families = sorted(all_families, key=lambda f: f.created_at, reverse=True)[:limit]
        
        if not families:
            typer.echo("No families found yet. Ingest some prompts and run 'genome run' first!")
            return
        
        if format == "json":
            output = [
                {
                    "family_id": f.family_id,
                    "family_name": f.family_name,
                    "member_count": f.member_count,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                }
                for f in families
            ]
            typer.echo(json.dumps(output, indent=2))
        else:
            typer.echo(f"\n{'ID':<40} {'Name':<30} {'Members':<10} {'Created':<20}")
            typer.echo("-" * 100)
            for f in families:
                created_str = f.created_at.strftime("%Y-%m-%d %H:%M") if f.created_at else "N/A"
                typer.echo(f"{f.family_id:<40} {f.family_name[:28]:<30} {f.member_count:<10} {created_str:<20}")
            typer.echo(f"\nTotal: {len(all_families)} families")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.command()
def family(
    family_id: str = typer.Argument(..., help="Family ID to inspect"),
):
    from packages.storage.database import get_db
    from packages.storage.repositories import FamilyRepository, TemplateRepository, PromptRepository
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        family_repo = FamilyRepository(db)
        template_repo = TemplateRepository(db)
        prompt_repo = PromptRepository(db)
        
        family = family_repo.get_by_id(family_id)
        if not family:
            typer.echo(f"❌ Family {family_id} not found")
            raise typer.Exit(1)
        
        members = prompt_repo.get_by_family(family_id)
        template = template_repo.get_by_family(family_id)
        
        typer.echo(f"\n📋 Family: {family.family_name}")
        typer.echo(f"   ID: {family.family_id}")
        typer.echo(f"   Members: {family.member_count}")
        if family.description:
            typer.echo(f"   Description: {family.description}")
        typer.echo(f"   Created: {family.created_at}")
        
        if template:
            typer.echo(f"\n📝 Template:")
            typer.echo(f"   {template.template_text}")
            if template.slots.get("variables"):
                typer.echo(f"   Variables: {', '.join(template.slots['variables'])}")
        
        typer.echo(f"\n👥 Member Prompts ({len(members)}):")
        for i, m in enumerate(members[:10], 1):
            preview = m.original_text[:80] + "..." if len(m.original_text) > 80 else m.original_text
            typer.echo(f"   {i}. {preview}")
        if len(members) > 10:
            typer.echo(f"   ... and {len(members) - 10} more")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.command()
def template(
    family_id: str = typer.Argument(..., help="Family ID to get template for"),
    extract: bool = typer.Option(False, "--extract", help="Extract template if not exists"),
):
    from packages.storage.database import get_db
    from packages.storage.repositories import FamilyRepository, TemplateRepository, PromptRepository
    from packages.core.processing import _model_to_dna
    from packages.llm import LLMClient, MockLLMClient
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        family_repo = FamilyRepository(db)
        template_repo = TemplateRepository(db)
        prompt_repo = PromptRepository(db)
        
        family = family_repo.get_by_id(family_id)
        if not family:
            typer.echo(f"❌ Family {family_id} not found")
            raise typer.Exit(1)
        
        template = template_repo.get_by_family(family_id)
        
        if not template:
            if extract:
                typer.echo("🔍 Extracting template...")
                members = prompt_repo.get_by_family(family_id)
                if not members:
                    typer.echo("❌ Family has no members")
                    raise typer.Exit(1)
                
                prompt_dnas = [_model_to_dna(m) for m in members]
                try:
                    llm_client = LLMClient()
                    extracted = asyncio.run(llm_client.extract_template(prompt_dnas))
                except Exception:
                    typer.echo("⚠️  Real LLM unavailable, using mock extraction")
                    llm_client = MockLLMClient()
                    extracted = asyncio.run(llm_client.extract_template(prompt_dnas))
                
                template_repo.create_template(
                    family_id=family_id,
                    template_text=extracted.text,
                    slots={"variables": extracted.variables, "example_values": extracted.example_values},
                    quality_score=None,
                )
                template = template_repo.get_by_family(family_id)
                typer.echo("✅ Template extracted")
            else:
                typer.echo(f"❌ Template for family {family_id} not found")
                typer.echo("💡 Run with --extract to extract template")
                raise typer.Exit(1)
        
        typer.echo(f"\n📝 Template for Family: {family.family_name}")
        typer.echo(f"   Template ID: {template.template_id}")
        typer.echo(f"\n   {template.template_text}")
        
        if template.slots.get("variables"):
            typer.echo(f"\n   Variables: {', '.join(template.slots['variables'])}")
        
        if template.slots.get("example_values"):
            typer.echo(f"\n   Example Values:")
            for var, examples in list(template.slots["example_values"].items())[:3]:
                typer.echo(f"     {var}: {examples[:2]}")
        
        if template.quality_score:
            typer.echo(f"\n   Quality Score: {template.quality_score:.2f}")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.command()
def evolve(
    prompt_id: str = typer.Argument(..., help="Prompt ID to trace evolution"),
):
    from packages.storage.database import get_db
    from packages.storage.repositories import PromptRepository, LineageRepository
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        prompt_repo = PromptRepository(db)
        lineage_repo = LineageRepository(db)
        
        prompt = prompt_repo.get_by_id(prompt_id)
        if not prompt:
            typer.echo(f"❌ Prompt {prompt_id} not found")
            raise typer.Exit(1)
        
        typer.echo(f"\n🔗 Evolution chain for prompt: {prompt_id}")
        typer.echo(f"   Text: {prompt.original_text[:80]}...")
        if prompt.family_id:
            typer.echo(f"   Family: {prompt.family_id}")
        
        chain = lineage_repo.get_lineage_chain(prompt_id)
        
        if len(chain) == 1:
            typer.echo("\n   No lineage links found (this prompt has no ancestors or descendants)")
        else:
            typer.echo(f"\n   Lineage chain ({len(chain) - 1} links):")
            
            ancestors = [c for c in chain if c.get("direction") == "ancestor"]
            descendants = [c for c in chain if c.get("direction") == "descendant"]
            
            if ancestors:
                typer.echo("\n   Ancestors (parents):")
                for link in sorted(ancestors, key=lambda x: len(x.get("path", [])), reverse=True):
                    mutation = link.get("mutation_type", "unknown")
                    conf = link.get("confidence", 0.0)
                    typer.echo(f"      ← {link['prompt_id'][:8]}... ({mutation}, conf: {conf:.2f})")
            
            typer.echo(f"\n   Current: {prompt_id[:8]}...")
            
            if descendants:
                typer.echo("\n   Descendants (children):")
                for link in sorted(descendants, key=lambda x: len(x.get("path", []))):
                    mutation = link.get("mutation_type", "unknown")
                    conf = link.get("confidence", 0.0)
                    typer.echo(f"      → {link['prompt_id'][:8]}... ({mutation}, conf: {conf:.2f})")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.command()
def stats(
    format: str = typer.Option("table", "--format", "-f", help="Output format: table or json"),
):
    from packages.storage.database import get_db
    from packages.storage.repositories import PromptRepository, FamilyRepository, TemplateRepository
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        prompt_repo = PromptRepository(db)
        family_repo = FamilyRepository(db)
        template_repo = TemplateRepository(db)
        
        total_prompts = prompt_repo.count_all()
        pending_prompts = prompt_repo.count_pending()
        total_families = family_repo.count_all()
        total_templates = template_repo.count_all()
        
        families = family_repo.get_all()
        avg_family_size = sum(f.member_count for f in families) / len(families) if families else 0
        
        latest_prompt = prompt_repo.get_latest(limit=1)
        last_ingestion = latest_prompt[0].created_at if latest_prompt else None
        
        stats_data = {
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
            "last_ingestion": last_ingestion.isoformat() if last_ingestion else None,
        }
        
        if format == "json":
            typer.echo(json.dumps(stats_data, indent=2))
        else:
            typer.echo("\n📊 System Statistics\n")
            typer.echo(f"Prompts:")
            typer.echo(f"  Total: {total_prompts}")
            typer.echo(f"  Pending: {pending_prompts}")
            typer.echo(f"  Processed: {total_prompts - pending_prompts}")
            typer.echo(f"\nFamilies:")
            typer.echo(f"  Total: {total_families}")
            typer.echo(f"  Average Size: {avg_family_size:.2f}")
            typer.echo(f"\nTemplates:")
            typer.echo(f"  Extracted: {total_templates}")
            if last_ingestion:
                typer.echo(f"\nLast Ingestion: {last_ingestion}")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.command()
def ml_process(
    csv_file: str = typer.Argument(..., help="Path to CSV file with prompts"),
    output_dir: str = typer.Option("./output", "--output", "-o", help="Output directory"),
    embedding_model: str = typer.Option("bge-large-en", "--embedding", help="Embedding model"),
    enable_reranking: bool = typer.Option(False, "--rerank", help="Enable LLM reranking"),
    enable_explanations: bool = typer.Option(False, "--explain", help="Enable LLM explanations"),
):
    from packages.ml_core.pipeline import MLPipeline
    from packages.ml_core.config import MLConfig
    
    csv_path = Path(csv_file)
    if not csv_path.exists():
        typer.echo(f"❌ Error: CSV file not found: {csv_file}", err=True)
        raise typer.Exit(1)
    
    config = MLConfig.from_env()
    config.output_dir = output_dir
    config.embedding_model = embedding_model
    config.enable_reranking = enable_reranking
    config.enable_explanations = enable_explanations
    
    typer.echo("🚀 Starting ML Core Engine Pipeline...")
    typer.echo(f"  Input: {csv_file}")
    typer.echo(f"  Output: {output_dir}")
    typer.echo(f"  Embedding model: {embedding_model}")
    typer.echo(f"  Reranking: {'enabled' if enable_reranking else 'disabled'}")
    typer.echo(f"  Explanations: {'enabled' if enable_explanations else 'disabled'}")
    typer.echo()
    
    try:
        pipeline = MLPipeline(config)
        asyncio.run(pipeline.run(csv_path))
        typer.echo("\n✅ ML Core Engine processing complete!")
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("portkey-worker")
def portkey_worker(
    interval: int = typer.Option(10, help="Ingestion interval in minutes"),
):
    import asyncio
    from packages.ingestion.worker import run_worker
    
    typer.echo(f"🚀 Starting Portkey Ingestion Worker (every {interval} min)...")
    try:
        asyncio.run(run_worker(interval_minutes=interval))
    except KeyboardInterrupt:
        typer.echo("\n🛑 Worker stopped.")


@app.command("full-classify")
def full_classify():
    """
    Run full HDBSCAN classification on all prompts.
    
    This is the WEEKLY job that:
    - Embeds all prompts
    - Runs HDBSCAN clustering
    - Creates/updates PromptFamily records
    - Updates all family assignments
    """
    from packages.ml_core.full_classifier import run_full_classification
    
    typer.echo("🧠 Starting Full Classification (HDBSCAN)...")
    typer.echo("This may take a while depending on the number of prompts.\n")
    
    try:
        stats = run_full_classification()
        
        typer.echo("\n✅ Full Classification Complete!")
        typer.echo(f"   Total prompts: {stats['total_prompts']}")
        typer.echo(f"   Newly embedded: {stats['embedded']}")
        typer.echo(f"   Clusters created: {stats['clusters_created']}")
        typer.echo(f"   Prompts assigned: {stats['prompts_assigned']}")
        typer.echo(f"   Unclustered: {stats['unclustered']}")
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("clear-embeddings")
def clear_embeddings():
    """
    Clear all embedding vectors from the database.
    
    Use this when switching embedding models to avoid dimension mismatch errors.
    After clearing, run full-classify to re-embed all prompts.
    """
    from packages.storage.database import get_db
    from packages.storage.repositories import PromptRepository
    
    typer.echo("⚠️  This will clear ALL embedding vectors from the database.")
    confirm = typer.confirm("Are you sure you want to continue?")
    
    if not confirm:
        typer.echo("Aborted.")
        raise typer.Exit(0)
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        prompt_repo = PromptRepository(db)
        cleared = prompt_repo.clear_all_embeddings()
        typer.echo(f"✅ Cleared {cleared} embeddings.")
        typer.echo("💡 Now run: python -m apps.cli.main full-classify")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.command("classify-worker")
def classify_worker(
    interval: int = typer.Option(10, help="Classification interval in minutes"),
    batch_size: int = typer.Option(500, help="Minimum prompts to trigger processing"),
):
    """
    Run the incremental classification worker.
    
    This is the DAILY job that:
    - Checks for new prompts every X minutes
    - Assigns new prompts to existing families
    - Uses centroids from full-classify
    """
    import asyncio
    from packages.ml_core.incremental_worker import run_worker
    
    typer.echo(f"🧠 Starting Incremental Classification Worker...")
    typer.echo(f"   Interval: every {interval} min")
    typer.echo(f"   Batch size: {batch_size} prompts minimum")
    typer.echo(f"   Loading embedding model (this may take a minute on first run)...\n")
    
    try:
        asyncio.run(run_worker(interval_minutes=interval, batch_size=batch_size))
    except KeyboardInterrupt:
        typer.echo("\n🛑 Worker stopped.")


@app.command("migrate-db")
def migrate_db():
    """
    Apply manual schema migrations (Fix for missing columns).
    """
    from packages.storage.database import get_db
    from sqlalchemy import text
    
    typer.echo("🔄 Checking database schema...")
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        # Check if column exists
        try:
            db.execute(text("SELECT member_count_at_creation FROM templates LIMIT 1"))
            typer.echo("✅ Column 'member_count_at_creation' already exists.")
        except Exception:
            typer.echo("⚠️  Column 'member_count_at_creation' missing. Adding it...")
            db.execute(text("ALTER TABLE templates ADD COLUMN member_count_at_creation INTEGER DEFAULT 0"))
            db.commit()
            typer.echo("✅ Successfully added column 'member_count_at_creation'.")
            
    except Exception as e:
        typer.echo(f"❌ Migration failed: {str(e)}", err=True)
        raise typer.Exit(1)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.command("update-templates")
def update_templates():
    """
    Job to analyze ALL families and generate/update templates.
    """
    typer.echo("🚀 Starting Template Update Job...")
    typer.echo("   Loading modules...")
    
    import asyncio
    try:
        from packages.storage.database import get_db
        from packages.ml_core.template_generator import TemplateGenerator
        typer.echo("   Modules loaded.")
    except Exception as e:
        typer.echo(f"❌ Error loading modules: {e}")
        raise typer.Exit(1)
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        template_generator = TemplateGenerator(db)
        typer.echo("   Scanning families...")
        
        # We need async loop
        updated_count = asyncio.run(template_generator.process_all_families())
        
        if updated_count > 0:
            typer.echo(f"\n✅ Successfully created/updated {updated_count} templates.")
        else:
            typer.echo("\n✨ No templates needed updates.")
            
    except Exception as e:
        typer.echo(f"❌ Error during template updates: {str(e)}", err=True)
        raise typer.Exit(1)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


if __name__ == "__main__":
    app()
