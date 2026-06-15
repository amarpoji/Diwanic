"""Typer-based CLI for Diwanic."""
import typer
from diwanic.pipelines.flows.full_pipeline_flow import full_pipeline_flow
import uvicorn

app = typer.Typer(help="Diwanic CLI - Arabic Poetry Search System")

@app.command()
def run_pipeline(
    config: str = typer.Option("configs/poets.yaml", help="Path to poets config YAML"),
    max_poems: int = typer.Option(30, help="Max poems to scrape per poet"),
):
    """Run the full data pipeline (Scrape -> Preprocess -> Embed -> Ingest)."""
    typer.echo("🚀 Starting full pipeline flow...")
    full_pipeline_flow(poets_config=config, max_poems=max_poems)
    typer.echo("✅ Pipeline completed successfully.")

@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind the server to"),
    port: int = typer.Option(8000, help="Port to bind the server to"),
    reload: bool = typer.Option(True, help="Enable auto-reload for development"),
):
    """Start the FastAPI server."""
    typer.echo(f"🌐 Starting API server on {host}:{port}...")
    uvicorn.run("diwanic.app.main:app", host=host, port=port, reload=reload)

@app.command()
def search(query: str = typer.Argument(..., help="Search query (Arabic)")):
    """Perform a hybrid search from the CLI."""
    from diwanic.search.engine import HybridSearchEngineV2
    from diwanic.search.router import IntentRouter
    
    router = IntentRouter()
    engine = HybridSearchEngineV2()
    
    typer.echo(f"🔍 Searching for: {query}")
    plan = router.analyze_query(query)
    results = engine.search(plan)
    
    if not results:
        typer.echo("❌ No results found.")
    else:
        for i, res in enumerate(results):
            typer.echo(f"\n[{i+1}] {res.title} - {res.poet} ({res.score:.4f})")
            # Show a snippet of original text
            snippet = res.original_text[:100].replace('\n', ' ')
            typer.echo(f"    {snippet}...")
            
    engine.close()

if __name__ == "__main__":
    app()
