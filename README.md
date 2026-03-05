# reka

Command-line interface for the [Reka Vision Agent API](https://docs.reka.ai/vision/api-reference). Upload videos, search content, and ask questions — from a terminal or an AI agent.

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/reka-ai/reka-cli/main/install.sh | bash
```

To install a specific version:

```bash
curl -fsSL https://raw.githubusercontent.com/reka-ai/reka-cli/main/install.sh | bash -s v0.2.0
```

## Quick start

```bash
# Configure with your API token
reka configure --token reka_...

# Upload a video and wait for indexing
VIDEO_ID=$(reka videos upload --url https://example.com/clip.mp4 --name "clip" --wait | jq -r .video_id)

# Search it
reka search --query "person at whiteboard" --video-ids "$VIDEO_ID"

# Ask a question
reka qa --video-id "$VIDEO_ID" --question "What is being discussed?"
```

## Designed for Agents

`reka` is built to be used by AI agents and scripts, not just humans. Every design decision
optimizes for programmatic use.

### JSON output by default

All commands output JSON to stdout. Parse it directly without scraping human-readable text:

```bash
$ reka videos list
[{"video_id": "abc123", "name": "clip.mp4", "status": "indexed"}, ...]

$ reka videos list | jq '.[].video_id'
"abc123"
```

Use `--format text` for human-readable tables when debugging interactively.

### Predictable exit codes

Exit code tells you *what kind* of failure occurred — no need to parse error messages:

```
0   Success
1   Usage error (bad arguments)
2   Authentication failure
3   Permission denied
4   Resource not found
5   Validation error / quota exceeded
6   Rate limit exceeded
7   Server error
8   Timeout
9   Connection error
```

```bash
# Chain commands safely:
VIDEO_ID=$(reka videos upload --url "$URL" --name "test" --wait | jq -r .video_id)
reka search --query "car" --video-ids "$VIDEO_ID"

# Branch on failure type:
reka videos get "$ID" || [ $? -eq 4 ] && echo "video not found"
```

### Structured errors on stderr

Errors always emit JSON to stderr (never mixed with stdout data):

```bash
$ reka videos get nonexistent-id
# stdout: (empty)
# stderr: {"error": {"type": "not_found_error", "message": "Video not found"}}
# exit code: 4
```

### No interactive prompts

Every option is a flag. `reka` never blocks waiting for keyboard input, so it works safely
in non-TTY environments (CI, Docker, agent subprocess calls).

### Environment variable configuration

Inject credentials without touching config files:

```bash
REKA_API_TOKEN=your_token REKA_ENV=staging reka search --query "test"
```

### Async operations with --wait

Some operations (video indexing, generation) complete asynchronously. By default, `reka`
returns immediately with the initial state. Use `--wait` to block until completion:

```bash
# Returns immediately with {"status": "upload_initiated"}
reka videos upload --file clip.mp4 --name "clip" --index

# Blocks until indexed or failed
reka videos upload --file clip.mp4 --name "clip" --index --wait
```

This lets agents implement their own polling strategy, or delegate it to `--wait`.

### Consistent flags everywhere

`--format`, `--verbose`, `--env`, `--timeout`, `--token` work identically on every command.
No surprises.

---

## Command reference

### Global flags

All commands accept these flags:

```
--format json|text     Output format (default: json)
--output-file <path>   Write output to file instead of stdout
--verbose              Show HTTP request/response debug info on stderr
--env staging|prod     API environment (default: prod)
--token <token>        Override token (or set REKA_API_TOKEN)
--timeout <seconds>    Request timeout in seconds (default: 30)
--wait                 Poll until terminal state for async operations
--wait-timeout <secs>  Max wait time when --wait is used (default: 300)
```

### configure

```bash
reka configure --token reka_...          # save token for prod
reka configure --token reka_... --env staging
```

### videos

```bash
reka videos upload --url <url> --name <name> [--index/--no-index] [--group-id <id>] [--wait]
reka videos upload --file <path> --name <name> [--index/--no-index] [--group-id <id>] [--wait]
reka videos list
reka videos get <video-id>
reka videos delete <video-id>
```

### search

```bash
reka search --query <text> [--max-results N] [--video-ids id,id,...] [--threshold F] [--report]
reka search hybrid --query <text> [--max-results N] [--video-ids id,id,...]
```

### qa

```bash
reka qa --video-id <id> --question <text>
```

### groups

```bash
reka groups create --name <name>
reka groups list
reka groups get <group-id>
reka groups delete <group-id>
```

---

## Configuration

**Resolution order** (highest priority first):

| Source | Example |
|--------|---------|
| `--token` flag | `reka videos list --token reka_...` |
| `REKA_API_TOKEN` env var | `export REKA_API_TOKEN=reka_...` |
| `~/.reka/config.json` | Written by `reka configure` |

**Config file** (`~/.reka/config.json`):
```json
{"token": "reka_...", "env": "prod"}
```

**Base URL override**: set `REKA_BASE_URL` or `--base-url` to point at a custom endpoint.

**Environments**:
- `prod` → `https://prod.vision-agent.api.reka.ai`
- `staging` → `https://staging.vision-agent.api.reka.ai`

---

## Binary Distribution

`reka` ships as a self-contained executable with no runtime dependencies — no Python, no pip,
no virtualenv required. The binary includes the Python interpreter and all dependencies
compiled in.

### How the binary is built

Each release triggers a GitHub Actions workflow that builds `reka` using
[PyInstaller](https://pyinstaller.org/) on four platforms:

| Platform       | Binary name           |
|----------------|-----------------------|
| macOS arm64    | `reka-darwin-arm64`   |
| macOS x86_64   | `reka-darwin-x64`     |
| Linux arm64    | `reka-linux-arm64`    |
| Linux x86_64   | `reka-linux-x64`      |

Each binary is accompanied by a SHA256 checksum. The install script verifies the checksum
before installation.

### What PyInstaller does

PyInstaller bundles the Python interpreter, the `reka` package, and all dependencies
(`typer`, `httpx`, `rich`) into a single executable. When you run `reka`, it unpacks
into a temp directory at startup and runs from there. This adds ~100ms to startup time
but means zero installation complexity for users.

### Install script

The install script (`install.sh`) mirrors the approach used by Claude Code:

1. Detects OS and architecture
2. Fetches the latest release version from GitHub
3. Downloads the correct binary
4. Verifies the SHA256 checksum
5. Installs to `~/.reka/bin/reka`
6. Adds `~/.reka/bin` to your PATH via `.bashrc`/`.zshrc`

To install a specific version:

```bash
curl -fsSL https://raw.githubusercontent.com/reka-ai/reka-cli/main/install.sh | bash -s v0.2.0
```

### Building locally

```bash
make build
# produces: dist/reka
```

---

## Development

```bash
# Install in development mode
make install

# Run unit tests
make test

# Run integration tests (requires REKA_API_TOKEN)
REKA_API_TOKEN=reka_... make test-integration
```
