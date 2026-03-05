# ABOUTME: Implements the `reka streams` command group (add, get, delete, list)
# ABOUTME: All endpoints are POST-based as defined by the streams API

from typing import Annotated, Optional

import typer

from reka.commands._common import api_command, emit_result, make_client

app = typer.Typer(help="Manage streams.", no_args_is_help=True)


@app.command("add")
@api_command
def add_stream(
    url: Annotated[str, typer.Option("--url", help="Stream URL (e.g. rtsp://...)")],
) -> None:
    """Add a stream for monitoring."""
    client = make_client()
    result = client.post("/v1/streams/add", json={"stream_url": url})
    emit_result(result)


@app.command("get")
@api_command
def get_stream(
    stream_id: Annotated[str, typer.Argument(help="Stream ID")],
) -> None:
    """Get a stream by ID."""
    client = make_client()
    result = client.post("/v1/streams/get", json={"stream_id": stream_id})
    emit_result(result)


@app.command("delete")
@api_command
def delete_stream(
    stream_id: Annotated[str, typer.Argument(help="Stream ID")],
) -> None:
    """Delete a stream by ID."""
    client = make_client()
    result = client.post("/v1/streams/delete", json={"stream_id": stream_id})
    emit_result(result)


@app.command("list")
@api_command
def list_streams(
    limit: Annotated[Optional[int], typer.Option("--limit", help="Max results")] = None,
    offset: Annotated[Optional[int], typer.Option("--offset", help="Pagination offset")] = None,
) -> None:
    """List all streams."""
    client = make_client()
    payload: dict = {}
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    response = client.post("/v1/streams/list", json=payload)
    emit_result(response.get("streams", []))
