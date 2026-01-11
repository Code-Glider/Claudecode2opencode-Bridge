# Example: Hello World Command

This example shows how to create a simple Claude Code command for cc2oc-bridge.

## File: `.claude/commands/hello.md`

```markdown
---
description: Greets the user with a personalized message
argument-hint: [name]
allowed-tools: Bash
---

# Hello World Command

Greet the user named $ARGUMENTS with enthusiasm!

Current time: !`date`
```

## Usage

After installing this command, run:

```bash
python loader.py --list
```

You'll see:
```
Commands (1):
  /hello [project] - Greets the user with a personalized message
```

## How It Works

1. `$ARGUMENTS` is replaced with whatever the user provides
2. `!`date`` is executed and replaced with the current date/time
3. The resulting prompt is sent to the model
