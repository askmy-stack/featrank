"""Typer CLI entrypoint for featrank."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console

app = typer.Typer(
    name="featrank",
    help="Semantic feature request deduplication + priority ranking.",
    add_completion=False,
)
console = Console()


def _check_env() -> None:
    """Warn about missing optional env vars on startup."""
    from featrank.config import settings

    if not settings.groq_api_key and settings.llm_provider == "groq":
        logger.warning(
            "GROQ_API_KEY is not set. LLM features will use TF-IDF fallbacks. "
            "Set LLM_PROVIDER=ollama for local inference."
        )


@app.command()
def ingest(
    source: str = typer.Option("csv", help="Source type: csv | intercom | zendesk | github"),
    file: Optional[Path] = typer.Option(None, help="Path to CSV file (required for source=csv)"),
    output: Path = typer.Option("data/raw/requests.json", help="Output path for JSON"),
) -> None:
    """Ingest feature requests from a source and save as JSON."""
    _check_env()
    from featrank.schemas import RawRequest

    requests: list[RawRequest] = []

    if source == "csv":
        if file is None:
            typer.echo("--file is required for source=csv", err=True)
            raise typer.Exit(1)
        from featrank.ingest.csv_connector import CSVConnector

        requests = CSVConnector(file).fetch_all()
    elif source == "github":
        from featrank.ingest.github import GitHubConnector

        requests = GitHubConnector().fetch_all()
    elif source == "intercom":
        from featrank.ingest.intercom import IntercomConnector

        requests = IntercomConnector().fetch_all()
    elif source == "zendesk":
        from featrank.ingest.zendesk import ZendeskConnector

        requests = ZendeskConnector().fetch_all()
    else:
        typer.echo(f"Unknown source: {source}", err=True)
        raise typer.Exit(1)

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump([r.model_dump(mode="json") for r in requests], f, indent=2)

    console.print(f"[green]✓[/green] Ingested {len(requests)} requests → {output}")


@app.command()
def cluster(
    input: Path = typer.Option("data/raw/requests.json", help="Input JSON from ingest"),
    output: Path = typer.Option("data/processed/clusters.json", help="Output clusters JSON"),
) -> None:
    """Clean, embed, and cluster feature requests."""
    _check_env()
    from featrank.pipeline.cleaner import TextCleaner
    from featrank.pipeline.clusterer import HDBSCANClusterer
    from featrank.pipeline.embedder import Embedder
    from featrank.pipeline.labeler import ClusterLabeler
    from featrank.schemas import RawRequest

    with open(input) as f:
        raw = json.load(f)
    requests = [RawRequest(**r) for r in raw]

    cleaner = TextCleaner()
    embedder = Embedder()
    clusterer_obj = HDBSCANClusterer()
    labeler = ClusterLabeler()

    kept, cleaned_texts = cleaner.clean_requests(requests)
    embeddings = embedder.embed(cleaned_texts)
    clustered = clusterer_obj.fit_predict(kept, embeddings, cleaned_texts)
    clusters = labeler.build_clusters(clustered)

    noise_count = sum(1 for r in clustered if r.cluster_id == -1)

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump([c.model_dump(mode="json") for c in clusters], f, indent=2)

    console.print(
        f"[green]✓[/green] {len(clusters)} clusters, {noise_count} noise → {output}"
    )


@app.command()
def rank(
    clusters: Path = typer.Option("data/processed/clusters.json"),
    roadmap: Optional[Path] = typer.Option(None, help="Plain-text roadmap file"),
    crm: Optional[Path] = typer.Option(None, help="CRM CSV with user_id,mrr columns"),
    output: Path = typer.Option("data/processed/ranked.json"),
) -> None:
    """Score and rank feature clusters by business value."""
    _check_env()
    from featrank.schemas import FeatureCluster
    from featrank.scoring.ranker import CompositeRanker

    with open(clusters) as f:
        raw = json.load(f)
    cluster_objs = [FeatureCluster(**c) for c in raw]

    roadmap_text: Optional[str] = None
    if roadmap and roadmap.exists():
        roadmap_text = roadmap.read_text()

    ranker = CompositeRanker()
    ranked = ranker.rank(cluster_objs, roadmap_text=roadmap_text)

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump([c.model_dump(mode="json") for c in ranked], f, indent=2)

    console.print(f"[green]✓[/green] {len(ranked)} clusters ranked → {output}")


@app.command()
def report(
    input: Path = typer.Option("data/processed/ranked.json"),
    format: str = typer.Option("markdown", help="Output format: markdown | json | slack"),
    output: Optional[Path] = typer.Option(None, help="Write to file (default: stdout)"),
) -> None:
    """Generate a priority report from ranked clusters."""
    from featrank.schemas import PrioritizedCluster

    with open(input) as f:
        raw = json.load(f)
    ranked = [PrioritizedCluster(**c) for c in raw]

    if format == "markdown":
        from featrank.report.markdown import MarkdownFormatter

        content = MarkdownFormatter().format(ranked)
    elif format == "json":
        from featrank.report.json_report import JSONFormatter

        content = JSONFormatter().format(ranked)
    elif format == "slack":
        from featrank.report.slack import SlackFormatter

        content = SlackFormatter().format(ranked)
    else:
        typer.echo(f"Unknown format: {format}", err=True)
        raise typer.Exit(1)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content)
        console.print(f"[green]✓[/green] Report written to {output}")
    else:
        print(content)


@app.command()
def run(
    source: str = typer.Option("csv", help="Source type"),
    file: Optional[Path] = typer.Option(None, help="CSV input file"),
    roadmap: Optional[Path] = typer.Option(None),
    crm: Optional[Path] = typer.Option(None),
    format: str = typer.Option("markdown"),
) -> None:
    """Run the full pipeline in one shot."""
    _check_env()
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        raw_path = tmp / "requests.json"
        clusters_path = tmp / "clusters.json"
        ranked_path = tmp / "ranked.json"

        ingest.callback(source=source, file=file, output=raw_path)  # type: ignore[arg-type]
        cluster.callback(input=raw_path, output=clusters_path)  # type: ignore[arg-type]
        rank.callback(clusters=clusters_path, roadmap=roadmap, crm=crm, output=ranked_path)  # type: ignore[arg-type]
        report.callback(input=ranked_path, format=format, output=None)  # type: ignore[arg-type]


@app.command()
def demo() -> None:
    """Run the full pipeline on built-in sample data."""
    fixtures = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_requests.csv"
    if not fixtures.exists():
        console.print("[yellow]Fixtures not found. Generating...[/yellow]")
        from scripts.generate_fixtures import generate

        generate(count=200, output=fixtures)

    console.print(f"[blue]Running demo on {fixtures}[/blue]")
    ctx = typer.get_current_context()
    ctx.invoke(run, source="csv", file=fixtures, roadmap=None, crm=None, format="markdown")


@app.command()
def serve() -> None:
    """Start the FastAPI REST API server."""
    import uvicorn

    from featrank.config import settings

    console.print(f"[green]Starting featrank API on {settings.api_host}:{settings.api_port}[/green]")
    uvicorn.run(
        "featrank.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    app()
