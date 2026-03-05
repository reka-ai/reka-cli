# ABOUTME: Implements the `reka tag` command for generating metadata tags on indexed videos
# ABOUTME: Registers as a direct root command (not a nested command group)

from typing import Annotated

import typer

from reka.commands._common import api_command, emit_result, make_client

@api_command
def tag(
    video_id: Annotated[str, typer.Option("--video-id", help="ID of the video to tag")],
) -> None:
    """Generate metadata tags for an indexed video."""
    client = make_client()
    result = client.post("/v1/qa/indexedtag", json={"video_id": video_id})
    emit_result(result)


def register(root: typer.Typer) -> None:
    root.command("tag", help="Generate metadata tags for an indexed video.")(tag)
