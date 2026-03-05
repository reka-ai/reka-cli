#!/usr/bin/env bash
# ABOUTME: Installer script for the reka CLI binary
# ABOUTME: Downloads the correct binary for the current platform, verifies SHA256, and installs to ~/.reka/bin

set -euo pipefail

REPO="reka-ai/reka-cli"
BINARY="reka"
INSTALL_DIR="$HOME/.reka/bin"
VERSION="${1:-latest}"

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Darwin) OS_NAME="darwin" ;;
    Linux)  OS_NAME="linux" ;;
    *)
        echo "Unsupported OS: $OS" >&2
        exit 1
        ;;
esac

# Detect architecture
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64 | amd64) ARCH_NAME="x64" ;;
    arm64 | aarch64) ARCH_NAME="arm64" ;;
    *)
        echo "Unsupported architecture: $ARCH" >&2
        exit 1
        ;;
esac

PLATFORM="${OS_NAME}-${ARCH_NAME}"

# Resolve version
if [ "$VERSION" = "latest" ]; then
    echo "Fetching latest release version..."
    VERSION="$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" \
        | grep '"tag_name"' | sed 's/.*"tag_name": *"\([^"]*\)".*/\1/')"
fi

echo "Installing reka ${VERSION} (${PLATFORM})..."

BINARY_NAME="${BINARY}-${PLATFORM}"
BASE_URL="https://github.com/${REPO}/releases/download/${VERSION}"
BINARY_URL="${BASE_URL}/${BINARY_NAME}"
CHECKSUM_URL="${BASE_URL}/${BINARY_NAME}.sha256"

# Create install directory
mkdir -p "$INSTALL_DIR"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# Download binary and checksum
echo "Downloading ${BINARY_URL}..."
curl -fsSL -o "${TMP_DIR}/${BINARY_NAME}" "$BINARY_URL"
curl -fsSL -o "${TMP_DIR}/${BINARY_NAME}.sha256" "$CHECKSUM_URL"

# Verify SHA256
echo "Verifying checksum..."
cd "$TMP_DIR"
if command -v sha256sum >/dev/null 2>&1; then
    sha256sum --check "${BINARY_NAME}.sha256"
elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 --check "${BINARY_NAME}.sha256"
else
    echo "Warning: no sha256 tool found, skipping checksum verification" >&2
fi
cd - >/dev/null

# Install
install -m 755 "${TMP_DIR}/${BINARY_NAME}" "${INSTALL_DIR}/${BINARY}"
echo "Installed to ${INSTALL_DIR}/${BINARY}"

# Add to PATH if needed
add_to_path() {
    local shell_rc="$1"
    local path_line='export PATH="$HOME/.reka/bin:$PATH"'
    if [ -f "$shell_rc" ] && ! grep -qF '.reka/bin' "$shell_rc"; then
        echo "" >> "$shell_rc"
        echo "# Added by reka installer" >> "$shell_rc"
        echo "$path_line" >> "$shell_rc"
        echo "Added ~/.reka/bin to PATH in ${shell_rc}"
    fi
}

add_to_path "$HOME/.bashrc"
add_to_path "$HOME/.zshrc"

# Install agent skill
for skill_target in "$HOME/.claude/skills/reka-cli" "$HOME/.codex/skills/reka-cli" "$HOME/.agents/skills/reka-cli"; do
    mkdir -p "$skill_target"
    cat > "${skill_target}/SKILL.md" << 'EOF'
---
name: reka-cli
description: Use the reka CLI to work with the Reka Vision Agent API — upload videos, search content, ask questions, and manage groups.
---

## What is the Reka Vision Agent API?

The Reka Vision Agent API is a managed service for uploading, processing, and analyzing videos with AI.
It handles preprocessing, storage, and embeddings automatically. Key capabilities:

- **Video management** — upload (by URL or file), retrieve, list, delete
- **Semantic search** — search video content by natural language query
- **Q&A** — ask questions about a video and get AI-generated answers
- **Tagging** — automatic metadata tag generation
- **Clip generation** — extract shorter clips from longer source videos, and check on the status of the generation

## Agent bootstrap

Use the `reka` CLI directly. Always run with non-interactive flags only.

1. Ensure auth is present:
   - `REKA_API_TOKEN` env var, or
   - `reka configure --token <token>`
2. Load machine-readable contract first:
   - `reka meta --format json`
3. Use `reka --help` / `reka <command> --help` only for human-readable inspection.

## Canonical workflow

```bash
VIDEO_ID=$(reka videos upload --url "https://example.com/clip.mp4" --name "clip" --wait | jq -r .video_id)
reka search --query "person at whiteboard" --video-ids "$VIDEO_ID"
reka qa --video-id "$VIDEO_ID" --question "What is being discussed?"
```

## Contract for automation

- Success payloads: JSON on stdout
- Error payloads: JSON on stderr as `{"error": {...}}`
- Do not parse human text; branch by exit code
- Prefer `reka meta --format json` over help-text parsing for command discovery

Exit codes:
- `0` success
- `1` usage error
- `2` authentication error
- `3` permission error
- `4` not found
- `5` validation/quota error
- `6` rate limit
- `7` server error
- `8` timeout
- `9` connection error

## Reliability rules

- Use `--wait` when a downstream step needs a terminal async result.
- Prefer `--format json` (default) for all machine parsing.
- Use `--timeout` and retry on exit `8`/`9`/`6` with backoff.
- Auth resolution order: `--token` > `REKA_API_TOKEN` > `~/.reka/config.json`.
- Base URL resolution: `--base-url` > `REKA_BASE_URL` > config `base_url` > `--env`.
EOF
    echo "Installed agent skill to ${skill_target}"
done

echo ""
echo "reka ${VERSION} installed successfully."
echo "Run 'reka --help' to get started (you may need to restart your shell or run: export PATH=\"\$HOME/.reka/bin:\$PATH\")"
