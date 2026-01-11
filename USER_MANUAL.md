---
name: cc2oc-bridge
description: |
  Claude Code Compatibility Bridge. Loads and executes Claude Code plugins, 
  commands, skills, and subagents within OpenCode. Full v2.1.x compatibility
  including browser automation.
---

# 🌉 cc2oc-bridge: User Manual

## Table of Contents
1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Commands](#commands)
4. [Subagents](#subagents)
5. [Skills](#skills)
6. [Hooks](#hooks)
7. [Browser Automation](#browser-automation)
8. [MCP Integration](#mcp-integration)
9. [Plugin Management](#plugin-management)
10. [Publishing to GitHub](#publishing-to-github)

---

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/cc2oc-bridge.git
cd cc2oc-bridge

# Install dependencies
pip install pyyaml

# Setup browser (optional)
cd dev-browser && npm install && npx playwright install chromium && cd ..

# Install bridge
./install.sh

# List components
python loader.py --list
```

---

## Installation

### From Source (Development)
```bash
git clone https://github.com/YOUR_USERNAME/cc2oc-bridge.git
cd cc2oc-bridge
pip install pyyaml
./install.sh
```

### As a Service in Your Project
```bash
# Copy into your project
cp -r cc2oc-bridge services/cc2oc-bridge
./services/cc2oc-bridge/install.sh
```

---

## Commands

Commands are markdown files with optional YAML frontmatter.

### Location
- User: `~/.claude/commands/`
- Project: `.claude/commands/`
- Plugin: `plugins/<name>/commands/`

### Frontmatter Options
```yaml
---
description: What this command does
argument-hint: [filename]
allowed-tools: Bash, Read, Write
disallowedTools: Edit
model: opus-4.5
context: fork  # v2.1.x: run in isolated subagent
agent: reviewer  # v2.1.x: use specific agent
hooks:
  PreToolUse:
    - type: command
      matcher: "Write"
      command: "npm run lint"
---
```

### Substitution
- `$ARGUMENTS` → All arguments
- `$1`, `$2` → Positional arguments
- `@path/file` → File content injection
- `!command` → Inline bash output

---

## Subagents

Subagents are persona-driven experts with restricted toolsets.

### Location
- User: `~/.claude/agents/`
- Project: `.claude/agents/`

### Frontmatter (v2.1.x)
```yaml
---
name: code-reviewer
description: Reviews code for issues
tools: [read, bash]
model: sonnet
permissionMode: default
skills: [linting, testing]
hooks:  # v2.1.x: hooks in agent frontmatter
  PostToolUse:
    - type: command
      matcher: ".*"
      command: "echo 'Tool completed'"
      once: true
---
```

---

## Skills

Skills are complex workflows in subdirectories.

### Location
- User: `~/.claude/skills/<name>/SKILL.md`
- Project: `.claude/skills/<name>/SKILL.md`

### Frontmatter (v2.1.x)
```yaml
---
name: my-skill
description: What this skill does
allowed-tools:
  - Bash
  - Read
  - Write
context: fork  # Run in isolated context
user-invocable: true
agent: specialist  # v2.1.x: use specific agent
hooks:
  PreToolUse:
    - type: prompt
      prompt: "Verify this action is safe"
---
```

---

## Hooks

Lifecycle hooks run before/after tools.

### Hook Types
| Type | Trigger |
|------|---------|
| `PreToolUse` | Before any tool |
| `PostToolUse` | After successful tool |
| `PostToolUseFailure` | After failed tool |
| `Stop` | When agent stops |
| `SessionStart` | Session begins |
| `SessionEnd` | Session ends |

### Configuration (v2.1.x)
```json
{
  "hooks": {
    "PreToolUse": [{
      "type": "command",
      "matcher": "Write|Edit",
      "command": "npm run lint",
      "timeout": 600,
      "once": true
    }]
  }
}
```

### Hook Types
- `command` - Execute shell command
- `prompt` - Evaluate with LLM
- `agent` - Run agent verifier

### once: true (v2.1.x)
Hooks with `once: true` run only once per session.

### Timeout (v2.1.x)
Default timeout is 10 minutes (600 seconds).

---

## Browser Automation

The bridge includes dev-browser for browser control.

### Setup (First Time)
```bash
cd dev-browser
npm install
npx playwright install chromium
cd ..
```

### Usage
```python
from browser import BrowserIntegration

browser = BrowserIntegration()

# Navigate
browser.navigate("https://example.com")

# Interact
browser.click("button#submit")
browser.type_text("input#email", "test@example.com")

# Get LLM-friendly snapshot
snapshot = browser.get_aria_snapshot()

# Screenshot
browser.screenshot("screenshot.png")
```

---

## MCP Integration

Claude Code MCP configs are converted to OpenCode format.

### Automatic Conversion
When installing a plugin with `.mcp.json`, it's converted:

**Claude Code** (`.mcp.json`):
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

**OpenCode** (`opencode.json`):
```json
{
  "mcp": {
    "github": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
      "enabled": true
    }
  }
}
```

---

## Plugin Management

### Install a Plugin
```bash
./install-plugin.sh /path/to/plugin plugin-name
```

### List Installed
```bash
python loader.py --list
```

### Plugin Structure
```
my-plugin/
├── .claude/
│   ├── commands/
│   ├── agents/
│   └── skills/
├── hooks/
│   └── hooks.json
├── .mcp.json
└── plugin.json
```

---

## Publishing to GitHub

### Extract to Standalone Repo

```bash
# Copy to new location
cp -r services/cc2oc-bridge /path/to/new-repo
cd /path/to/new-repo

# Initialize git
git init
git add .
git commit -m "Initial commit: cc2oc-bridge v1.0.0"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/cc2oc-bridge.git
git push -u origin main
```

### Create Release
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `./install.sh` | Install bridge to OpenCode |
| `./install-plugin.sh <path> <name>` | Install a plugin |
| `python loader.py --list` | List all components |
| `python loader.py --json` | Export as JSON |
| `python browser.py` | Test browser integration |
| `python hooks.py` | Test hooks engine |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin not found | Check `plugins/` directory |
| Command not loading | Verify YAML frontmatter |
| Browser not working | Run `cd dev-browser && npm install` |
| MCP not merging | Check `~/.config/opencode/opencode.json` |
| Hooks not firing | Check matcher regex syntax |

---

## Context Compaction

The bridge includes an advanced context compaction system that outperforms Claude Code's basic summarization.

### Why It's Better

| Feature | Claude Code | cc2oc-bridge |
|---------|-------------|--------------|
| Memory Type | Flat summary | **Layered memory model** |
| Action Tracking | Lost on compact | **Never loses actions** |
| Decision Rationale | Often lost | **Preserved with IDs** |
| Dependencies | Not tracked | **Dependency graph** |
| Recency | Uniform | **Gradient detail** |
| Errors | Summarized | **Preserved for learning** |

### The Layered Memory Model

```
🔒 IDENTITY    - Agent role, constraints (never compacted)
🎯 TASK        - Current objective (high priority)
🧠 DECISIONS   - Choices + rationale (preserved)
✅ ACTIONS     - What was done (structured log)
⚠️ ERRORS      - Mistakes + fixes (learn from)
📁 WORKSPACE   - Git status, files (refreshable)
💭 CONTEXT     - Background info (summarizable)
```

### Usage

```python
from compactor import ContextCompactor, MemoryLayer

compactor = ContextCompactor()

# Add important memory
compactor.add_memory(
    MemoryLayer.TASK,
    "Build feature X",
    importance=1.0
)

# Log actions (never lost)
compactor.log_action(
    "Created file.py",
    files=["file.py"],
    outcome="success"
)

# Check if compaction needed
if compactor.should_compact(conversation):
    result = compactor.compact(conversation, llm_fn=my_llm)
    print(f"Compressed to {result.compression_ratio:.0%}")
```

### Auto-Compaction Rules

1. **PRESERVE EXACT QUOTES** for:
   - User's task description
   - Error messages
   - Critical code snippets
   - Decision rationale

2. **SUMMARIZE AGGRESSIVELY** for:
   - Exploratory discussion
   - Failed attempts (keep lesson only)
   - Verbose tool outputs

3. **RECENCY GRADIENT**:
   - Last 3 exchanges: Full detail
   - Last 10 exchanges: Key points
   - Older: Summary only

4. **NEVER LOSE**:
   - Current active task
   - Uncommitted code changes
   - Unresolved errors
   - User's explicit requests

---

## Testing

For comprehensive testing strategies, including a full validation plan for the GSD plugin, see:
[docs/TEST_PLAN.md](docs/TEST_PLAN.md)

### Quick Test Script
You can use the bridge's self-test capabilities:

```bash
# Test component loading
python loader.py --list

# Test hook engine
python hooks.py

# Test browser integration
python browser.py
```

---

## System Prompts (CLAUDE.md)

The bridge automatically loads and merges system prompts, similar to OpenCode's native handling of `AGENTS.md`.

### Loading Order (Merged)
1. `~/.claude/CLAUDE.md` (Global user instructions)
2. `./CLAUDE.md` (Project specific instructions)
3. `.claude/project-context.md` (Project context/status)

This ensures that any rules, style guides, or context defined for Claude Code are automatically applied when running via the bridge.
