"""
CLI application for Evolv - Prompt Genome Project
"""

import typer
from pathlib import Path
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = typer.Typer(
    name="genome",
    help="Evolv CLI - Your prompts, but smarter every week",
    add_completion=False,
)


@app.command()
def ingest(
    file: str = typer.Argument(..., help="Path to file containing prompts"),
    source: str = typer.Option("file", help="Source type: file, portkey, git"),
):
    """Ingest prompts from a file, Portkey logs, or git repository"""
    typer.echo(f"Ingesting prompts from {source}: {file}")
    # TODO: Implement ingestion logic
    typer.echo("✅ Ingestion complete")


@app.command()
def prompts(limit: int = 20):
    """List latest ingested prompts"""
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
def run():
    """Process pending prompts (clustering, template extraction)"""
    typer.echo("Processing pending prompts...")
    # TODO: Implement processing logic
    typer.echo("✅ Processing complete")


@app.command()
def families():
    """List all prompt families"""
    typer.echo("Fetching prompt families...")
    # TODO: Implement family listing
    typer.echo("No families found yet. Ingest some prompts first!")


@app.command()
def family(
    family_id: str = typer.Argument(..., help="Family ID to inspect"),
):
    """Show details for a specific prompt family"""
    typer.echo(f"Fetching family: {family_id}")
    # TODO: Implement family details
    typer.echo(f"Family {family_id} not found")


@app.command()
def template(
    family_id: str = typer.Argument(..., help="Family ID to get template for"),
):
    """Show canonical template for a prompt family"""
    typer.echo(f"Fetching template for family: {family_id}")
    # TODO: Implement template retrieval
    typer.echo(f"Template for {family_id} not found")


@app.command()
def evolve(
    prompt_id: str = typer.Argument(..., help="Prompt ID to trace evolution"),
):
    """Show evolution chain for a prompt"""
    typer.echo(f"Tracing evolution for prompt: {prompt_id}")
    # TODO: Implement evolution tracking
    typer.echo(f"Evolution chain for {prompt_id} not found")


@app.command()
def stats():
    """Show system-wide statistics"""
    typer.echo("System Statistics:")
    # TODO: Implement statistics
    typer.echo("  Prompts: 0")
    typer.echo("  Families: 0")
    typer.echo("  Templates: 0")


@app.command()
def ml_process(
    csv_file: str = typer.Argument(..., help="Path to CSV file with prompts"),
    output_dir: str = typer.Option("./output", "--output", "-o", help="Output directory"),
    embedding_model: str = typer.Option("bge-large-en", "--embedding", help="Embedding model"),
    enable_reranking: bool = typer.Option(False, "--rerank", help="Enable LLM reranking"),
    enable_explanations: bool = typer.Option(False, "--explain", help="Enable LLM explanations"),
):
    """
    Process prompts through ML Core Engine (Module C)
    
    This is an OFFLINE/BATCH pipeline that:
    - Normalizes prompts
    - Generates semantic embeddings
    - Clusters prompts into families
    - Builds FAISS retrieval index
    - Optionally reranks and explains (if enabled)
    
    Input: CSV file with 'prompt' column
    Output: JSON artifacts and FAISS index in output directory
    """
    from packages.ml_core.pipeline import MLPipeline
    from packages.ml_core.config import MLConfig
    
    csv_path = Path(csv_file)
    if not csv_path.exists():
        typer.echo(f"❌ Error: CSV file not found: {csv_file}", err=True)
        raise typer.Exit(1)
    
    # Create config
    config = MLConfig.from_env()
    config.output_dir = output_dir
    config.embedding_model = embedding_model  # type: ignore
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
    """
    Run the Portkey ingestion background worker.
    Fetches logs every X minutes (default: 10).
    """
    import asyncio
    from packages.ingestion.worker import run_worker
    
    typer.echo(f"🚀 Starting Portkey Ingestion Worker (every {interval} min)...")
    try:
        asyncio.run(run_worker(interval_minutes=interval))
    except KeyboardInterrupt:
        typer.echo("\n🛑 Worker stopped.")


if __name__ == "__main__":
    app()
