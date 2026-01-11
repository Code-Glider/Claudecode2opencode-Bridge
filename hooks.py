#!/usr/bin/env python3
"""
Claude Code → OpenCode Bridge: Hook Engine

Executes Claude Code lifecycle hooks with full v2.1.x compatibility:
- PreToolUse, PostToolUse, PostToolUseFailure, Stop
- SessionStart, SessionEnd
- SubagentStart, SubagentStop
- once: true support
- 10-minute timeout (v2.1.x update)
- command, prompt, and agent hook types
"""

import os
import re
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum


class HookType(Enum):
    PRETOOLUSE = "PreToolUse"
    POSTTOOLUSE = "PostToolUse"
    POSTTOOLUSEFAILURE = "PostToolUseFailure"
    STOP = "Stop"
    SESSIONSTART = "SessionStart"
    SESSIONEND = "SessionEnd"
    SUBAGENTSTART = "SubagentStart"
    SUBAGENTSTOP = "SubagentStop"
    PERMISSIONREQUEST = "PermissionRequest"


class HookResult(Enum):
    CONTINUE = 0  # Success, continue execution
    ERROR = 1     # Error, log and continue
    BLOCK = 2     # Block the tool from running


@dataclass
class HookContext:
    """Context passed to hook execution."""
    hook_type: HookType
    tool_name: str = ""
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_output: str = ""
    error: str = ""
    session_id: str = ""
    agent_name: str = ""
    plugin_root: str = ""
    project_root: str = ""


@dataclass
class HookConfig:
    """Configuration for a single hook."""
    type: str  # "command", "prompt", or "agent"
    matcher: str = ".*"
    command: Optional[str] = None
    prompt: Optional[str] = None
    agent: Optional[str] = None
    timeout: int = 600  # v2.1.x: 10 minutes
    once: bool = False  # v2.1.x: run only once per session


class HookEngine:
    """Executes Claude Code lifecycle hooks."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.hooks: Dict[str, List[HookConfig]] = {}
        self.executed_once_hooks: set = set()
        self.prompt_executor: Optional[Callable] = None
        self.agent_executor: Optional[Callable] = None
    
    def register_prompt_executor(self, executor: Callable[[str, HookContext], str]):
        """Register a function to execute prompt-type hooks."""
        self.prompt_executor = executor
    
    def register_agent_executor(self, executor: Callable[[str, HookContext], str]):
        """Register a function to execute agent-type hooks."""
        self.agent_executor = executor
    
    def load_hooks(self, hooks_data: Dict[str, List[Dict]]):
        """Load hooks from a hooks configuration dictionary."""
        for hook_type, hook_list in hooks_data.items():
            if hook_type not in self.hooks:
                self.hooks[hook_type] = []
            
            for hook_dict in hook_list:
                config = HookConfig(
                    type=hook_dict.get("type", "command"),
                    matcher=hook_dict.get("matcher", ".*"),
                    command=hook_dict.get("command"),
                    prompt=hook_dict.get("prompt"),
                    agent=hook_dict.get("agent"),
                    timeout=hook_dict.get("timeout", 600),
                    once=hook_dict.get("once", False)
                )
                self.hooks[hook_type].append(config)
    
    def load_hooks_from_file(self, hooks_file: Path):
        """Load hooks from a hooks.json file."""
        if not hooks_file.exists():
            return
        
        try:
            data = json.loads(hooks_file.read_text(encoding="utf-8"))
            hooks_dict = data.get("hooks", data)  # Support both wrapped and unwrapped
            self.load_hooks(hooks_dict)
        except Exception as e:
            print(f"Warning: Failed to load hooks from {hooks_file}: {e}")
    
    def load_hooks_from_frontmatter(self, hooks_data: Dict[str, Any]):
        """Load hooks from frontmatter (agent or skill)."""
        if not hooks_data:
            return
        self.load_hooks(hooks_data)
    
    def execute(self, hook_type: HookType, context: HookContext) -> HookResult:
        """
        Execute all hooks for a given type.
        
        Returns:
            HookResult.CONTINUE if all hooks pass
            HookResult.BLOCK if any hook blocks
            HookResult.ERROR if any hook errors (but doesn't block)
        """
        type_str = hook_type.value
        if type_str not in self.hooks:
            return HookResult.CONTINUE
        
        result = HookResult.CONTINUE
        
        for hook in self.hooks[type_str]:
            # Check matcher
            if not self._matches(hook.matcher, context.tool_name):
                continue
            
            # Check once flag
            hook_id = f"{type_str}:{hook.matcher}:{hook.command or hook.prompt or hook.agent}"
            if hook.once and hook_id in self.executed_once_hooks:
                continue
            
            # Execute hook
            hook_result = self._execute_hook(hook, context)
            
            # Mark as executed if once flag is set
            if hook.once:
                self.executed_once_hooks.add(hook_id)
            
            # Handle result
            if hook_result == HookResult.BLOCK:
                return HookResult.BLOCK
            elif hook_result == HookResult.ERROR:
                result = HookResult.ERROR
        
        return result
    
    def _matches(self, matcher: str, tool_name: str) -> bool:
        """Check if a tool name matches the hook's matcher regex."""
        try:
            return bool(re.match(matcher, tool_name, re.IGNORECASE))
        except re.error:
            return False
    
    def _execute_hook(self, hook: HookConfig, context: HookContext) -> HookResult:
        """Execute a single hook."""
        if hook.type == "command":
            return self._execute_command_hook(hook, context)
        elif hook.type == "prompt":
            return self._execute_prompt_hook(hook, context)
        elif hook.type == "agent":
            return self._execute_agent_hook(hook, context)
        else:
            print(f"Warning: Unknown hook type: {hook.type}")
            return HookResult.ERROR
    
    def _execute_command_hook(self, hook: HookConfig, context: HookContext) -> HookResult:
        """Execute a command-type hook."""
        if not hook.command:
            return HookResult.ERROR
        
        # Substitute variables
        command = self._substitute_variables(hook.command, context)
        
        # Set environment
        env = os.environ.copy()
        env["TOOL_NAME"] = context.tool_name
        env["TOOL_INPUT"] = json.dumps(context.tool_input)
        env["TOOL_OUTPUT"] = context.tool_output
        env["SESSION_ID"] = context.session_id
        env["AGENT_NAME"] = context.agent_name
        env["CLAUDE_PLUGIN_ROOT"] = context.plugin_root
        env["PROJECT_ROOT"] = str(context.project_root or self.project_root)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.project_root),
                env=env,
                capture_output=True,
                text=True,
                timeout=hook.timeout
            )
            
            if result.returncode == 0:
                if result.stdout:
                    print(f"[Hook] {result.stdout.strip()}")
                return HookResult.CONTINUE
            elif result.returncode == 2:
                if result.stderr:
                    print(f"[Hook BLOCKED] {result.stderr.strip()}")
                return HookResult.BLOCK
            else:
                if result.stderr:
                    print(f"[Hook ERROR] {result.stderr.strip()}")
                return HookResult.ERROR
                
        except subprocess.TimeoutExpired:
            print(f"[Hook TIMEOUT] Command timed out after {hook.timeout}s")
            return HookResult.ERROR
        except Exception as e:
            print(f"[Hook ERROR] {e}")
            return HookResult.ERROR
    
    def _execute_prompt_hook(self, hook: HookConfig, context: HookContext) -> HookResult:
        """Execute a prompt-type hook."""
        if not hook.prompt or not self.prompt_executor:
            return HookResult.ERROR
        
        try:
            prompt = self._substitute_variables(hook.prompt, context)
            result = self.prompt_executor(prompt, context)
            
            # Check result for block signal
            if result and "BLOCK" in result.upper():
                return HookResult.BLOCK
            return HookResult.CONTINUE
            
        except Exception as e:
            print(f"[Hook ERROR] Prompt execution failed: {e}")
            return HookResult.ERROR
    
    def _execute_agent_hook(self, hook: HookConfig, context: HookContext) -> HookResult:
        """Execute an agent-type hook."""
        if not hook.agent or not self.agent_executor:
            return HookResult.ERROR
        
        try:
            result = self.agent_executor(hook.agent, context)
            
            # Check result for block signal
            if result and "BLOCK" in result.upper():
                return HookResult.BLOCK
            return HookResult.CONTINUE
            
        except Exception as e:
            print(f"[Hook ERROR] Agent execution failed: {e}")
            return HookResult.ERROR
    
    def _substitute_variables(self, template: str, context: HookContext) -> str:
        """Substitute context variables in a template string."""
        result = template
        result = result.replace("${TOOL_NAME}", context.tool_name)
        result = result.replace("$TOOL_NAME", context.tool_name)
        result = result.replace("${TOOL_INPUT}", json.dumps(context.tool_input))
        result = result.replace("$TOOL_INPUT", json.dumps(context.tool_input))
        result = result.replace("${TOOL_OUTPUT}", context.tool_output)
        result = result.replace("$TOOL_OUTPUT", context.tool_output)
        result = result.replace("${SESSION_ID}", context.session_id)
        result = result.replace("$SESSION_ID", context.session_id)
        result = result.replace("${AGENT_NAME}", context.agent_name)
        result = result.replace("$AGENT_NAME", context.agent_name)
        result = result.replace("${CLAUDE_PLUGIN_ROOT}", context.plugin_root)
        result = result.replace("$CLAUDE_PLUGIN_ROOT", context.plugin_root)
        result = result.replace("${PROJECT_ROOT}", str(context.project_root or self.project_root))
        result = result.replace("$PROJECT_ROOT", str(context.project_root or self.project_root))
        return result


def main():
    """Test hook engine."""
    engine = HookEngine()
    
    # Load example hooks
    example_hooks = {
        "PreToolUse": [
            {
                "type": "command",
                "matcher": "Write|Edit",
                "command": "echo 'Pre-tool check for ${TOOL_NAME}'",
                "once": False
            }
        ],
        "PostToolUse": [
            {
                "type": "command",
                "matcher": "Bash",
                "command": "echo 'Post-bash cleanup'",
                "once": True  # Only run once per session
            }
        ]
    }
    
    engine.load_hooks(example_hooks)
    
    # Test execution
    context = HookContext(
        hook_type=HookType.PRETOOLUSE,
        tool_name="Write",
        tool_input={"path": "test.txt", "content": "Hello"}
    )
    
    result = engine.execute(HookType.PRETOOLUSE, context)
    print(f"Hook result: {result}")
    
    # Test once flag
    context2 = HookContext(
        hook_type=HookType.POSTTOOLUSE,
        tool_name="Bash",
        tool_input={"command": "ls"}
    )
    
    result1 = engine.execute(HookType.POSTTOOLUSE, context2)
    print(f"First execution: {result1}")
    
    result2 = engine.execute(HookType.POSTTOOLUSE, context2)
    print(f"Second execution (should skip due to once:true): {result2}")


if __name__ == "__main__":
    main()
