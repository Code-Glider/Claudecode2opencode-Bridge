# cc2oc-bridge

**Claude Code Compatibility Bridge for OpenCode**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

Run Claude Code plugins, commands, skills, and agents within OpenCode using a prompt-based runtime.

## Table of Contents

- [What It Does](#what-it-does)
- [Getting Started](#getting-started)
  - [Quick Start](#quick-start)
  - [How It Works](#how-it-works)
  - [Installation](#installation)
- [Usage](#usage)
- [Plugin Structure](#plugin-structure)
- [Model Requirements](#model-requirements)
- [Testing](#testing)
- [Limitations](#limitations)
- [Files](#files)
- [Advanced](#advanced)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## What It Does

The bridge enables you to:
- ✅ Install Claude Code plugins into OpenCode
- ✅ Execute slash commands with argument substitution and file injection
- ✅ Run subagents with tool restrictions
- ✅ Use skills as reusable workflows
- ✅ Execute lifecycle hooks (PreToolUse, PostToolUse, etc.)
- ✅ Convert MCP configurations automatically

## Getting Started

### Quick Start

```bash
# 1. Install the bridge
./install.sh

# 2. Install a plugin (e.g., test-plugin)
./install-plugin.sh plugins/test-plugin test-plugin

# 3. Use in OpenCode
@cc2oc-bridge run test-plugin:greet
```

### How It Works

The bridge is a **prompt-based runtime**. Instead of executing code, it teaches an LLM how to:
1. Discover components (commands, agents, skills)
2. Parse Claude Code frontmatter
3. Substitute arguments (`$1`, `$ARGUMENTS`)
4. Inject file content (`@file`)
5. Execute inline bash (`!`command``)
6. Run hooks at lifecycle points
7. Enforce tool restrictions

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User                                    │
│                    @cc2oc-bridge run ...                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Bridge Agent (LLM)                           │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ • Component Discovery (commands/agents/skills)            │ │
│  │ • Frontmatter Parsing (YAML metadata)                     │ │
│  │ • Substitution ($1, @file, !cmd)                          │ │
│  │ • Hook Execution (Pre/Post ToolUse)                        │ │
│  │ • Tool Restrictions Enforcement                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Plugin Files System                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  commands/       │  │  agents/         │  │  skills/     │ │
│  │  └── *.md        │  │  └── *.md        │  │  └── SKILL.md│ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│  ┌──────────────────┐  ┌──────────────────┐                  │ │
│  │  core/           │  │  hooks/          │                  │ │
│  │  └── templates/  │  │  └── hooks.json  │                  │ │
│  └──────────────────┘  └──────────────────┘                  │ └─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Execution                                 │
│  • Follow <process> steps from command markdown                │
│  • Execute with allowed tools only                            │
│  • Apply constraints and restrictions                         │
└─────────────────────────────────────────────────────────────────┘
```

The agent definition (`agent/cc2oc-bridge.md`) contains detailed instructions that capable models follow.

## Installation

### Prerequisites
- Python 3.8+
- `pyyaml` (`pip install pyyaml`)
- OpenCode installed

### Install Bridge
```bash
./install.sh
```

This creates:
- `~/.config/opencode/agent/cc2oc-bridge.md` - The bridge agent
- `~/.config/opencode/skill/cc2oc-bridge/SKILL.md` - The bridge skill

### Install a Plugin
```bash
./install-plugin.sh <plugin-source-path> [plugin-name]
```

Example:
```bash
./install-plugin.sh plugins/test-plugin test-plugin
```

This:
1. Creates `plugins/<name>/.claude/` structure
2. Copies commands, agents, skills
3. Copies `core/` (references, templates)
4. Rewrites absolute paths to relative
5. Generates `plugin.json` manifest

**Current Version**: 1.0.0
**Changelog**: See [CHANGELOG.md](CHANGELOG.md) for version history

## Usage

### List Components
```
@cc2oc-bridge load
```

### Run a Command
```
@cc2oc-bridge run <command-name> [arguments]
```

Example:
```
@cc2oc-bridge run test-plugin:greet
@cc2oc-bridge run count-files md
```

### Use an Agent
```
@cc2oc-bridge agent <agent-name> <task>
```

Example:
```
@cc2oc-bridge agent helper "What Python files are in this project?"
```

### Invoke a Skill
```
@cc2oc-bridge skill <skill-name>
```

## Plugin Structure

After installation, plugins have this structure:

```
plugins/my-plugin/
├── .claude/
│   ├── commands/       # Slash commands
│   ├── agents/         # Subagents
│   └── skills/         # Reusable workflows
├── core/
│   ├── references/     # Documentation
│   └── templates/      # File templates
├── hooks/
│   └── hooks.json      # Lifecycle hooks
└── plugin.json         # Manifest
```

## Model Requirements

The bridge works best with capable models. Based on testing:

### ✅ Verified Working

| Provider | Models | Notes |
|:---------|:-------|:------|
| **GLM** | 4.5+ (all variants) | ✅ Tested, excellent |
| **DeepSeek** | 3.1+ (all variants) | ✅ Tested, excellent |
| **Minimax** | All models | ✅ Tested, works well |
| **Kimi** | K2 (all variants) | ✅ Tested, works well |
| **Qwen** | 3 Max, Coder | ✅ Tested, excellent |
| **Claude** | Sonnet/Haiku 4.5+, Haiku 3.5+ | ✅ Excellent (premium) |
| **Gemini** | 2.5 Flash/Pro, 3 Flash/Pro | ✅ Excellent (premium) |
| **GPT** | 4.1/4.1 mini, 4.5+, 5.1 mini, o1+ | ✅ Excellent (premium) |
| **Grok** | Latest | ✅ Works well (premium) |

### ⚠️ Limited Support

- Small models (<10B parameters) - May skip complex steps
- Models without tool use training - Cannot execute commands properly
- Models with small context (<8K) - Struggle with long prompts

### Recommended for Production

1. **Claude Sonnet 4.5+** - Best instruction following
2. **DeepSeek 3.1+** - Excellent open source option
3. **GLM 4.5+** - Great free tier option
4. **Qwen 3 Max / Coder** - Excellent for code tasks
5. **Gemini 2.5+** - Strong all-around performance

## Testing

A test plugin is included at `plugins/test-plugin/`:

```bash
# Test command
@cc2oc-bridge run greet

# Test agent
@cc2oc-bridge agent helper "List files"

# Test hooks
python3 hooks.py
```

## Limitations

### What Works
- ✅ Command execution with substitution
- ✅ Agent spawning
- ✅ Skill loading
- ✅ Hook execution
- ✅ Tool restrictions
- ✅ MCP conversion

### What Doesn't
- ❌ Native `/command` autocomplete (requires `@cc2oc-bridge run`)
- ❌ Native `@agent` invocation (requires `@cc2oc-bridge agent`)
- ❌ Automatic hook registration in OpenCode
- ❌ Works only as well as the model can follow instructions

## Files

| File | Purpose |
|------|---------|
| `install.sh` | Install bridge to OpenCode |
| `install-plugin.sh` | Install a plugin |
| `loader.py` | Component discovery |
| `commands.py` | Command execution logic |
| `hooks.py` | Hook engine |
| `browser.py` | Browser automation |
| `compactor.py` | Context compaction |
| `agent/cc2oc-bridge.md` | Bridge agent definition |

## Advanced

### Manual Testing
```bash
# List all components
python3 loader.py --list

# Export as JSON
python3 loader.py --json

# Test hooks
python3 hooks.py

# Test browser
python3 browser.py
```

### Custom Plugins

Create your own plugin:
```
my-plugin/
├── commands/
│   └── my-command.md
├── core/
│   └── templates/
└── plugin.json
```

Then install:
```bash
./install-plugin.sh ./my-plugin
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/Code-Glider/Claudecode2opencode-Bridge.git
cd cc2oc-bridge

# Install dependencies
pip install pyyaml

# Run tests
python3 hooks.py
python3 loader.py --list
```

### Code Style

- Follow existing code conventions
- Add comments for complex logic
- Update documentation for new features
- Test thoroughly before submitting

### Support

- 📝 [Documentation](AGENTS.md)
- 🐛 [Report Issues](https://github.com/YOUR_USERNAME/cc2oc-bridge/issues)
- 💬 [Discussions](https://github.com/YOUR_USERNAME/cc2oc-bridge/discussions)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Commands not found | Run `@cc2oc-bridge load` |
| Model can't execute | Switch to a more capable model |
| Paths broken | Check `plugins/<name>/core/` exists |
| Hooks not firing | Verify `hooks/hooks.json` syntax |

## License

MIT

## Credits

- Bridge design inspired by Claude Code's plugin system
- Compatible with plugins from the Claude Code ecosystem
