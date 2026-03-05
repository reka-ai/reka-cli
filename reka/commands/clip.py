# ABOUTME: Implements the `reka clip` command group (create, list, get, delete)
# ABOUTME: Maps to /v1/clips endpoints for generating highlight clips from videos

from typing import Annotated, Optional

import typer

from reka.commands._common import api_command, emit_result, make_client
from reka.output import ApiError

app = typer.Typer(help="Manage clip generations.", no_args_is_help=True)

_TERMINAL_STATES = {"completed", "failed"}


@app.command("create")
@api_command
def create_clip(
    video_urls: Annotated[str, typer.Option("--video-urls", help="Comma-separated video URLs to generate a clip from")],
    prompt: Annotated[Optional[str], typer.Option("--prompt", help="Prompt describing the desired clip")] = None,
) -> None:
    """Create a clip generation from one or more videos."""
    from reka.main import state

    client = make_client()
    payload: dict = {
        "video_urls": [u.strip() for u in video_urls.split(",")],
    }
    if prompt:
        payload["prompt"] = prompt

    result = client.post("/v1/clips", json=payload)

    if state.wait:
        clip_id = result.get("id")
        result = client.wait_for_status(
            poll_fn=lambda: client.get(f"/v1/clips/{clip_id}"),
            status_field="status",
            terminal_states=_TERMINAL_STATES,
            timeout=state.wait_timeout,
        )
        if result.get("status") == "failed":
            raise ApiError(exit_code=7, error={"type": "server_error", "message": "Clip generation failed"})

    emit_result(result)


@app.command("list")
@api_command
def list_clips() -> None:
    """List all clip generations."""
    client = make_client()
    response = client.get("/v1/clips")
    emit_result(response.get("items", []))


@app.command("get")
@api_command
def get_clip(
    clip_id: Annotated[str, typer.Argument(help="Clip generation ID")],
) -> None:
    """Get a clip generation by ID."""
    client = make_client()
    result = client.get(f"/v1/clips/{clip_id}")
    emit_result(result)


@app.command("delete")
@api_command
def delete_clip(
    clip_id: Annotated[str, typer.Argument(help="Clip generation ID")],
) -> None:
    """Delete a clip generation by ID."""
    client = make_client()
    result = client.delete(f"/v1/clips/{clip_id}")
    emit_result(result)
