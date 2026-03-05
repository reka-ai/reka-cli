# ABOUTME: Entry point for the reka CLI; registers subcommands and global options
# ABOUTME: Global state is populated by @app.callback() and consumed by all commands

import sys
from dataclasses import dataclass, field
from typing import Annotated, Optional

import typer

from reka.commands import configure, groups, qa, search, videos
from reka.output import ApiError, emit_error

app = typer.Typer(
    name="reka",
    help="Reka Vision Agent CLI — agent-optimized interface to the Reka API.",
    no_args_is_help=True,
    add_completion=False,
)


@dataclass
class State:
    token: Optional[str] = None
    env: str = "prod"
    base_url: Optional[str] = None
    format: str = "json"
    output_file: Optional[str] = None
    verbose: bool = False
    timeout: int = 30
    wait: bool = False
    wait_timeout: int = 300


# Singleton state shared with subcommands
state = State()


@app.callback()
def main(
    token: Annotated[Optional[str], typer.Option(envvar="REKA_API_TOKEN", help="API token")] = None,
    env: Annotated[str, typer.Option(envvar="REKA_ENV", help="API environment")] = "prod",
    base_url: Annotated[Optional[str], typer.Option(envvar="REKA_BASE_URL", help="Override base URL")] = None,
    format: Annotated[str, typer.Option(help="Output format: json or text")] = "json",
    output_file: Annotated[Optional[str], typer.Option(help="Write output to file")] = None,
    verbose: Annotated[bool, typer.Option(help="Show HTTP debug info on stderr")] = False,
    timeout: Annotated[int, typer.Option(help="Request timeout in seconds")] = 30,
    wait: Annotated[bool, typer.Option(help="Poll until terminal state for async operations")] = False,
    wait_timeout: Annotated[int, typer.Option(help="Max wait time in seconds when --wait is used")] = 300,
) -> None:
    state.token = token
    state.env = env
    state.base_url = base_url
    state.format = format
    state.output_file = output_file
    state.verbose = verbose
    state.timeout = timeout
    state.wait = wait
    state.wait_timeout = wait_timeout


app.add_typer(configure.app, name="configure")
app.add_typer(videos.app, name="videos")
app.add_typer(search.app, name="search")
app.add_typer(qa.app, name="qa")
app.add_typer(groups.app, name="groups")


def _run() -> None:
    try:
        app()
    except ApiError as e:
        emit_error(e.error)
        sys.exit(e.exit_code)
    except SystemExit:
        raise
    except Exception as e:
        emit_error({"type": "server_error", "message": str(e)})
        sys.exit(7)


if __name__ == "__main__":
    _run()
