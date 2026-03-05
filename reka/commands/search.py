# ABOUTME: Implements the `reka search` command group (embedding and hybrid search)
# ABOUTME: Sends SearchRequest JSON to /v1/videos/search

from typing import Annotated, Optional

import typer

from reka.commands._common import api_command, emit_result, make_client

app = typer.Typer(help="Search video content.", invoke_without_command=True, no_args_is_help=False)


@app.callback(invoke_without_command=True)
@api_command
def search(
    ctx: typer.Context,
    query: Annotated[Optional[str], typer.Option("--query", help="Search query text")] = None,
    max_results: Annotated[int, typer.Option("--max-results", help="Maximum results to return")] = 10,
    video_ids: Annotated[Optional[str], typer.Option("--video-ids", help="Comma-separated video IDs to search within")] = None,
    threshold: Annotated[Optional[float], typer.Option("--threshold", help="Minimum similarity score (0-1)")] = None,
    report: Annotated[bool, typer.Option("--report", help="Generate a summary report of results")] = False,
) -> None:
    """Embedding-based semantic search across video content."""
    if ctx.invoked_subcommand is not None:
        return
    if query is None:
        typer.echo("Error: --query is required", err=True)
        raise typer.Exit(1)

    client = make_client()
    body: dict = {
        "query": query,
        "max_results": max_results,
        "generate_report": report,
    }
    if video_ids:
        body["video_ids"] = [v.strip() for v in video_ids.split(",")]
    if threshold is not None:
        body["threshold"] = threshold

    result = client.post("/v1/videos/search", json=body)
    emit_result(result)


@app.command("hybrid")
@api_command
def hybrid(
    query: Annotated[str, typer.Option("--query", help="Search query text")],
    max_results: Annotated[int, typer.Option("--max-results", help="Maximum results to return")] = 10,
    video_ids: Annotated[Optional[str], typer.Option("--video-ids", help="Comma-separated video IDs to search within")] = None,
) -> None:
    """Hybrid search combining embedding and keyword matching."""
    client = make_client()
    body: dict = {
        "query": query,
        "max_results": max_results,
    }
    if video_ids:
        body["video_ids"] = [v.strip() for v in video_ids.split(",")]

    result = client.post("/v1/videos/search/hybrid", json=body)
    emit_result(result)
