# ABOUTME: Implements the `reka qa` command for video question-answering
# ABOUTME: Registers as a direct root command (not a nested command group)

from typing import Annotated

import typer

from reka.commands._common import api_command, emit_result, make_client

@api_command
def qa(
    video_id: Annotated[str, typer.Option("--video-id", help="ID of the video to query")],
    question: Annotated[str, typer.Option("--question", help="Question to ask about the video")],
) -> None:
    """Ask a question about a video."""
    client = make_client()
    body = {
        "video_id": video_id,
        "messages": [{"role": "user", "content": question}],
        "stream": False,
    }
    result = client.post("/v1/qa/chat", json=body)
    emit_result(result)


def register(root: typer.Typer) -> None:
    root.command("qa", help="Ask questions about a video.")(qa)
