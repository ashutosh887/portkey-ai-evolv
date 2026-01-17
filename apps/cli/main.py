"""
CLI application for Evolv - Prompt Genome Project
"""

import typer

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
