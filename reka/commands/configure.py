# ABOUTME: Implements the `reka configure` command for saving API credentials
# ABOUTME: Writes token, environment, and optional base URL to ~/.reka/config.json

from typing import Annotated, Optional

import typer

from reka.config import Config, DEFAULT_CONFIG_PATH, save_config

app = typer.Typer(help="Save API credentials to the config file.", invoke_without_command=True)


@app.callback(invoke_without_command=True)
def configure(
    token: Annotated[str, typer.Option("--token", help="API token to save")],
    env: Annotated[str, typer.Option("--env", help="Environment: prod or staging")] = "prod",
    base_url: Annotated[Optional[str], typer.Option("--base-url", help="Custom base URL (overrides --env)")] = None,
) -> None:
    """Save API token, environment, and optional base URL to ~/.reka/config.json."""
    save_config(Config(token=token, env=env, base_url=base_url), DEFAULT_CONFIG_PATH)
    url_note = f", base_url={base_url}" if base_url else ""
    typer.echo(f"Configured: env={env}{url_note}, token saved to {DEFAULT_CONFIG_PATH}", err=True)
