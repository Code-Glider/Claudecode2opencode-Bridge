# 🌉 cc2oc-bridge

**Claude Code → OpenCode Universal Bridge**

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/Code-Glider/cc2oc-bridge/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OpenCode Compatible](https://img.shields.io/badge/OpenCode-Compatible-brightgreen)](https://opencode.ai)
[![Status](https://img.shields.io/badge/status-active-success)](https://github.com/Code-Glider/cc2oc-bridge)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Run Claude Code plugins, commands, skills, and agents within OpenCode using a prompt-based runtime.**

> 🚀 **The bridge that brings the entire Claude Code ecosystem to OpenCode** - No code changes required. Install any Claude Code plugin and use it instantly in OpenCode.

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

## 🎯 What It Does

The **cc2oc-bridge** is a universal compatibility layer that unlocks the entire Claude Code plugin ecosystem for OpenCode users. It works by teaching OpenCode's LLM how to interpret and execute Claude Code components through natural language instructions - no native code execution required.

### ✨ Key Features

- 🔌 **Plugin Compatibility** - Install and run any Claude Code plugin without modification
- 🎛️ **Command Execution** - Full support for slash commands with argument substitution (`$1`, `$ARGUMENTS`)
- 📁 **File Injection** - Reference files with `@file` syntax
- 🖥️ **Inline Bash** - Execute commands with `` !`bash` `` syntax
- 🤖 **Agent Spawning** - Run subagents with tool restrictions and lifecycle hooks
- 🧩 **Skill Integration** - Use reusable workflows across projects
- 🔗 **MCP Conversion** - Automatic MCP server configuration conversion
- 🎣 **Hook System** - PreToolUse, PostToolUse, SessionStart, and more
- 🌐 **Browser Automation** - Built-in dev-browser integration for web tasks
- 🔒 **Tool Restrictions** - Enforce security policies with allow/deny lists

### 🎬 Demo

```bash
# Install and use any Claude Code plugin in seconds
./install-plugin.sh /path/to/claude-code-plugin my-plugin
@cc2oc-bridge run my-plugin:command-name
```

> **Note**: While we don't have a live GIF demo yet, the bridge works seamlessly with any Claude Code plugin. Check out our [examples](examples/) directory for sample commands and agents.

## 🚀 Getting Started

### ⚡ Quick Start (30 seconds)

```bash
# 1. Install the bridge to OpenCode
./install.sh

# 2. Install the included test plugin
./install-plugin.sh plugins/test-plugin test-plugin

# 3. Start using Claude Code commands in OpenCode!
@cc2oc-bridge run test-plugin:greet
@cc2oc-bridge run test-plugin:count-files md
@cc2oc-bridge agent test-plugin:helper "List all Python files"
```

### 🎓 How It Works

Unlike traditional runtime bridges that execute code, **cc2oc-bridge** uses a **prompt-based runtime** approach:

```
User Request → Bridge Agent → LLM Interpreter → Component Execution
```

Instead of writing execution code for each feature, the bridge:
1. **Teaches** the LLM how to interpret Claude Code components through detailed instructions
2. **Provides** execution workflows in natural language
3. **Relies** on the model's instruction-following capability

This makes the bridge:
- 🔄 **Easy to extend** - Just modify instructions, not code
- 📝 **Self-documenting** - Instructions are human-readable
- 🌍 **Model-agnostic** - Works with any capable LLM
- 💪 **Flexible** - Adapts to new Claude Code features quickly

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

## 🤝 Contributing

We love contributions! Whether it's bug reports, feature requests, documentation improvements, or code contributions, please get involved.

### 🌟 Ways to Contribute

- **Report Bugs**: [Open an issue](https://github.com/Code-Glider/cc2oc-bridge/issues) with the `bug` label
- **Request Features**: [Open an issue](https://github.com/Code-Glider/cc2oc-bridge/issues) with the `enhancement` label
- **Improve Docs**: Fix typos, clarify instructions, add examples
- **Submit Plugins**: Share your Claude Code plugins that work with the bridge
- **Write Tests**: Increase test coverage
- **Fix Issues**: Grab an issue labeled `good first issue`

### 🛠️ Development Setup

```bash
# Clone repository
git clone https://github.com/Code-Glider/cc2oc-bridge.git
cd cc2oc-bridge

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install pyyaml

# Run tests
python3 hooks.py
python3 loader.py --list
python3 -m pytest tests/  # If you add tests
```

### 📋 Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Commit with clear messages (`git commit -m 'Add: description of feature'`)
7. Push to your fork (`git push origin feature/amazing-feature`)
8. Open a Pull Request with a clear description

### 🎯 Code Style Guidelines

- Follow PEP 8 for Python code
- Use descriptive variable and function names
- Add docstrings for public functions
- Keep functions focused and small
- Add comments for complex logic
- Update documentation for new features
- Test thoroughly before submitting

See our [Contributing Guide](CONTRIBUTING.md) for detailed information.

## 📣 Community & Support

### 💬 Get Help

- 📖 **Documentation**: Check the [AGENTS.md](AGENTS.md) file for detailed architecture docs
- 🐛 **Issues**: [Report bugs or request features](https://github.com/Code-Glider/cc2oc-bridge/issues)
- 💭 **Discussions**: [Ask questions or share ideas](https://github.com/Code-Glider/cc2oc-bridge/discussions)
- 📧 **Email**: For security issues, contact security@cc2oc-bridge.dev

### 🌟 Show Your Support

If this project helped you, please consider:

- ⭐ **Star** this repository to help others find it
- 🐦 **Tweet** about it: `Just discovered cc2oc-bridge - run Claude Code plugins in OpenCode! 🌉`
- 📄 **Write** a blog post about your experience
- 🎤 **Present** it at a meetup or conference

### 📢 Spread the Word

Share cc2oc-bridge with your network:

```markdown
🌉 cc2oc-bridge: Run Claude Code plugins in OpenCode!

Universal compatibility bridge for Claude Code → OpenCode
⭐ https://github.com/Code-Glider/cc2oc-bridge
```

### 🏆 Contributors

Thanks to all contributors who have helped make this project better!

<a href="https://github.com/Code-Glider/cc2oc-bridge/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Code-Glider/cc2oc-bridge" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

## 🔍 Troubleshooting

| Issue | Solution | Related Links |
|-------|----------|---------------|
| Commands not found | Run `@cc2oc-bridge load` to refresh component cache | [Usage Guide](#usage) |
| Model can't execute | Switch to Claude Sonnet 4.5+, GPT-4, or Gemini 2.5+ | [Model Requirements](#model-requirements) |
| Paths broken | Verify `plugins/<name>/core/` directory exists | [Plugin Structure](#plugin-structure) |
| Hooks not firing | Check `hooks/hooks.json` syntax and matcher patterns | [AGENTS.md](AGENTS.md#hook-types) |
| Plugin install fails | Ensure plugin follows Claude Code v2.1.x structure | [Plugin Structure](#plugin-structure) |
| MCP not working | Verify `.mcp.json` format and server availability | [docs/DIRECTIVE.md](docs/DIRECTIVE.md) |

### 🆘 Getting More Help

If you're stuck:

1. Check the [FAQ section](docs/FAQ.md) (coming soon)
2. Search [existing issues](https://github.com/Code-Glider/cc2oc-bridge/issues)
3. Ask in [Discussions](https://github.com/Code-Glider/cc2oc-bridge/discussions)
4. Create a new issue with the `question` label

### 🐛 Reporting Bugs

When reporting bugs, please include:

- Your OpenCode version
- The model you're using
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or error messages

Use the [bug report template](https://github.com/Code-Glider/cc2oc-bridge/issues/new?template=bug_report.md) for faster resolution.

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 cc2oc-bridge contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
...
```

## 🙏 Credits & Acknowledgments

- 🌉 **Bridge Design**: Inspired by Claude Code's innovative plugin architecture
- 🔌 **Compatibility**: Works with the entire Claude Code ecosystem
- 🤖 **Model Testing**: Community-tested across multiple LLM providers
- 📖 **Documentation**: Built with insights from the OpenCode community

### 🔗 Related Projects

- [OpenCode](https://opencode.ai) - The AI-native code editor
- [Claude Code](https://github.com/anthropics/claude-code) - The original plugin system
- [dev-browser](dev-browser/) - Browser automation integration

---

<div align="center">

**🌉 cc2oc-bridge** - Bridging the Claude Code ecosystem to OpenCode

⭐ Star us on GitHub: [https://github.com/Code-Glider/cc2oc-bridge](https://github.com/Code-Glider/cc2oc-bridge)

</div>
