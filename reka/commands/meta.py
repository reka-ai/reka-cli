# ABOUTME: Implements the `reka meta` command for machine-readable CLI introspection
# ABOUTME: Exposes command/flag contracts, auth resolution, and exit-code mappings as JSON

from importlib.metadata import PackageNotFoundError, version
from typing import Annotated, Any

import click
import typer
from typer.main import get_command

from reka.config import BASE_URLS
from reka.output import EXIT_CODES, emit


_WAIT_CAPABILITIES = {
    "videos upload": {
        "status_field": "status",
        "terminal_states": ["indexed", "index_failed", "upload_failed", "download_failed"],
    },
    "clip create": {
        "status_field": "status",
        "terminal_states": ["completed", "failed"],
    },
    "generations create": {
        "status_field": "status",
        "terminal_states": ["completed", "ready", "failed", "skipped"],
    },
}


def _package_version() -> str:
    try:
        return version("reka-cli")
    except PackageNotFoundError:
        return "unknown"


def _param_type_name(param: click.Parameter) -> str:
    param_type = getattr(param, "type", None)
    if param_type is None:
        return "string"
    name = getattr(param_type, "name", None)
    if name:
        return str(name)
    return param_type.__class__.__name__.lower()


def _serialize_param(param: click.Parameter) -> dict[str, Any]:
    item: dict[str, Any] = {
        "name": str(param.name),
        "required": bool(param.required),
        "type": _param_type_name(param),
    }
    default = getattr(param, "default", None)
    if default is not None:
        item["default"] = default

    if isinstance(param, click.Option):
        item["kind"] = "option"
        item["flags"] = list(param.opts)
        if param.secondary_opts:
            item["secondary_flags"] = list(param.secondary_opts)
        if param.help:
            item["description"] = param.help
        if param.envvar:
            item["env_var"] = param.envvar
    else:
        item["kind"] = "argument"
    if isinstance(getattr(param, "type", None), click.types.Choice):
        item["choices"] = list(param.type.choices)

    return item


def _serialize_command(path: str, command: click.Command) -> dict[str, Any]:
    params = []
    for param in command.params:
        if isinstance(param, click.Option) and "--help" in param.opts:
            continue
        params.append(_serialize_param(param))

    item: dict[str, Any] = {
        "path": path,
        "kind": "group" if isinstance(command, click.Group) and bool(command.commands) else "command",
        "description": command.help or command.short_help or "",
        "params": params,
    }

    if path in _WAIT_CAPABILITIES:
        item["supports_wait"] = True
        item["wait_contract"] = _WAIT_CAPABILITIES[path]
    else:
        item["supports_wait"] = False

    if isinstance(command, click.Group) and command.commands:
        item["subcommands"] = [
            _serialize_command(f"{path} {name}".strip(), sub)
            for name, sub in command.commands.items()
        ]
    return item


def _contract() -> dict[str, Any]:
    from reka.main import app

    root = get_command(app)
    commands = [
        _serialize_command(name, command)
        for name, command in root.commands.items()
    ]
    return {
        "name": "reka",
        "version": _package_version(),
        "summary": "Reka Vision Agent CLI machine-readable contract.",
        "default_output_format": "json",
        "error_output_stream": "stderr",
        "error_shape": {"error": {"type": "string", "message": "string"}},
        "auth": {
            "token_resolution_order": ["--token", "REKA_API_TOKEN", "~/.reka/config.json"],
            "base_url_resolution_order": ["--base-url", "REKA_BASE_URL", "~/.reka/config.json:base_url", "--env"],
            "environments": BASE_URLS,
        },
        "exit_codes": {"0": "success", "1": "usage_error", **{str(code): name for name, code in EXIT_CODES.items()}},
        "global_flags": [
            {
                "name": str(param.name),
                "flags": list(param.opts),
                "secondary_flags": list(param.secondary_opts),
                "required": bool(param.required),
                "type": _param_type_name(param),
                "default": param.default,
                "env_var": param.envvar,
                "description": param.help,
            }
            for param in root.params
            if isinstance(param, click.Option) and "--help" not in param.opts
        ],
        "commands": commands,
    }


def meta(
    format: Annotated[str, typer.Option("--format", help="Output format: json or text")] = "json",
) -> None:
    """Print machine-readable command/flag contracts for agent tooling."""
    out_format = format.lower()
    if out_format not in {"json", "text"}:
        typer.echo("Error: --format must be json or text", err=True)
        raise typer.Exit(1)
    from reka.main import state

    emit(_contract(), format=out_format, output_file=state.output_file)


def register(root: typer.Typer) -> None:
    root.command("meta", help="Print machine-readable command contract for agents.")(meta)
