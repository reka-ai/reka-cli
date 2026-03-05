# ABOUTME: Shared helpers for command modules
# ABOUTME: Builds a RekaClient from the global state and resolves auth/URL

from functools import wraps

from reka.client import RekaClient
from reka.config import DEFAULT_CONFIG_PATH, resolve_base_url, resolve_token
from reka.output import ApiError, emit_error


def make_client() -> RekaClient:
    """Build a RekaClient from the global CLI state, raising ApiError if no token is set."""
    from reka.main import state

    token = resolve_token(state.token, DEFAULT_CONFIG_PATH)
    if not token:
        raise ApiError(
            exit_code=2,
            error={"type": "authentication_error", "message": "No API token. Set REKA_API_TOKEN or run: reka configure --token <token>"},
        )
    base_url = resolve_base_url(state.base_url, state.env)
    return RekaClient(
        base_url=base_url,
        token=token,
        timeout=state.timeout,
        verbose=state.verbose,
    )


def api_command(fn):
    """Decorator: converts ApiError to SystemExit so the CLI runner sees the correct exit code."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ApiError as e:
            emit_error(e.error)
            raise SystemExit(e.exit_code)
    return wrapper


def emit_result(data) -> None:
    """Emit data using the format and output_file from global state."""
    from reka.main import state
    from reka.output import emit

    emit(data, format=state.format, output_file=state.output_file)
