---
name: cc2oc-bridge
description: |
  Claude Code → OpenCode Universal Bridge. Enables execution of any Claude Code 
  plugin, command, skill, or subagent within OpenCode using OpenCode's native 
  model connection. Full v2.1.x compatibility.
triggers:
  - "run claude code plugin"
  - "execute test-plugin"
  - "install plugin"
  - "load plugin"
  - "claude command"
  - "cc2oc"
  - "browser automation"
capabilities:
  - Load Claude Code commands from .claude/commands/
  - Load Claude Code subagents from .claude/agents/
  - Load Claude Code skills from .claude/skills/
  - Install and manage Claude Code plugins
  - Execute commands with $ARGUMENTS, @file, and !bash substitution
  - Run lifecycle hooks (PreToolUse, PostToolUse, etc.)
  - Emulate AskFollowupQuestion, Skill, NotebookEdit tools
  - Browser automation via dev-browser integration
  - MCP server passthrough to OpenCode
chains_with:
  - "directives/meta/create_directive.md": "Create new directives after bridging"
  - "directives/tools/browser/dev-browser.md": "Browser automation"
tags:
  - bridge
  - compatibility
  - claude-code
  - opencode
  - migration
  - test-plugin
  - browser
---

# cc2oc-bridge: Claude Code → OpenCode Bridge

## Overview

The **cc2oc-bridge** is a complete compatibility layer that enables **any** Claude Code plugin, command, skill, or subagent to run within OpenCode. It uses OpenCode's native model connection (no separate Claude API calls).

**Version Compatibility: Claude Code v2.1.x**

## Quick Start

```bash
# Install the bridge
./services/cc2oc-bridge/install.sh

# Install a plugin (e.g., test-plugin)
./services/cc2oc-bridge/install-plugin.sh plugins/test-plugin test-plugin

# Verify installation
python services/cc2oc-bridge/loader.py --list
```

## Architecture

```
┌────────────────────┐      ┌──────────────────────────────┐
│    OpenCode        │      │       cc2oc-bridge           │
│                    │ ──>  │  services/cc2oc-bridge/      │
│  - Native LSP      │      │  ├── loader.py (discover)    │
│  - Native Plan     │      │  ├── commands.py (execute)   │
│  - Native Tools    │      │  ├── hooks.py (lifecycle)    │
│                    │      │  ├── browser.py (dev-browser)│
│                    │      │  ├── mcp.py (MCP conversion) │
│                    │      │  └── plugins/ (installed)    │
└────────────────────┘      └──────────────────────────────┘
```

## Claude Code v2.1.x Features

### Commands & Skills (Merged)
Commands and skills now share a unified structure:
- **context: fork** - Run in isolated sub-agent
- **agent: name** - Use specific agent for execution
- **hooks** - Lifecycle hooks in frontmatter

### Hooks in Frontmatter
Agents and skills can define hooks directly:
```yaml
---
name: my-agent
hooks:
  PreToolUse:
    - type: command
      matcher: "Write|Edit"
      command: "npm run lint"
      once: true  # Run only once per session
---
```

### once: true Hook Config
Hooks can be configured to run only once per session:
```json
{
  "PreToolUse": [{
    "matcher": ".*",
    "hooks": [{"type": "command", "command": "...", "once": true}]
  }]
}
```

### YAML-style Lists in allowed-tools
Both formats are supported:
```yaml
# String format
allowed-tools: Bash, Read, Write

# YAML list format
allowed-tools:
  - Bash
  - Read
  - Write
```

## Browser Integration

The bridge integrates with `services/dev-browser` to provide browser automation
similar to Claude's "Claude in Chrome" feature.

```python
from cc2oc_bridge.browser import BrowserIntegration

browser = BrowserIntegration()
browser.navigate("https://example.com")
browser.click("button#submit")
snapshot = browser.get_aria_snapshot()
```

## MCP Integration

Claude Code MCP configs (`.mcp.json`) are automatically converted to OpenCode format:

**Claude Code** → **OpenCode**
```json
{"mcpServers": {...}} → {"mcp": {...}}
```

## Feature Compatibility Matrix

### ✅ Fully Supported
| Feature | Notes |
|---------|-------|
| Slash Commands | Full substitution support |
| Skills (SKILL.md) | context: fork, agent field |
| Subagents | Hooks in frontmatter |
| Plugins | Full manifest support |
| Hooks | once:true, 10min timeout |
| MCP Servers | Auto-conversion |
| Browser (via dev-browser) | ARIA snapshots |

### ⚠️ OpenCode Native (Passthrough)
| Feature | Notes |
|---------|-------|
| LSP | Use OpenCode's LSP config |
| Plan Mode | Use OpenCode's /plan |
| Background Agents | Use OpenCode's async |

### ❌ Not Applicable
| Feature | Reason |
|---------|--------|
| Claude in Chrome | Use dev-browser instead |
| Teleport/Remote | Infrastructure feature |
| VSCode Extension | OpenCode has its own |

## Files

| File | Purpose |
|------|---------|
| `loader.py` | Discover and parse components |
| `commands.py` | Execute commands with substitution |
| `hooks.py` | Lifecycle hook engine |
| `browser.py` | dev-browser integration |
| `mcp.py` | MCP format conversion |
| `install.sh` | Bridge installer |
| `install-plugin.sh` | Plugin installer |

## Reference

- [Claude Code v2.1.x Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
- [OpenCode Docs](https://opencode.ai/docs)
- [dev-browser Directive](../../../directives/tools/browser/dev-browser.md)
