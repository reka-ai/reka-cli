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

echo ""
echo "reka ${VERSION} installed successfully."
echo "Run 'reka --help' to get started (you may need to restart your shell or run: export PATH=\"\$HOME/.reka/bin:\$PATH\")"
