# ABOUTME: Implements the `reka groups` command group (create, list, get, delete)
# ABOUTME: Maps to /v1/videos/groups endpoints

from typing import Annotated

import typer

from reka.commands._common import api_command, emit_result, make_client

app = typer.Typer(help="Manage video groups.", no_args_is_help=True)


@app.command("create")
@api_command
def create(
    name: Annotated[str, typer.Option("--name", help="Group name")],
) -> None:
    """Create a new video group."""
    client = make_client()
    result = client.post("/v1/videos/groups", json={"name": name})
    emit_result(result)


@app.command("list")
@api_command
def list_groups() -> None:
    """List all video groups."""
    client = make_client()
    response = client.get("/v1/videos/groups")
    emit_result(response.get("results", []))


@app.command("get")
@api_command
def get_group(
    group_id: Annotated[str, typer.Argument(help="Group ID")],
) -> None:
    """Get a video group by ID."""
    client = make_client()
    result = client.get(f"/v1/videos/groups/{group_id}")
    emit_result(result)


@app.command("delete")
@api_command
def delete_group(
    group_id: Annotated[str, typer.Argument(help="Group ID")],
) -> None:
    """Delete a video group by ID."""
    client = make_client()
    result = client.delete(f"/v1/videos/groups/{group_id}")
    emit_result(result)
