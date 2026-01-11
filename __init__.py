#!/usr/bin/env python3
"""
Claude Code → OpenCode Bridge: Main Entry Point

This is the primary interface for the bridge service.
It provides a CLI and importable API for loading and executing
Claude Code components in OpenCode.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List

from .loader import BridgeLoader, BridgeRegistry
from .commands import CommandExecutor
from .hooks import HookEngine, HookType


class Bridge:
    """
    Main Bridge class that coordinates all components.
    
    Usage:
        bridge = Bridge()
        bridge.load()
        
        # Execute a command
        result = bridge.execute_command("gsd:new-project", ["my-project"])
        
        # Get a subagent
        agent = bridge.get_subagent("code-reviewer")
    """
    
    def __init__(self, project_root: Path = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.loader = BridgeLoader(self.project_root)
        self.executor = CommandExecutor(self.project_root)
        self.hook_engine = HookEngine(self.project_root)
        self.registry: Optional[BridgeRegistry] = None
    
    def load(self) -> BridgeRegistry:
        """Load all Claude Code components."""
        self.registry = self.loader.load_all()
        
        # Register all hooks
        for plugin in self.registry.plugins.values():
            self.hook_engine.register_hooks(plugin.hooks)
        
        return self.registry
    
    def list_components(self) -> dict:
        """List all loaded components."""
        if not self.registry:
            self.load()
        
        return {
            "commands": list(self.registry.commands.keys()),
            "subagents": list(self.registry.subagents.keys()),
            "skills": list(self.registry.skills.keys()),
            "plugins": list(self.registry.plugins.keys())
        }
    
    def execute_command(self, command_name: str, arguments: List[str] = None) -> dict:
        """
        Execute a Claude Code command.
        
        Args:
            command_name: Name of the command (e.g., "gsd:new-project")
            arguments: List of arguments to pass
        
        Returns:
            Dict with prepared prompt and metadata
        """
        if not self.registry:
            self.load()
        
        arguments = arguments or []
        
        # Find the command
        if command_name not in self.registry.commands:
            return {
                "error": f"Command '{command_name}' not found",
                "available": list(self.registry.commands.keys())
            }
        
        command = self.registry.commands[command_name]
        
        # Execute pre-hooks
        pre_results = self.hook_engine.execute_hooks(
            HookType.PRE_TOOL_USE,
            {"tool_name": "Command", "command_name": command_name, "arguments": arguments}
        )
        
        if self.hook_engine.should_block_action(pre_results):
            return {
                "blocked": True,
                "reason": self.hook_engine.get_blocking_message(pre_results)
            }
        
        # Prepare the prompt
        prepared_prompt = self.executor.format_for_agent(command, arguments)
        
        return {
            "command": command_name,
            "prompt": prepared_prompt,
            "allowed_tools": command.allowed_tools,
            "disallowed_tools": command.disallowed_tools,
            "model": command.model,
            "scope": command.scope
        }
    
    def get_subagent(self, agent_name: str) -> dict:
        """
        Get a subagent configuration.
        
        Args:
            agent_name: Name of the subagent
        
        Returns:
            Dict with subagent configuration
        """
        if not self.registry:
            self.load()
        
        if agent_name not in self.registry.subagents:
            return {
                "error": f"Subagent '{agent_name}' not found",
                "available": list(self.registry.subagents.keys())
            }
        
        agent = self.registry.subagents[agent_name]
        
        return {
            "name": agent.name,
            "description": agent.description,
            "system_prompt": agent.prompt,
            "tools": agent.tools,
            "disallowed_tools": agent.disallowed_tools,
            "model": agent.model,
            "permission_mode": agent.permission_mode,
            "scope": agent.scope
        }
    
    def get_skill(self, skill_name: str) -> dict:
        """
        Get a skill configuration.
        
        Args:
            skill_name: Name of the skill
        
        Returns:
            Dict with skill configuration
        """
        if not self.registry:
            self.load()
        
        if skill_name not in self.registry.skills:
            return {
                "error": f"Skill '{skill_name}' not found",
                "available": list(self.registry.skills.keys())
            }
        
        skill = self.registry.skills[skill_name]
        
        return {
            "name": skill.name,
            "description": skill.description,
            "content": skill.content,
            "allowed_tools": skill.allowed_tools,
            "context_mode": skill.context_mode,
            "user_invocable": skill.user_invocable,
            "supporting_files": [str(f) for f in skill.supporting_files]
        }
    
    def to_json(self) -> str:
        """Export the entire registry as JSON."""
        if not self.registry:
            self.load()
        return self.loader.to_json()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Code → OpenCode Bridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all components
  python -m services.cc2oc-bridge load
  
  # Execute a command
  python -m services.cc2oc-bridge run gsd:new-project my-project
  
  # Get subagent info
  python -m services.cc2oc-bridge agent code-reviewer
  
  # Export registry as JSON
  python -m services.cc2oc-bridge export
        """
    )
    
    parser.add_argument("action", choices=["load", "run", "agent", "skill", "export"],
                        help="Action to perform")
    parser.add_argument("name", nargs="?", help="Component name")
    parser.add_argument("args", nargs="*", help="Additional arguments")
    parser.add_argument("--project", "-p", default=".", help="Project root directory")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    bridge = Bridge(Path(args.project))
    
    if args.action == "load":
        bridge.load()
        components = bridge.list_components()
        
        if args.json:
            print(json.dumps(components, indent=2))
        else:
            print(f"\n{'='*50}")
            print("  Claude Code Bridge - Loaded Components")
            print(f"{'='*50}\n")
            
            print(f"Commands ({len(components['commands'])}):")
            for cmd in components['commands']:
                print(f"  /{cmd}")
            
            print(f"\nSubagents ({len(components['subagents'])}):")
            for agent in components['subagents']:
                print(f"  @{agent}")
            
            print(f"\nSkills ({len(components['skills'])}):")
            for skill in components['skills']:
                print(f"  {skill}")
            
            print(f"\nPlugins ({len(components['plugins'])}):")
            for plugin in components['plugins']:
                print(f"  {plugin}")
    
    elif args.action == "run":
        if not args.name:
            print("Error: Command name required")
            sys.exit(1)
        
        result = bridge.execute_command(args.name, args.args)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if "error" in result:
                print(f"Error: {result['error']}")
                print(f"Available commands: {', '.join(result.get('available', []))}")
            elif "blocked" in result:
                print(f"Blocked: {result['reason']}")
            else:
                print(result['prompt'])
    
    elif args.action == "agent":
        if not args.name:
            print("Error: Agent name required")
            sys.exit(1)
        
        result = bridge.get_subagent(args.name)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"\nSubagent: @{result['name']}")
                print(f"Model: {result['model']}")
                print(f"Tools: {', '.join(result['tools'])}")
                print(f"\nSystem Prompt:\n{result['system_prompt'][:500]}...")
    
    elif args.action == "skill":
        if not args.name:
            print("Error: Skill name required")
            sys.exit(1)
        
        result = bridge.get_skill(args.name)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"\nSkill: {result['name']}")
                print(f"Context Mode: {result['context_mode']}")
                print(f"Allowed Tools: {', '.join(result['allowed_tools'])}")
                print(f"\nContent:\n{result['content'][:500]}...")
    
    elif args.action == "export":
        print(bridge.to_json())


if __name__ == "__main__":
    main()
