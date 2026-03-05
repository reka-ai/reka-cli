# ABOUTME: Implements the `reka configure` command for saving API credentials
# ABOUTME: Writes token and environment to ~/.reka/config.json

from typing import Annotated, Optional

import typer

from reka.config import Config, DEFAULT_CONFIG_PATH, save_config

app = typer.Typer(help="Save API credentials to the config file.", invoke_without_command=True)


@app.callback(invoke_without_command=True)
def configure(
    token: Annotated[str, typer.Option("--token", help="API token to save")],
    env: Annotated[str, typer.Option("--env", help="Environment: prod or staging")] = "prod",
) -> None:
    """Save API token and environment to ~/.reka/config.json."""
    save_config(Config(token=token, env=env), DEFAULT_CONFIG_PATH)
    typer.echo(f"Configured: env={env}, token saved to {DEFAULT_CONFIG_PATH}", err=True)
