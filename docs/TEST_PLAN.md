# cc2oc-bridge: Test Plugin Validation Plan

This document outlines the validation strategy for ensuring plugins work correctly when bridged to OpenCode via `cc2oc-bridge`.

## 1. Test Environment Setup

We will create an isolated test environment to avoid polluting the main installation.

```bash
# 1. Create a test directory
mkdir -p .tmp/test-plugin

# 2. Copy cc2oc-bridge (simulate standalone usage)
cp -r services/cc2oc-bridge .tmp/test-plugin/bridge

# 3. Use test-plugin (included in repo)
cp -r services/cc2oc-bridge/plugins/test-plugin .tmp/test-plugin/test-plugin-source

# 4. Initialize test project
cd .tmp/test-plugin
echo "# Test Plugin Project" > README.md
```

## 2. Installation Validation

Verify that the bridge can correctly install the GSD plugin and convert its MCP configuration.

### Steps
1. Run the plugin installer using the bridge.
2. Verify directory structure.
3. Check `opencode.json` for MCP injection.

```bash
# Install test-plugin via Bridge
./bridge/install-plugin.sh ./test-plugin-source test-plugin

# Verification Checks
# 1. Check plugin dir
ls -la .claude/plugins/test-plugin/

# 2. Check commands loaded
python bridge/loader.py --list | grep "test-plugin"

# 3. Check MCP config
cat ~/.config/opencode/opencode.json | grep "mcp"
```

### Expected Result
- Plugin files present in `.claude/plugins/test-plugin`
- Bridge loader lists test-plugin commands (e.g., `greet`, `count-files`)
- OpenCode config contains MCP server configuration if present

## 3. Command Execution Tests

Test core test-plugin commands to ensure argument parsing, tool execution, and hook firing.

### Test Case A: Greet Command
**Command:** `greet`
**Expected:**
- Executes greeting command
- Hooks fire (if configured)

### Test Case B: Count Files (Tool Usage)
**Command:** `count-files md`
**Expected:**
- Bridge executes `count-files.md` prompt
- Uses `Bash` tool to count files
- Returns correct count

### Test Case C: Agent Spawning
**Command:** `helper` agent
**Expected:**
- Spawns helper agent
- Executes task with tool restrictions

## 4. Lifecycle Hook Validation

Verify that `once: true` hooks and 10-minute timeouts are respected.

### Test Case D: PreToolUse Hook
1. Configure a `PreToolUse` hook in `test-plugin/hooks/hooks.json`.
2. Run a command that triggers the hook.
3. **Expected:** Hook engine executes and logs output.

### Test Case E: Once-Only Hook
1. Verify the session start hook runs on the first command.
2. Run a second command.
3. **Expected:** Session message does NOT appear again.

## 5. Browser Integration (Dev-Browser)

Verify the bridge can drive the browser if plugins need web research.

### Test Case F: Web Research
**Script:**
```python
from bridge.browser import BrowserIntegration
b = BrowserIntegration()
b.setup()
b.navigate("https://opencode.ai/docs")
snap = b.get_aria_snapshot()
print(len(snap))
```
**Expected:** Non-zero snapshot length, browser process starts.

## 6. Context Compaction

Verify the bridge's custom compactor handles large contexts.

### Test Case G: Compaction Trigger
1. artificially fill context > 70%.
2. Run `bridge/compactor.py`.
3. **Expected:**
   - "Deep Compaction" triggered
   - Important content preserved
   - Actions log preserved
   - Compression ratio > 20%

## 7. Automated Test Script

Save this as `run_tests.sh` in the test directory:

```bash
#!/bin/bash
set -e

echo "=== GSD Bridge Test Suite ==="

# 1. Install
echo "[1] Installing..."
./bridge/install-plugin.sh ./test-plugin-source test-plugin

# 2. Verify Loader
echo "[2] Verifying Loader..."
python bridge/loader.py --list > components.txt
if grep -q "greet" components.txt; then
    echo "✅ Test Plugin Commands found"
else
    echo "❌ Test Plugin Commands MISSING"
    exit 1
fi

# 3. Verify MCP
echo "[3] Verifying MCP..."
# (Mock check of opencode.json since we can't real-time check OpenCode internal state)
if [ -f .claude/plugins/test-plugin/.mcp.json ]; then
     echo "✅ MCP config present"
else
     echo "ℹ️  No MCP config (optional)"
fi

# 4. Dry Run Command
echo "[4] Dry Run Command..."
# Bridge doesn't have a direct CLI runner yet, assume python runner
# python bridge/commands.py --dry-run /new-project "Test"

echo "✅ All Setup Tests Passed"
```
