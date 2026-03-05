# ABOUTME: Implements the `reka generations` command group (create, get)
# ABOUTME: No list or delete endpoints exist in the API

from typing import Annotated, Optional

import typer

from reka.commands._common import api_command, emit_result, make_client
from reka.output import ApiError

app = typer.Typer(help="Manage video generations.", no_args_is_help=True)

# Terminal states for generation polling
_TERMINAL_STATES = {"completed", "ready", "failed", "skipped"}


@app.command("create")
@api_command
def create_generation(
    prompt: Annotated[Optional[str], typer.Option("--prompt", help="Generation prompt")] = None,
    video_ids: Annotated[Optional[str], typer.Option("--video-ids", help="Comma-separated video IDs")] = None,
    template: Annotated[Optional[str], typer.Option("--template", help="Template: compilation, moments, voiceover, trailer")] = None,
) -> None:
    """Create a video generation."""
    from reka.main import state

    client = make_client()
    payload: dict = {}
    if prompt:
        payload["prompt"] = prompt
    if video_ids:
        payload["video_ids"] = [v.strip() for v in video_ids.split(",")]
    if template:
        payload["template"] = template

    result = client.post("/v1/generations", json=payload)

    if state.wait:
        generation_id = result.get("id")
        result = client.wait_for_status(
            poll_fn=lambda: client.get(f"/v1/generations/{generation_id}"),
            status_field="status",
            terminal_states=_TERMINAL_STATES,
            timeout=state.wait_timeout,
        )
        if result.get("status") in {"failed", "skipped"}:
            raise ApiError(exit_code=7, error={"type": "server_error", "message": f"Generation failed: {result.get('status')}"})

    emit_result(result)


@app.command("get")
@api_command
def get_generation(
    generation_id: Annotated[str, typer.Argument(help="Generation ID")],
) -> None:
    """Get a generation by ID."""
    client = make_client()
    result = client.get(f"/v1/generations/{generation_id}")
    emit_result(result)
