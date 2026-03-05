# ABOUTME: Configuration loading and token/URL resolution for reka CLI
# ABOUTME: Reads ~/.reka/config.json; resolution order: CLI flag > env var > config file

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

BASE_URLS = {
    "prod": "https://prod.vision-agent.api.reka.ai",
    "staging": "https://staging.vision-agent.api.reka.ai",
}

DEFAULT_CONFIG_PATH = Path.home() / ".reka" / "config.json"


@dataclass
class Config:
    token: Optional[str] = None
    env: str = "prod"


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    """Load config from a JSON file, returning an empty Config on any failure."""
    try:
        data = json.loads(path.read_text())
        return Config(
            token=data.get("token"),
            env=data.get("env", "prod"),
        )
    except Exception:
        return Config()


def save_config(config: Config, path: Path = DEFAULT_CONFIG_PATH) -> None:
    """Write config to disk, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"token": config.token, "env": config.env}, indent=2))


def resolve_token(
    cli_flag: Optional[str],
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> Optional[str]:
    """Resolve API token: CLI flag > REKA_API_TOKEN env var > config file."""
    if cli_flag:
        return cli_flag
    env_token = os.environ.get("REKA_API_TOKEN")
    if env_token:
        return env_token
    return load_config(config_path).token


def resolve_base_url(
    cli_flag: Optional[str],
    env: str,
) -> str:
    """Resolve base URL: CLI flag > REKA_BASE_URL env var > derived from env name."""
    if cli_flag:
        return cli_flag
    env_url = os.environ.get("REKA_BASE_URL")
    if env_url:
        return env_url
    return BASE_URLS.get(env, BASE_URLS["prod"])
