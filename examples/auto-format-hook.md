# Example: Auto-Format Hook

This example shows how to create a lifecycle hook that auto-formats code.

## File: `hooks/hooks.json`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write ${TOOL_INPUT}"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/validate-command.sh"
          }
        ]
      }
    ]
  }
}
```

## Hook Types

| Type | Description |
|------|-------------|
| `command` | Execute a shell command |
| `prompt` | Evaluate a prompt with the LLM |
| `agent` | Run an agentic verifier |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success - continue execution |
| `1` | Error - log and continue |
| `2` | Block - prevent the tool from running |

## Environment Variables

Hooks receive context via environment:
- `$TOOL_NAME` - Name of the tool being used
- `$TOOL_INPUT` - JSON of the tool's input
- `$CLAUDE_PLUGIN_ROOT` - Path to the plugin directory
