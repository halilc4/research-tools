#!/bin/bash
# Research Tools MCP - macOS Installer
# Run: chmod +x install-macos.sh && ./install-macos.sh

set -e

echo ""
echo "=== Research Tools MCP Installer ==="

# =============================================================================
# PREREQUISITES
# =============================================================================

echo ""
echo "[1/5] Checking prerequisites..."

# --- Python ---
echo ""
echo "Checking Python..."

PYTHON_PATH=""
PYTHON_PATHS=(
    "python3"
    "python"
    "/opt/homebrew/bin/python3"
    "/usr/local/bin/python3"
    "/usr/bin/python3"
    "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
)

for p in "${PYTHON_PATHS[@]}"; do
    if command -v "$p" &> /dev/null; then
        PYTHON_PATH=$(command -v "$p")
        break
    elif [[ -x "$p" ]]; then
        PYTHON_PATH="$p"
        break
    fi
done

if [[ -n "$PYTHON_PATH" ]]; then
    PYTHON_VERSION=$("$PYTHON_PATH" --version 2>&1)
    echo "  Found Python: $PYTHON_PATH ($PYTHON_VERSION)"
else
    echo "  Python not found. Installing..."

    INSTALLED=false

    # Try Homebrew
    if [[ "$INSTALLED" == "false" ]] && command -v brew &> /dev/null; then
        echo "  Installing via Homebrew..."
        brew install python@3.12
        PYTHON_PATH="$(brew --prefix python@3.12)/bin/python3"
        INSTALLED=true
    fi

    # Try installing Homebrew first, then Python
    if [[ "$INSTALLED" == "false" ]]; then
        echo "  Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -f "/usr/local/bin/brew" ]]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi

        echo "  Installing Python via Homebrew..."
        brew install python@3.12
        PYTHON_PATH="$(brew --prefix python@3.12)/bin/python3"
        INSTALLED=true
    fi

    if [[ "$INSTALLED" == "true" ]]; then
        echo "  Python installed: $PYTHON_PATH"
    else
        echo "  Failed to install Python."
        exit 1
    fi
fi

# --- uv ---
echo ""
echo "Checking uv..."

UV_PATH=""
UV_PATHS=(
    "uv"
    "$HOME/.local/bin/uv"
    "$HOME/.cargo/bin/uv"
    "/opt/homebrew/bin/uv"
    "/usr/local/bin/uv"
)

for u in "${UV_PATHS[@]}"; do
    if command -v "$u" &> /dev/null; then
        UV_PATH=$(command -v "$u")
        break
    elif [[ -x "$u" ]]; then
        UV_PATH="$u"
        break
    fi
done

if [[ -n "$UV_PATH" ]]; then
    UV_VERSION=$("$UV_PATH" --version 2>&1)
    echo "  Found uv: $UV_PATH ($UV_VERSION)"
else
    echo "  uv not found. Installing..."

    # Use official installer
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Source env if exists
    # shellcheck source=/dev/null
    [[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env"

    # Find installed uv
    if [[ -x "$HOME/.local/bin/uv" ]]; then
        UV_PATH="$HOME/.local/bin/uv"
        export PATH="$HOME/.local/bin:$PATH"
    elif [[ -x "$HOME/.cargo/bin/uv" ]]; then
        UV_PATH="$HOME/.cargo/bin/uv"
        export PATH="$HOME/.cargo/bin:$PATH"
    fi

    if [[ -n "$UV_PATH" ]]; then
        echo "  uv installed: $UV_PATH"
    else
        echo "  Failed to install uv."
        exit 1
    fi
fi

# Derive uvx path
UVX_PATH="${UV_PATH/\/uv/\/uvx}"
if [[ ! -x "$UVX_PATH" ]]; then
    UVX_PATH="uvx"
fi
echo "  uvx path: $UVX_PATH"

# =============================================================================
# API KEYS
# =============================================================================

echo ""
echo "[2/5] API Keys Configuration"
echo "Press Enter to skip any key."
echo ""

read -rp "DEVTO_API_KEY (https://dev.to/settings/extensions): " DEVTO_KEY
read -rp "SERPER_API_KEY (https://serper.dev/api-key): " SERPER_KEY

# =============================================================================
# CONFIGURE CLAUDE DESKTOP
# =============================================================================

echo ""
echo "[3/5] Configuring Claude Desktop..."

CONFIG_DIR="$HOME/Library/Application Support/Claude"
CONFIG_PATH="$CONFIG_DIR/claude_desktop_config.json"

mkdir -p "$CONFIG_DIR"

"$PYTHON_PATH" << EOF
import json
import os

config_path = "$CONFIG_PATH"
uvx_path = "$UVX_PATH"
devto_key = "$DEVTO_KEY"
serper_key = "$SERPER_KEY"

if os.path.exists(config_path) and os.path.getsize(config_path) > 0:
    with open(config_path, 'r') as f:
        config = json.load(f)
    print("  Found existing config, merging...")
else:
    config = {}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

server_config = {
    "command": uvx_path,
    "args": ["--from", "mcp-cli-research-tools[mcp]", "rt-mcp"]
}

env = {}
if devto_key:
    env["DEVTO_API_KEY"] = devto_key
if serper_key:
    env["SERPER_API_KEY"] = serper_key
if env:
    server_config["env"] = env

config['mcpServers']['research-tools'] = server_config

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"  Config saved to: {config_path}")
EOF

# =============================================================================
# TEST MCP SERVER
# =============================================================================

echo ""
echo "[4/5] Testing MCP server..."
if "$UVX_PATH" --from mcp-cli-research-tools[mcp] rt-mcp --help &> /dev/null; then
    echo "  MCP server OK"
else
    echo "  Warning: Could not verify MCP server. It may still work."
fi

# =============================================================================
# RESTART CLAUDE DESKTOP
# =============================================================================

echo ""
echo "[5/5] Restarting Claude Desktop..."

if pgrep -x "Claude" > /dev/null; then
    pkill -x "Claude"
    sleep 2
fi

if [[ -d "/Applications/Claude.app" ]]; then
    open -a "Claude"
    echo "  Claude Desktop restarted."
else
    echo "  Claude Desktop not found. Please start manually."
fi

# =============================================================================
# DONE
# =============================================================================

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Summary:"
echo "  Python: $PYTHON_PATH"
echo "  uv:     $UV_PATH"
echo "  Config: $CONFIG_PATH"
echo ""
echo "Research Tools MCP is now available in Claude Desktop."
echo ""
