#!/usr/bin/env bash
# Dev Browser Server Launch Script
# Usage: ./server.sh [--headless]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
HEADLESS=""
for arg in "$@"; do
    case $arg in
        --headless)
            HEADLESS="true"
            ;;
    esac
done

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "Error: Node.js 18+ is required. Current version: $(node -v)"
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Check if Playwright browsers are installed
if [ ! -d "$HOME/.cache/ms-playwright" ] || [ -z "$(ls -A $HOME/.cache/ms-playwright 2>/dev/null | grep chromium)" ]; then
    echo "Installing Playwright Chromium browser..."
    npx playwright install chromium
fi

# Start the server
echo "Starting Dev Browser server..."
if [ -n "$HEADLESS" ]; then
    HEADLESS=true npx tsx scripts/start-server.ts
else
    npx tsx scripts/start-server.ts
fi
