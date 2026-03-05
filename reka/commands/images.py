# ABOUTME: Implements the `reka images` command group (upload, list, get, delete, search)
# ABOUTME: Upload supports both local files and URLs via multipart form with JSON metadata

import json
from pathlib import Path
from typing import Annotated, Optional

import typer

from reka.commands._common import api_command, emit_result, make_client

app = typer.Typer(help="Manage images.", no_args_is_help=True)


@app.command("upload")
@api_command
def upload(
    files: Annotated[Optional[str], typer.Option("--files", help="Comma-separated local file paths")] = None,
    urls: Annotated[Optional[str], typer.Option("--urls", help="Comma-separated URLs to index")] = None,
) -> None:
    """Upload images from local files or URLs."""
    if not files and not urls:
        typer.echo("Error: provide --files or --urls", err=True)
        raise typer.Exit(1)

    client = make_client()

    if urls:
        url_list = [u.strip() for u in urls.split(",")]
        requests_meta = [{"indexing_config": {"index": True}, "metadata": {}} for _ in url_list]
        metadata = json.dumps({"requests": requests_meta, "image_urls": url_list})
        result = client.post("/v1/images/upload", data={"metadata": metadata}, files=None)
    else:
        file_list = [Path(p.strip()) for p in files.split(",")]
        requests_meta = [{"indexing_config": {"index": True}, "metadata": {}} for _ in file_list]
        metadata = json.dumps({"requests": requests_meta})
        opened = [(f.name, open(f, "rb")) for f in file_list]
        try:
            result = client.post(
                "/v1/images/upload",
                data={"metadata": metadata},
                files=[("images", (name, fh)) for name, fh in opened],
            )
        finally:
            for _, fh in opened:
                fh.close()

    emit_result(result)


@app.command("list")
@api_command
def list_images(
    limit: Annotated[Optional[int], typer.Option("--limit", help="Max results")] = None,
    offset: Annotated[Optional[int], typer.Option("--offset", help="Pagination offset")] = None,
) -> None:
    """List all images."""
    client = make_client()
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    response = client.get("/v1/images", params=params or None)
    emit_result(response.get("results", []))


@app.command("get")
@api_command
def get_image(
    image_id: Annotated[str, typer.Argument(help="Image ID")],
) -> None:
    """Get an image by ID."""
    client = make_client()
    result = client.get(f"/v1/images/{image_id}")
    emit_result(result)


@app.command("delete")
@api_command
def delete_image(
    image_id: Annotated[str, typer.Argument(help="Image ID")],
) -> None:
    """Delete an image by ID."""
    client = make_client()
    result = client.delete(f"/v1/images/{image_id}")
    emit_result(result)


@app.command("search")
@api_command
def search_images(
    query: Annotated[str, typer.Option("--query", help="Search query text")],
    max_results: Annotated[Optional[int], typer.Option("--max-results", help="Maximum results")] = None,
) -> None:
    """Search images by text query."""
    client = make_client()
    payload: dict = {"query": query}
    if max_results is not None:
        payload["max_results"] = max_results
    result = client.post("/v1/images/search", json=payload)
    emit_result(result)
