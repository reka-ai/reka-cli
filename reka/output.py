# ABOUTME: Output formatting and exit code mapping for reka CLI
# ABOUTME: JSON goes to stdout; errors always go to stderr as JSON

import json
import sys
from typing import Any, Optional

from rich.console import Console
from rich.table import Table

EXIT_CODES = {
    "authentication_error": 2,
    "permission_error": 3,
    "not_found_error": 4,
    "validation_error": 5,
    "rate_limit_error": 6,
    "server_error": 7,
    "timeout": 8,
    "connection_error": 9,
}

_stderr_console = Console(stderr=True)


class ApiError(Exception):
    """Raised when the API returns a non-2xx response or a timeout/connection error occurs."""

    def __init__(self, exit_code: int, error: dict):
        self.exit_code = exit_code
        self.error = error
        super().__init__(error.get("message", "API error"))

    @classmethod
    def from_response(cls, body: dict) -> "ApiError":
        """Construct from a parsed API error response body."""
        error = body.get("error", body)
        error_type = error.get("type", "server_error")
        exit_code = EXIT_CODES.get(error_type, EXIT_CODES["server_error"])
        return cls(exit_code=exit_code, error=error)

    @classmethod
    def timeout(cls) -> "ApiError":
        return cls(exit_code=8, error={"type": "timeout", "message": "Request timed out"})

    @classmethod
    def connection(cls, message: str) -> "ApiError":
        return cls(exit_code=9, error={"type": "connection_error", "message": message})


def emit(data: Any, format: str, output_file: Optional[str]) -> None:
    """Write data to stdout (or a file). JSON is default; text renders a human-readable table."""
    if format == "text":
        _emit_text(data)
        return

    output = json.dumps(data, indent=2, default=str)
    if output_file:
        with open(output_file, "w") as f:
            f.write(output + "\n")
    else:
        print(output)


def emit_error(error: dict) -> None:
    """Write an error to stderr as JSON. Never touches stdout."""
    print(json.dumps({"error": error}, default=str), file=sys.stderr)


def _emit_text(data: Any) -> None:
    """Render data as a rich table for human consumption."""
    console = Console()

    if isinstance(data, list):
        if not data:
            console.print("(no results)")
            return
        first = data[0] if isinstance(data[0], dict) else {}
        table = Table()
        for key in first.keys():
            table.add_column(key)
        for item in data:
            if isinstance(item, dict):
                table.add_row(*[str(v) for v in item.values()])
        console.print(table)
    elif isinstance(data, dict):
        table = Table("key", "value", show_header=True)
        for k, v in data.items():
            table.add_row(str(k), str(v))
        console.print(table)
    else:
        console.print(str(data))
