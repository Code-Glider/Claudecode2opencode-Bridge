#!/bin/bash
# =================================================================================
# cc2oc-bridge Plugin Installer
# =================================================================================
# Installs a Claude Code plugin into the bridge registry.
# Creates a self-contained copy with proper .claude structure.
#
# Usage: ./install-plugin.sh <plugin-path> [plugin-name]
# Example: ./install-plugin.sh ../get-shit-done gsd
# =================================================================================

set -e

BRIDGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="$BRIDGE_DIR/plugins"
LOG_FILE="$BRIDGE_DIR/plugin-install.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }

# =================================================================================
# Argument Parsing
# =================================================================================
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <plugin-path> [plugin-name]"
    echo ""
    echo "Examples:"
    echo "  $0 ../get-shit-done gsd"
    echo "  $0 ~/.claude/plugins/my-plugin"
    exit 1
fi

PLUGIN_SOURCE="$1"
PLUGIN_NAME="${2:-$(basename "$PLUGIN_SOURCE")}"

echo "=========================================="
echo "  cc2oc-bridge Plugin Installer"
echo "=========================================="
log_info "Plugin Source: $PLUGIN_SOURCE"
log_info "Plugin Name: $PLUGIN_NAME"

# =================================================================================
# Validation
# =================================================================================
if [[ ! -d "$PLUGIN_SOURCE" ]]; then
    log_error "Plugin source not found: $PLUGIN_SOURCE"
    exit 1
fi

# Resolve to absolute path
PLUGIN_SOURCE="$(cd "$PLUGIN_SOURCE" && pwd)"

# =================================================================================
# Create Installation Directory
# =================================================================================
mkdir -p "$PLUGINS_DIR"

PLUGIN_INSTALL_DIR="$PLUGINS_DIR/$PLUGIN_NAME"
log_info "Installing to: $PLUGIN_INSTALL_DIR"

# Remove old installation if exists
if [[ -d "$PLUGIN_INSTALL_DIR" ]]; then
    log_warn "Removing existing installation..."
    rm -rf "$PLUGIN_INSTALL_DIR"
fi

# Create structure
mkdir -p "$PLUGIN_INSTALL_DIR/.claude/commands"
mkdir -p "$PLUGIN_INSTALL_DIR/.claude/agents"
mkdir -p "$PLUGIN_INSTALL_DIR/.claude/skills"
mkdir -p "$PLUGIN_INSTALL_DIR/hooks"
mkdir -p "$PLUGIN_INSTALL_DIR/core"

# =================================================================================
# Detect and Copy Plugin Components
# =================================================================================
log_info "Detecting plugin structure..."

# Helper function to copy directory contents
copy_if_exists() {
    local src="$1"
    local dest="$2"
    local label="$3"
    
    if [[ -d "$src" ]]; then
        log_info "Copying $label from $src"
        cp -r "$src"/* "$dest/" 2>/dev/null || true
        local count=$(find "$dest" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        log_success "Copied $count $label files"
        return 0
    fi
    return 1
}

# Copy commands (check multiple possible locations)
COMMANDS_COPIED=false
if copy_if_exists "$PLUGIN_SOURCE/.claude/commands" "$PLUGIN_INSTALL_DIR/.claude/commands" "commands"; then
    COMMANDS_COPIED=true
elif copy_if_exists "$PLUGIN_SOURCE/commands/gsd" "$PLUGIN_INSTALL_DIR/.claude/commands" "commands"; then
    COMMANDS_COPIED=true
elif copy_if_exists "$PLUGIN_SOURCE/commands/$PLUGIN_NAME" "$PLUGIN_INSTALL_DIR/.claude/commands" "commands"; then
    COMMANDS_COPIED=true
elif copy_if_exists "$PLUGIN_SOURCE/commands" "$PLUGIN_INSTALL_DIR/.claude/commands" "commands"; then
    COMMANDS_COPIED=true
fi

if [[ "$COMMANDS_COPIED" == "false" ]]; then
    log_warn "No commands directory found"
fi

# Copy agents
if ! copy_if_exists "$PLUGIN_SOURCE/.claude/agents" "$PLUGIN_INSTALL_DIR/.claude/agents" "agents"; then
    if ! copy_if_exists "$PLUGIN_SOURCE/agents" "$PLUGIN_INSTALL_DIR/.claude/agents" "agents"; then
        log_warn "No agents directory found"
    fi
fi

# Copy skills
if ! copy_if_exists "$PLUGIN_SOURCE/.claude/skills" "$PLUGIN_INSTALL_DIR/.claude/skills" "skills"; then
    if ! copy_if_exists "$PLUGIN_SOURCE/skills" "$PLUGIN_INSTALL_DIR/.claude/skills" "skills"; then
        log_warn "No skills directory found"
    fi
fi

# Copy hooks
if [[ -f "$PLUGIN_SOURCE/hooks/hooks.json" ]]; then
    cp "$PLUGIN_SOURCE/hooks/hooks.json" "$PLUGIN_INSTALL_DIR/hooks/"
    log_success "Copied hooks configuration"
fi

# Copy core (references, templates, workflows)
for core_dir in "core" "get-shit-done" "$PLUGIN_NAME"; do
    if [[ -d "$PLUGIN_SOURCE/$core_dir/references" ]]; then
        mkdir -p "$PLUGIN_INSTALL_DIR/core/references"
        cp -r "$PLUGIN_SOURCE/$core_dir/references"/* "$PLUGIN_INSTALL_DIR/core/references/" 2>/dev/null || true
        log_success "Copied core/references"
    fi
    if [[ -d "$PLUGIN_SOURCE/$core_dir/templates" ]]; then
        mkdir -p "$PLUGIN_INSTALL_DIR/core/templates"
        cp -r "$PLUGIN_SOURCE/$core_dir/templates"/* "$PLUGIN_INSTALL_DIR/core/templates/" 2>/dev/null || true
        log_success "Copied core/templates"
    fi
    if [[ -d "$PLUGIN_SOURCE/$core_dir/workflows" ]]; then
        mkdir -p "$PLUGIN_INSTALL_DIR/core/workflows"
        cp -r "$PLUGIN_SOURCE/$core_dir/workflows"/* "$PLUGIN_INSTALL_DIR/core/workflows/" 2>/dev/null || true
        log_success "Copied core/workflows"
    fi
done

# =================================================================================
# Rewrite Absolute Paths in Command Files
# =================================================================================
log_info "Rewriting absolute paths to relative..."

# Common patterns to replace
PATTERNS=(
    "@/Users/.*/get-shit-done/core/"
    "@~/.claude/get-shit-done/"
    "@../../core/"
    "~/.claude/get-shit-done/"
)

REPLACEMENT="@core/"

for pattern in "${PATTERNS[@]}"; do
    find "$PLUGIN_INSTALL_DIR/.claude/commands" -name "*.md" -exec sed -i '' "s|$pattern|$REPLACEMENT|g" {} \; 2>/dev/null || true
done

# Also fix template references without @
find "$PLUGIN_INSTALL_DIR/.claude/commands" -name "*.md" -exec sed -i '' "s|templates/|core/templates/|g" {} \; 2>/dev/null || true

log_success "Paths rewritten to use relative core/ references"

# =================================================================================
# Create Plugin Manifest
# =================================================================================
cat > "$PLUGIN_INSTALL_DIR/plugin.json" << EOF
{
    "name": "$PLUGIN_NAME",
    "version": "1.0.0",
    "source": "$PLUGIN_SOURCE",
    "installed": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "structure": {
        "commands": ".claude/commands",
        "agents": ".claude/agents",
        "skills": ".claude/skills",
        "hooks": "hooks",
        "core": "core"
    }
}
EOF

log_success "Created plugin manifest"

# =================================================================================
# Handle MCP Configuration
# =================================================================================
MCP_FILE="$PLUGIN_SOURCE/.mcp.json"
if [[ -f "$MCP_FILE" ]]; then
    log_info "Found MCP configuration..."
    
    cp "$MCP_FILE" "$PLUGIN_INSTALL_DIR/.mcp.json"
    log_success "Copied MCP configuration"
    
    # Convert and export to OpenCode's config
    OPENCODE_CONFIG="$HOME/.config/opencode/opencode.json"
    log_info "Converting Claude MCP format to OpenCode format..."
    
    python3 -c "
import json
from pathlib import Path

# Load Claude Code MCP config
claude_config = json.loads(Path('$MCP_FILE').read_text())

# Convert to OpenCode format
opencode_mcp = {}
for name, cfg in claude_config.get('mcpServers', {}).items():
    cmd = cfg.get('command', '')
    args = cfg.get('args', [])
    command_array = [cmd] + args if isinstance(cmd, str) else cmd
    
    opencode_mcp[name] = {
        'type': 'local',
        'command': command_array,
        'enabled': True,
        'environment': cfg.get('env', {})
    }

# Load existing OpenCode config or create new
opencode_config_path = Path('$OPENCODE_CONFIG')
existing = {}
if opencode_config_path.exists():
    existing = json.loads(opencode_config_path.read_text())

# Merge MCP servers
existing.setdefault('\$schema', 'https://opencode.ai/config.json')
existing.setdefault('mcp', {}).update(opencode_mcp)

# Write back
opencode_config_path.parent.mkdir(parents=True, exist_ok=True)
opencode_config_path.write_text(json.dumps(existing, indent=2))
print(f'Added {len(opencode_mcp)} MCP server(s) to OpenCode config')
" && log_success "MCP servers merged into OpenCode config ($OPENCODE_CONFIG)"
else
    log_warn "No MCP configuration found in plugin"
fi

# =================================================================================
# Summary
# =================================================================================
echo ""
echo "=========================================="
log_success "Plugin '$PLUGIN_NAME' installed successfully!"
echo "=========================================="
echo ""
echo "Installed to: $PLUGIN_INSTALL_DIR"
echo ""
echo "Structure:"
ls -la "$PLUGIN_INSTALL_DIR"
echo ""
echo "Commands:"
ls "$PLUGIN_INSTALL_DIR/.claude/commands" 2>/dev/null | head -10 || echo "  (none)"
echo ""
echo "To use: @cc2oc-bridge run $PLUGIN_NAME:<command>"
