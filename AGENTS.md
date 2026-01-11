# Agents

The **cc2oc-bridge** provides a sophisticated agent system that enables Claude Code plugins, commands, skills, and subagents to run within OpenCode through a prompt-based runtime architecture.

---

## Table of Contents

1. [Core Agent](#core-agent)
2. [Architecture](#architecture)
3. [How It Works](#how-it-works)
4. [Usage Patterns](#usage-patterns)
5. [Plugin Agents](#plugin-agents)
6. [Model Requirements](#model-requirements)
7. [Advanced Features](#advanced-features)
8. [Testing](#testing)
9. [Limitations](#limitations)
10. [Troubleshooting](#troubleshooting)

---

## Core Agent

| Agent | Description | Location | Status |
|:------|:------------|:---------|:-------|
| **cc2oc-bridge** | Main compatibility bridge. Orchestrates plugin execution, handles substitution, manages hooks, and enforces tool restrictions. | `agent/cc2oc-bridge.md` | ✅ Active |

The bridge agent is installed to:
- **Global**: `~/.config/opencode/agent/cc2oc-bridge.md`
- **Local**: `agent/cc2oc-bridge.md` (source)

---

## Architecture

### Design Philosophy

The bridge uses a **prompt-based runtime** approach rather than traditional code execution:

```
User Request → Bridge Agent → LLM Interpreter → Component Execution
```

Instead of writing Python/JavaScript to execute plugins, the bridge:
1. **Teaches** the LLM how to interpret Claude Code components
2. **Provides** detailed execution instructions in the agent definition
3. **Relies** on the model's instruction-following capability

### Why This Approach?

| Traditional Runtime | Prompt-Based Runtime |
|:-------------------|:--------------------|
| Requires code for each feature | Uses natural language instructions |
| Hard to extend | Easy to modify instructions |
| Needs debugging | Self-documenting |
| Language-specific | Model-agnostic |
| **Brittle** | **Flexible** |

### Component Flow

```
┌─────────────────────────────────────────────────────────┐
│                    User Invocation                      │
│         @cc2oc-bridge run <command> [args]              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Bridge Agent (LLM)                         │
│  • Reads agent/cc2oc-bridge.md instructions            │
│  • Understands component locations                      │
│  • Knows execution workflow                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Component Discovery                           │
│  1. Scan plugins/*/.claude/commands/                    │
│  2. Find matching command file                          │
│  3. Read markdown content                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Frontmatter Parsing                          │
│  • Extract allowed-tools                                │
│  • Parse hooks configuration                            │
│  • Read argument hints                                  │
│  • Identify model preferences                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Content Preparation                           │
│  1. Substitute $ARGUMENTS, $1, $2, etc.                 │
│  2. Resolve @file references                            │
│  3. Execute !`bash` inline commands                     │
│  4. Inject core/templates content                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Hook Execution                             │
│  • Run PreToolUse hooks                                 │
│  • Check for blocking conditions                        │
│  • Log hook outputs                                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Command Execution                             │
│  • Follow <process> steps                               │
│  • Respect tool restrictions                            │
│  • Execute bash commands                                │
│  • Read/write files as needed                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Post-Execution Hooks                           │
│  • Run PostToolUse hooks                                │
│  • Handle once:true logic                               │
│  • Report completion                                    │
└─────────────────────────────────────────────────────────┘
```

---

## How It Works

### Step-by-Step Execution

When you invoke:
```
@cc2oc-bridge run greet
```

The bridge agent performs these steps:

#### 1. **Component Discovery**
```bash
# Agent searches:
plugins/*/
  .claude/
    commands/
      greet.md  ← Found!
```

#### 2. **File Reading**
```markdown
---
name: greet
description: A simple greeting
allowed-tools:
  - Bash
---

# Greet Command
...
```

#### 3. **Frontmatter Parsing**
- **Tools**: `Bash` only
- **Hooks**: None
- **Arguments**: None expected

#### 4. **Content Preparation**
If command had:
```markdown
Hello $1!
@core/templates/greeting.md
!`date`
```

Becomes:
```markdown
Hello World!
[content of greeting.md]
Sun Jan 11 20:26:00 IST 2026
```

#### 5. **Hook Execution** (if defined)
```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "command": "echo 'About to run bash...'"
  }]
}
```

#### 6. **Command Execution**
Agent follows the `<process>` steps in the markdown.

#### 7. **Post-Hooks**
Run any `PostToolUse` hooks.

#### 8. **Completion**
Report results to user.

---

## Usage Patterns

### Basic Command Execution

```bash
# Simple command
@cc2oc-bridge run greet

# Command with arguments
@cc2oc-bridge run count-files md

# Namespaced command (from plugin)
@cc2oc-bridge run test-plugin:greet
```

### Subagent Spawning

```bash
# Spawn an agent with a task
@cc2oc-bridge agent helper "What Python files exist?"

# Agent with context
@cc2oc-bridge agent code-reviewer "Review auth.py for security issues"
```

### Skill Invocation

```bash
# Use a skill
@cc2oc-bridge skill summarize README.md

# Skill with multiple arguments
@cc2oc-bridge skill verify-fix auth.py "login bug"
```

### Discovery

```bash
# List all components
@cc2oc-bridge load

# This shows:
# - Commands (22)
# - Agents (1)
# - Skills (1)
# - Plugins (2)
```

---

## Plugin Agents

### Defining an Agent

Create `.claude/agents/my-agent.md`:

```markdown
---
name: my-agent
description: What this agent does
tools:
  - read
  - bash
model: default
permissionMode: default
skills:
  - skill-name
hooks:
  PostToolUse:
    - type: command
      matcher: ".*"
      command: "echo 'Done'"
      once: true
---

# My Agent

You are a specialized agent that...

## Behavior

1. Always do X
2. Never do Y
3. When asked Z, respond with...

## Constraints

- Only read files, never modify
- Keep responses under 100 words
- Ask for clarification if unclear
```

### Invoking Plugin Agents

```bash
@cc2oc-bridge agent my-agent "Task description"
```

The bridge will:
1. Find `plugins/*/. claude/agents/my-agent.md`
2. Load the agent definition
3. Apply tool restrictions
4. Execute hooks
5. Run the task with the agent's persona

---

## Model Requirements

The bridge works as well as the model can follow instructions:

### ✅ Verified Excellent

| Model Family | Versions | Tool Use | Hooks | Substitution | Overall |
|:-------------|:---------|:---------|:------|:-------------|:--------|
| **Claude** | Sonnet/Haiku 4.5+, Haiku 3.5+ | ✅ | ✅ | ✅ | ✅ **Excellent** |
| **GPT** | 4.1/4.1 mini, 4.5+, 5.1 mini, o1+ | ✅ | ✅ | ✅ | ✅ **Excellent** |
| **Gemini** | 2.5 Flash/Pro, 3 Flash/Pro | ✅ | ✅ | ✅ | ✅ **Excellent** |
| **DeepSeek** | 3.1+ | ✅ | ✅ | ✅ | ✅ **Excellent** |
| **GLM** | 4.5+ | ✅ | ✅ | ✅ | ✅ **Excellent** |
| **Kimi** | K2+ | ✅ | ✅ | ✅ | ✅ **Excellent** |
| **Qwen** | 3 Max, Coder | ✅ | ✅ | ✅ | ✅ **Excellent** |
| **Minimax** | All | ✅ | ✅ | ✅ | ✅ **Excellent** |
| **Grok** | Latest | ✅ | ✅ | ✅ | ✅ **Excellent** |

### ⚠️ Limited/Untested

Models not listed above may work but haven't been tested. Generally:
- **10B+ parameters** - Better chance of working
- **Tool use training** - Required for execution
- **32K+ context** - Needed for complex workflows

### ❌ Known Issues

- **Small models (<10B)** - Skip steps, poor instruction following
- **No tool support** - Cannot execute bash/read/write operations
- **Low context (<8K)** - Fail on long command definitions

### Recommended Models

For production use:
1. **Claude Sonnet 4.5** - Best instruction following
2. **GPT-4 Turbo** - Excellent tool use
3. **Gemini 2.5 Pro** - Good balance

For testing:
1. **glm-4.7** - Free, tested working
2. **Gemini 2.5 Flash** - Fast, mostly works

### Why Model Quality Matters

The bridge is **entirely prompt-based**. A weak model:
- ❌ Skips substitution steps
- ❌ Ignores hooks
- ❌ Doesn't enforce tool restrictions
- ❌ Fails to parse frontmatter

A strong model:
- ✅ Follows all 8 execution steps
- ✅ Respects tool restrictions
- ✅ Executes hooks correctly
- ✅ Handles edge cases

---

## Advanced Features

### Argument Substitution

Commands can use:

| Pattern | Meaning | Example |
|:--------|:--------|:--------|
| `$ARGUMENTS` | All arguments as string | `"file.txt 100"` |
| `$1`, `$2`, ... | Positional arguments | `"file.txt"`, `"100"` |
| `${1:-default}` | With default value | `"file.txt"` or `"default"` |

### File Injection

```markdown
# In command:
@core/templates/project.md
@plugins/test-plugin/core/references/guidelines.md

# Bridge reads and injects content
```

### Inline Bash

```markdown
Current time: !`date`
Files: !`ls -1 | wc -l`
```

Executed before command runs.

### Tool Restrictions

```yaml
allowed-tools:
  - Bash(git:*)  # Only git commands
  - Read
  - Write(*.md)  # Only markdown files

disallowedTools:
  - Edit  # Never allow editing
```

### Hook Types

#### Command Hooks
```json
{
  "type": "command",
  "matcher": "Write",
  "command": "npm run lint",
  "timeout": 600
}
```

#### Prompt Hooks
```json
{
  "type": "prompt",
  "prompt": "Is this action safe?",
  "matcher": ".*"
}
```

#### Agent Hooks
```json
{
  "type": "agent",
  "agent": "security-checker",
  "matcher": "Bash"
}
```

### Hook Lifecycle

```
SessionStart
    ↓
PreToolUse (before each tool)
    ↓
[Tool Execution]
    ↓
PostToolUse (after success)
    ↓
PostToolUseFailure (after error)
    ↓
Stop (when agent stops)
    ↓
SessionEnd
```

---

## Testing

### Test Plugin

The repository includes `plugins/test-plugin/` with:

#### Commands
- `greet` - Simple bash execution
- `count-files` - Argument handling
- `test-command` - Basic test

#### Agents
- `helper` - Read-only assistant

#### Skills
- `summarize` - File summarization

#### Hooks
- PreToolUse for Write/Edit
- PostToolUse for Bash (once)
- SessionStart notification

### Running Tests

```bash
# Test command execution
@cc2oc-bridge run greet
# Expected: Greeting with timestamp

# Test arguments
@cc2oc-bridge run count-files md
# Expected: Count of .md files

# Test agent
@cc2oc-bridge agent helper "List files"
# Expected: File listing with explanation

# Test hooks (manual)
python3 hooks.py
# Expected: Hook execution log

# Test loader
python3 loader.py --list
# Expected: Component inventory
```

### Validation Checklist

- [ ] Commands discovered correctly
- [ ] Arguments substituted
- [ ] Files injected
- [ ] Hooks executed
- [ ] Tool restrictions enforced
- [ ] Agents spawnable
- [ ] Skills invokable

---

## Limitations

### What Works

✅ **Command execution** with full substitution  
✅ **Agent spawning** with tool restrictions  
✅ **Skill loading** and invocation  
✅ **Hook execution** at lifecycle points  
✅ **Tool restrictions** enforcement  
✅ **MCP configuration** conversion  
✅ **File injection** (`@file`)  
✅ **Inline bash** (`!`command``)  

### What Doesn't Work

❌ **Native autocomplete** - Commands don't appear in `/` menu  
❌ **Direct invocation** - Must use `@cc2oc-bridge` prefix  
❌ **Agent shortcuts** - Can't use `@agent` directly  
❌ **Automatic registration** - No native OpenCode integration  
❌ **Code execution** - Everything runs through LLM interpretation  
❌ **Guaranteed consistency** - Quality depends on model capability  

### Trade-offs

| Feature | Benefit | Cost |
|:--------|:--------|:-----|
| Prompt-based | Easy to modify | Model-dependent |
| No code execution | Secure, sandboxed | Slower than native |
| LLM interpretation | Flexible | Inconsistent |
| Plugin compatibility | Works with Claude Code ecosystem | Requires bridge prefix |

---

## Troubleshooting

### Commands Not Found

**Symptom**: `@cc2oc-bridge run X` says "command not found"

**Solutions**:
1. Run `@cc2oc-bridge load` to refresh
2. Check `python3 loader.py --list` shows the command
3. Verify file exists in `plugins/*/.claude/commands/`
4. Restart OpenCode to reload agent

### Model Can't Execute

**Symptom**: Agent says "I don't have the capability"

**Solutions**:
1. Switch to a more capable model (Claude Sonnet 4.5+)
2. Check model has tool use enabled
3. Verify agent definition is loaded (`~/.config/opencode/agent/cc2oc-bridge.md`)

### Paths Broken

**Symptom**: `@file` references fail

**Solutions**:
1. Check `plugins/*/core/` directory exists
2. Verify paths are relative (`@core/...` not `@/absolute/...`)
3. Run `./install-plugin.sh` again to fix paths

### Hooks Not Firing

**Symptom**: No hook output

**Solutions**:
1. Check `hooks/hooks.json` syntax
2. Verify matcher regex is correct
3. Test manually: `python3 hooks.py`
4. Ensure model is following hook instructions

### Substitution Fails

**Symptom**: `$1` appears literally in output

**Solutions**:
1. Use a better model
2. Check command has `argument-hint` in frontmatter
3. Verify arguments were passed correctly

---

## Best Practices

### For Plugin Authors

1. **Keep commands focused** - One task per command
2. **Document arguments** - Use `argument-hint`
3. **Use relative paths** - `@core/...` not absolute
4. **Test with multiple models** - Don't assume capability
5. **Provide examples** - Show expected usage
6. **Handle errors gracefully** - Check for missing files

### For Users

1. **Use capable models** - Claude Sonnet 4.5+ recommended
2. **Reload after changes** - `@cc2oc-bridge load`
3. **Check loader output** - `python3 loader.py --list`
4. **Test incrementally** - Start with simple commands
5. **Read error messages** - They're usually accurate
6. **Report issues** - Help improve the bridge

---

## Future Enhancements

Potential improvements:

- [ ] Native OpenCode plugin API integration
- [ ] Automatic command registration
- [ ] Better error handling and reporting
- [ ] Performance optimization
- [ ] More comprehensive test suite
- [ ] Plugin marketplace integration
- [ ] Visual plugin manager
- [ ] Hook debugging tools

---

## Contributing

The bridge is open source. Contributions welcome:

1. Test with different models
2. Report compatibility issues
3. Improve documentation
4. Add example plugins
5. Enhance error messages
6. Optimize performance

---

## License

MIT - See LICENSE file

---

## Credits

- **Design**: Inspired by Claude Code's plugin architecture
- **Compatibility**: Works with Claude Code ecosystem plugins
- **Testing**: Community-tested with multiple models
