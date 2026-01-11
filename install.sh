#!/bin/bash
# =================================================================================
# cc2oc-bridge Installer
# =================================================================================
# This script sets up the cc2oc-bridge service for OpenCode.
# Links @cc2oc-bridge agent and skill.
#
# Usage: ./services/cc2oc-bridge/install.sh
# =================================================================================

set -e

# Configuration
OPENCODE_CONFIG_DIR="$HOME/.config/opencode"
# Robustly find the script's directory even if call from elsewhere
BRIDGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${BRIDGE_DIR}/install.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "Starting cc2oc-bridge Installation..."
log_info "Bridge Directory: $BRIDGE_DIR"

# 1. Clean up old links if they exist
log_info "Cleaning up old links..."
rm -f "$OPENCODE_CONFIG_DIR/agent/bridge.md"
rm -rf "$OPENCODE_CONFIG_DIR/skill/bridge"
rm -f "$OPENCODE_CONFIG_DIR/agent/cc2oc-bridge.md"
rm -rf "$OPENCODE_CONFIG_DIR/skill/cc2oc-bridge"

# 2. Setup Directories
AGENT_DIR="$OPENCODE_CONFIG_DIR/agent"
SKILL_DIR="$OPENCODE_CONFIG_DIR/skill/cc2oc-bridge"
mkdir -p "$AGENT_DIR"
mkdir -p "$SKILL_DIR"

# 3. Install Agent
log_info "Installing Agent..."
if [[ -f "$BRIDGE_DIR/agent/cc2oc-bridge.md" ]]; then
    ln -sf "$BRIDGE_DIR/agent/cc2oc-bridge.md" "$AGENT_DIR/cc2oc-bridge.md"
    log_success "Linked agent to $AGENT_DIR/cc2oc-bridge.md"
else
    log_error "Agent file not found at $BRIDGE_DIR/agent/cc2oc-bridge.md"
    exit 1
fi

# 4. Install Skill
log_info "Installing Skill..."
if [[ -f "$BRIDGE_DIR/USER_MANUAL.md" ]]; then
    ln -sf "$BRIDGE_DIR/USER_MANUAL.md" "$SKILL_DIR/SKILL.md"
    log_success "Linked skill to $SKILL_DIR/SKILL.md"
else
    log_error "Skill manual not found"
    exit 1
fi

# 5. Final Check
if command -v python3 &> /dev/null; then
    python3 "$BRIDGE_DIR/loader.py" --list > /dev/null 2>&1 && log_success "Loader validated" || log_error "Loader check failed"
fi

echo ""
echo -e "${GREEN}Installation Complete!${NC}"
echo "Restart OpenCode and use: @cc2oc-bridge load"
