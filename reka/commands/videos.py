# ABOUTME: Implements the `reka videos` command group (upload, list, get, delete)
# ABOUTME: Supports --wait polling for upload indexing completion

from pathlib import Path
from typing import Annotated, Optional

import typer

from reka.commands._common import api_command, emit_result, make_client
from reka.output import ApiError

app = typer.Typer(help="Manage videos.", no_args_is_help=True)

# Terminal states for video indexing
_TERMINAL_STATES = {"indexed", "index_failed", "upload_failed", "download_failed"}


@app.command("upload")
@api_command
def upload(
    file: Annotated[Optional[Path], typer.Option("--file", help="Local file to upload")] = None,
    url: Annotated[Optional[str], typer.Option("--url", help="URL to download and index")] = None,
    name: Annotated[Optional[str], typer.Option("--name", help="Video name")] = None,
    index: Annotated[bool, typer.Option("--index/--no-index", help="Index video after upload")] = True,
    group_id: Annotated[Optional[str], typer.Option("--group-id", help="Group to assign video to")] = None,
) -> None:
    """Upload a video from a file or URL."""
    from reka.main import state

    if not file and not url:
        typer.echo("Error: provide --file or --url", err=True)
        raise typer.Exit(1)
    if file and url:
        typer.echo("Error: provide only one of --file or --url", err=True)
        raise typer.Exit(1)
    if file and not name:
        typer.echo("Error: --name is required for file uploads", err=True)
        raise typer.Exit(1)

    client = make_client()

    form_data: dict = {"index": str(index).lower()}
    if name:
        form_data["video_name"] = name
    if group_id:
        form_data["group_id"] = group_id

    if url:
        form_data["video_url"] = url
        result = client.post("/v1/videos/upload", data=form_data)
    else:
        with open(file, "rb") as f:
            result = client.post("/v1/videos/upload", data=form_data, files={"file": (file.name, f)})

    if state.wait:
        video_id = result.get("video_id")
        result = client.wait_for_status(
            poll_fn=lambda: client.get(f"/v1/videos/{video_id}"),
            status_field="status",
            terminal_states=_TERMINAL_STATES,
            timeout=state.wait_timeout,
        )
        status = result.get("status")
        if status in {"index_failed", "upload_failed", "download_failed"}:
            raise ApiError(exit_code=7, error={"type": "server_error", "message": f"Video processing failed: {status}"})

    emit_result(result)


@app.command("list")
@api_command
def list_videos() -> None:
    """List all videos."""
    client = make_client()
    response = client.get("/v1/videos")
    emit_result(response.get("results", []))


@app.command("get")
@api_command
def get_video(
    video_id: Annotated[str, typer.Argument(help="Video ID")],
) -> None:
    """Get a video by ID."""
    client = make_client()
    result = client.get(f"/v1/videos/{video_id}")
    emit_result(result)


@app.command("delete")
@api_command
def delete_video(
    video_id: Annotated[str, typer.Argument(help="Video ID")],
) -> None:
    """Delete a video by ID."""
    client = make_client()
    result = client.delete(f"/v1/videos/{video_id}")
    emit_result(result)
