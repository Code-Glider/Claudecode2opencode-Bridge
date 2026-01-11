#!/usr/bin/env python3
"""
Claude Code → OpenCode Bridge: Command Executor

Executes Claude Code commands with proper argument substitution,
file references, and inline bash execution.
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .loader import Command, parse_frontmatter


@dataclass
class ExecutionContext:
    """Context for command execution."""
    project_root: Path
    arguments: List[str]
    environment: Dict[str, str]


class CommandExecutor:
    """Executes Claude Code commands with full feature support."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
    
    def prepare_prompt(self, command: Command, arguments: List[str]) -> str:
        """
        Prepare the command content for execution by:
        1. Substituting $ARGUMENTS and $1, $2, etc.
        2. Resolving @file references
        3. Executing !`bash` inline commands
        """
        content = command.content
        
        # Step 1: Substitute arguments
        content = self._substitute_arguments(content, arguments)
        
        # Step 2: Resolve file references
        content = self._resolve_file_references(content)
        
        # Step 3: Execute inline bash commands
        content = self._execute_inline_bash(content)
        
        return content
    
    def _substitute_arguments(self, content: str, arguments: List[str]) -> str:
        """Replace $ARGUMENTS and positional $1, $2, etc."""
        # Replace $ARGUMENTS with all arguments joined
        all_args = " ".join(arguments)
        content = content.replace("$ARGUMENTS", all_args)
        
        # Replace positional arguments $1, $2, ..., $9
        for i, arg in enumerate(arguments[:9], start=1):
            content = content.replace(f"${i}", arg)
        
        # Remove unreplaced positional args (if not enough arguments provided)
        for i in range(1, 10):
            content = content.replace(f"${i}", "")
        
        return content
    
    def _resolve_file_references(self, content: str) -> str:
        """
        Resolve @path/to/file references by reading file content.
        Supports both relative and absolute paths.
        """
        # Pattern: @path/to/file (not followed by another @)
        pattern = r'@([^\s@]+)'
        
        def replace_reference(match):
            file_path = match.group(1)
            
            # Try relative to project root first
            full_path = self.project_root / file_path
            if not full_path.exists():
                # Try absolute
                full_path = Path(file_path).expanduser()
            
            if full_path.exists() and full_path.is_file():
                try:
                    file_content = full_path.read_text(encoding="utf-8")
                    return f"\n--- Content of {file_path} ---\n{file_content}\n--- End of {file_path} ---\n"
                except Exception as e:
                    return f"[Error reading {file_path}: {e}]"
            else:
                return f"[File not found: {file_path}]"
        
        return re.sub(pattern, replace_reference, content)
    
    def _execute_inline_bash(self, content: str) -> str:
        """
        Execute inline bash commands marked with !`command`.
        Returns the output substituted in place.
        """
        # Pattern: !`command` or !`command with spaces`
        pattern = r'!\`([^`]+)\`'
        
        def execute_and_replace(match):
            command = match.group(1)
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.project_root
                )
                output = result.stdout.strip()
                if result.returncode != 0 and result.stderr:
                    output += f"\n[stderr: {result.stderr.strip()}]"
                return output if output else "[no output]"
            except subprocess.TimeoutExpired:
                return f"[Command timed out: {command}]"
            except Exception as e:
                return f"[Error executing '{command}': {e}]"
        
        return re.sub(pattern, execute_and_replace, content)
    
    def get_tool_restrictions(self, command: Command) -> Dict[str, List[str]]:
        """
        Parse tool restrictions from allowed-tools.
        Supports patterns like: Bash(git:*), Read, Edit
        """
        restrictions = {
            "allowed": [],
            "allowed_patterns": [],
            "disallowed": command.disallowed_tools
        }
        
        for tool in command.allowed_tools:
            # Check for pattern like Bash(git:*)
            pattern_match = re.match(r'(\w+)\(([^)]+)\)', tool)
            if pattern_match:
                tool_name = pattern_match.group(1)
                pattern = pattern_match.group(2)
                restrictions["allowed_patterns"].append({
                    "tool": tool_name,
                    "pattern": pattern
                })
            else:
                restrictions["allowed"].append(tool)
        
        return restrictions
    
    def format_for_agent(self, command: Command, arguments: List[str]) -> str:
        """
        Format the command as a complete prompt for the OpenCode agent.
        Includes tool restrictions as instructions.
        """
        prompt = self.prepare_prompt(command, arguments)
        
        restrictions = self.get_tool_restrictions(command)
        
        header = f"# Executing Command: /{command.name}\n\n"
        
        if restrictions["allowed"]:
            header += f"**Allowed Tools**: {', '.join(restrictions['allowed'])}\n"
        
        if restrictions["allowed_patterns"]:
            patterns = [f"{p['tool']}({p['pattern']})" for p in restrictions["allowed_patterns"]]
            header += f"**Tool Patterns**: {', '.join(patterns)}\n"
        
        if restrictions["disallowed"]:
            header += f"**Disallowed Tools**: {', '.join(restrictions['disallowed'])}\n"
        
        if command.model:
            header += f"**Preferred Model**: {command.model}\n"
        
        header += "\n---\n\n"
        
        return header + prompt


def main():
    """Test command execution."""
    from .loader import BridgeLoader
    
    loader = BridgeLoader()
    registry = loader.load_all()
    
    executor = CommandExecutor()
    
    # Test with first available command
    if registry.commands:
        cmd_name = list(registry.commands.keys())[0]
        cmd = registry.commands[cmd_name]
        
        print(f"Testing command: /{cmd_name}")
        print("-" * 50)
        
        result = executor.format_for_agent(cmd, ["test", "arg1", "arg2"])
        print(result[:1000])  # First 1000 chars
    else:
        print("No commands found to test.")


if __name__ == "__main__":
    main()
