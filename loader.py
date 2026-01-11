#!/usr/bin/env python3
"""
Claude Code → OpenCode Bridge: Main Loader

This module discovers and loads Claude Code plugins, commands, skills, 
subagents, and hooks from standard locations, making them available 
for execution in OpenCode.

Updated for Claude Code v2.1.x compatibility:
- Merged slash commands + skills
- Hooks in agent/skill frontmatter
- once: true hook config
- agent field in skills
- YAML-style lists in allowed-tools
"""

import os
import json
try:
    from .system_prompt import SystemPromptManager
except ImportError:
    from system_prompt import SystemPromptManager
import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union

# Standard Claude Code locations
CLAUDE_USER_DIR = Path.home() / ".claude"
CLAUDE_PROJECT_DIR = Path(".claude")


@dataclass
class Command:
    """Represents a Claude Code slash command."""
    name: str
    path: Path
    description: str = ""
    argument_hint: str = ""
    allowed_tools: List[str] = field(default_factory=list)
    disallowed_tools: List[str] = field(default_factory=list)
    model: Optional[str] = None
    hooks: Dict[str, Any] = field(default_factory=dict)
    content: str = ""
    scope: str = "project"  # "user" or "project" or "plugin"
    namespace: str = ""
    # v2.1.x: context mode for forked execution
    context: str = "main"  # "main" or "fork"
    # v2.1.x: agent field for skill execution
    agent: Optional[str] = None


@dataclass
class Subagent:
    """Represents a Claude Code subagent."""
    name: str
    path: Path
    description: str = ""
    tools: List[str] = field(default_factory=list)
    disallowed_tools: List[str] = field(default_factory=list)
    model: str = "sonnet"
    permission_mode: str = "default"
    hooks: Dict[str, Any] = field(default_factory=dict)
    skills: List[str] = field(default_factory=list)
    prompt: str = ""
    scope: str = "project"


@dataclass
class Skill:
    """Represents a Claude Code skill."""
    name: str
    path: Path
    description: str = ""
    allowed_tools: List[str] = field(default_factory=list)
    context_mode: str = "main"  # "main" or "fork"
    user_invocable: bool = True
    hooks: Dict[str, Any] = field(default_factory=dict)
    content: str = ""
    supporting_files: List[Path] = field(default_factory=list)
    # v2.1.x: agent field for skill execution
    agent: Optional[str] = None


@dataclass
class Hook:
    """Represents a single hook configuration."""
    type: str  # "command", "prompt", or "agent"
    matcher: str = ".*"  # Regex to match tool names
    command: Optional[str] = None
    prompt: Optional[str] = None
    agent: Optional[str] = None
    once: bool = False  # v2.1.x: run only once per session
    timeout: int = 600  # 10 minutes (v2.1.x update)


@dataclass
class Plugin:
    """Represents a Claude Code plugin."""
    name: str
    path: Path
    version: str = "1.0.0"
    description: str = ""
    commands: List[Command] = field(default_factory=list)
    agents: List[Subagent] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    hooks: Dict[str, Any] = field(default_factory=dict)
    mcp_config: Optional[Dict] = None


@dataclass
class BridgeRegistry:
    """Central registry of all loaded Claude Code components."""
    commands: Dict[str, Command] = field(default_factory=dict)
    subagents: Dict[str, Subagent] = field(default_factory=dict)
    skills: Dict[str, Skill] = field(default_factory=dict)
    plugins: Dict[str, Plugin] = field(default_factory=dict)
    hooks: Dict[str, List[Dict]] = field(default_factory=dict)
    # Track executed once-hooks
    executed_once_hooks: set = field(default_factory=set)


def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Extract YAML frontmatter and body from markdown content."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1)) or {}
            body = match.group(2)
            return frontmatter, body
        except yaml.YAMLError:
            return {}, content
    return {}, content


def parse_allowed_tools(tools_value: Union[str, List, None]) -> List[str]:
    """
    Parse allowed-tools which can be:
    - String: "Bash, Read, Write"
    - List: ["Bash", "Read", "Write"]
    - YAML-style list in frontmatter (already parsed as list)
    """
    if tools_value is None:
        return []
    if isinstance(tools_value, str):
        return [t.strip() for t in tools_value.split(",") if t.strip()]
    elif isinstance(tools_value, list):
        # Handle nested lists (YAML multiline)
        result = []
        for item in tools_value:
            if isinstance(item, str):
                result.append(item.strip())
            elif isinstance(item, list):
                result.extend([str(i).strip() for i in item])
        return result
    return []


def parse_hooks_from_frontmatter(hooks_value: Union[Dict, List, None]) -> Dict[str, List[Dict]]:
    """
    Parse hooks from frontmatter.
    
    Supports both dict and list formats:
    Dict: {"PreToolUse": [...], "PostToolUse": [...]}
    List: [{"type": "PreToolUse", ...}, ...]
    """
    if hooks_value is None:
        return {}
    
    if isinstance(hooks_value, dict):
        return hooks_value
    
    if isinstance(hooks_value, list):
        result = {}
        for hook in hooks_value:
            hook_type = hook.get("type", "PreToolUse")
            if hook_type not in result:
                result[hook_type] = []
            result[hook_type].append(hook)
        return result
    
    return {}


class BridgeLoader:
    """Loads Claude Code components from filesystem."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.registry = BridgeRegistry()
    
    def load_all(self) -> BridgeRegistry:
        """Load all Claude Code components."""
        # Load from user directory
        # self._load_commands(CLAUDE_USER_DIR / "commands", scope="user")
        # self._load_subagents(CLAUDE_USER_DIR / "agents", scope="user")
        # self._load_skills(CLAUDE_USER_DIR / "skills", scope="user")
        
        # Load from project directory
        project_claude = self.project_root / ".claude"
        self._load_commands(project_claude / "commands", scope="project")
        self._load_subagents(project_claude / "agents", scope="project")
        self._load_skills(project_claude / "skills", scope="project")
        
        # Load plugins
        self._load_plugins()
        
        return self.registry
    
    def _load_commands(self, commands_dir: Path, scope: str = "project"):
        """Load slash commands from a directory."""
        if not commands_dir.exists():
            return
        
        for cmd_file in commands_dir.rglob("*.md"):
            try:
                content = cmd_file.read_text(encoding="utf-8")
                frontmatter, body = parse_frontmatter(content)
                
                # Determine namespace from subdirectory
                rel_path = cmd_file.relative_to(commands_dir)
                namespace = str(rel_path.parent) if rel_path.parent != Path(".") else ""
                
                # Command name is filename without extension
                name = cmd_file.stem
                if namespace:
                    display_name = f"{namespace}:{name}"
                else:
                    display_name = name
                
                cmd = Command(
                    name=display_name,
                    path=cmd_file,
                    description=frontmatter.get("description", ""),
                    argument_hint=frontmatter.get("argument-hint", ""),
                    allowed_tools=parse_allowed_tools(frontmatter.get("allowed-tools")),
                    disallowed_tools=parse_allowed_tools(frontmatter.get("disallowedTools")),
                    model=frontmatter.get("model"),
                    hooks=parse_hooks_from_frontmatter(frontmatter.get("hooks")),
                    content=body,
                    scope=scope,
                    namespace=namespace,
                    # v2.1.x fields
                    context=frontmatter.get("context", "main"),
                    agent=frontmatter.get("agent")
                )
                
                self.registry.commands[display_name] = cmd
                
            except Exception as e:
                print(f"Warning: Failed to load command {cmd_file}: {e}")
    
    def _load_subagents(self, agents_dir: Path, scope: str = "project"):
        """Load subagents from a directory."""
        if not agents_dir.exists():
            return
        
        for agent_file in agents_dir.glob("*.md"):
            try:
                content = agent_file.read_text(encoding="utf-8")
                frontmatter, body = parse_frontmatter(content)
                
                name = frontmatter.get("name", agent_file.stem)
                
                agent = Subagent(
                    name=name,
                    path=agent_file,
                    description=frontmatter.get("description", ""),
                    tools=parse_allowed_tools(frontmatter.get("tools")),
                    disallowed_tools=parse_allowed_tools(frontmatter.get("disallowedTools")),
                    model=frontmatter.get("model", "sonnet"),
                    permission_mode=frontmatter.get("permissionMode", "default"),
                    # v2.1.x: hooks in agent frontmatter
                    hooks=parse_hooks_from_frontmatter(frontmatter.get("hooks")),
                    skills=frontmatter.get("skills", []),
                    prompt=body,
                    scope=scope
                )
                
                self.registry.subagents[name] = agent
                
            except Exception as e:
                print(f"Warning: Failed to load subagent {agent_file}: {e}")
    
    def _load_skills(self, skills_dir: Path, scope: str = "project"):
        """Load skills from a directory."""
        if not skills_dir.exists():
            return
        
        # Skills are in subdirectories with SKILL.md
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            
            try:
                content = skill_file.read_text(encoding="utf-8")
                frontmatter, body = parse_frontmatter(content)
                
                name = frontmatter.get("name", skill_dir.name)
                
                # Find supporting files
                supporting = [f for f in skill_dir.iterdir() 
                             if f.is_file() and f.name != "SKILL.md"]
                
                skill = Skill(
                    name=name,
                    path=skill_file,
                    description=frontmatter.get("description", ""),
                    allowed_tools=parse_allowed_tools(frontmatter.get("allowed-tools")),
                    context_mode=frontmatter.get("context", "main"),
                    user_invocable=frontmatter.get("user-invocable", True),
                    # v2.1.x: hooks in skill frontmatter
                    hooks=parse_hooks_from_frontmatter(frontmatter.get("hooks")),
                    content=body,
                    supporting_files=supporting,
                    # v2.1.x: agent field
                    agent=frontmatter.get("agent")
                )
                
                self.registry.skills[name] = skill
                
            except Exception as e:
                print(f"Warning: Failed to load skill {skill_dir}: {e}")
    
    def _load_plugins(self):
        """Load installed plugins."""
        # Check user plugins (disabled for testing isolation)
        # user_plugins = CLAUDE_USER_DIR / "plugins"
        # if user_plugins.exists():
        #     for plugin_dir in user_plugins.iterdir():
        #         if plugin_dir.is_dir() and plugin_dir.name != "marketplaces":
        #             self._load_plugin(plugin_dir)
        
        # Check project plugins
        project_plugins = self.project_root / ".claude-plugins"
        if project_plugins.exists():
            for plugin_dir in project_plugins.iterdir():
                if plugin_dir.is_dir():
                    self._load_plugin(plugin_dir)
        
        # Check for .claude-plugin in current directory (local plugin)
        local_plugin = self.project_root / ".claude-plugin"
        if local_plugin.exists():
            self._load_plugin(self.project_root)
        
        # Check cc2oc-bridge plugins directory
        bridge_plugins = Path(__file__).parent / "plugins"
        if bridge_plugins.exists():
            for plugin_dir in bridge_plugins.iterdir():
                if plugin_dir.is_dir():
                    self._load_plugin(plugin_dir)
    
    def _load_plugin(self, plugin_dir: Path):
        """Load a single plugin from its directory."""
        manifest_file = plugin_dir / ".claude-plugin" / "plugin.json"
        if not manifest_file.exists():
            manifest_file = plugin_dir / "plugin.json"
        
        if not manifest_file.exists():
            return
        
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            
            plugin = Plugin(
                name=manifest.get("name", plugin_dir.name),
                path=plugin_dir,
                version=manifest.get("version", "1.0.0"),
                description=manifest.get("description", "")
            )
            
            # Load plugin commands
            commands_dir = plugin_dir / manifest.get("commands", "commands")
            if commands_dir.exists():
                self._load_commands(commands_dir, scope="plugin")
            
            # Also check .claude/commands structure
            claude_commands = plugin_dir / ".claude" / "commands"
            if claude_commands.exists():
                self._load_commands(claude_commands, scope="plugin")
            
            # Load plugin agents
            agents_dir = plugin_dir / manifest.get("agents", "agents")
            if agents_dir.exists():
                self._load_subagents(agents_dir, scope="plugin")
            
            # Also check .claude/agents structure
            claude_agents = plugin_dir / ".claude" / "agents"
            if claude_agents.exists():
                self._load_subagents(claude_agents, scope="plugin")
            
            # Load plugin skills
            skills_dir = plugin_dir / manifest.get("skills", "skills")
            if skills_dir.exists():
                self._load_skills(skills_dir, scope="plugin")
            
            # Also check .claude/skills structure
            claude_skills = plugin_dir / ".claude" / "skills"
            if claude_skills.exists():
                self._load_skills(claude_skills, scope="plugin")
            
            # Load plugin hooks
            hooks_file = plugin_dir / "hooks" / "hooks.json"
            if hooks_file.exists():
                hooks_data = json.loads(hooks_file.read_text(encoding="utf-8"))
                plugin.hooks = hooks_data.get("hooks", {})
                self._merge_hooks(plugin.hooks)
            
            # Load MCP config
            mcp_file = plugin_dir / ".mcp.json"
            if mcp_file.exists():
                plugin.mcp_config = json.loads(mcp_file.read_text(encoding="utf-8"))
            
            self.registry.plugins[plugin.name] = plugin
            
        except Exception as e:
            print(f"Warning: Failed to load plugin {plugin_dir}: {e}")
    
    def _merge_hooks(self, hooks: Dict[str, Any]):
        """Merge hooks into the registry."""
        for hook_type, hook_list in hooks.items():
            if hook_type not in self.registry.hooks:
                self.registry.hooks[hook_type] = []
            if isinstance(hook_list, list):
                self.registry.hooks[hook_type].extend(hook_list)
    
    def get_system_prompt(self) -> str:
        """Get unified system prompt from CLAUDE.md files."""
        return SystemPromptManager(self.project_root).get_system_prompt()

    def to_json(self) -> str:
        """Export registry to JSON for inspection."""
        def serialize(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, set):
                return list(obj)
            elif hasattr(obj, '__dataclass_fields__'):
                return {k: serialize(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize(i) for i in obj]
            return obj
        
        return json.dumps(serialize(self.registry), indent=2)


def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Code Bridge Loader")
    parser.add_argument("--project", "-p", default=".", help="Project root directory")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--list", "-l", action="store_true", help="List loaded components")
    
    args = parser.parse_args()
    
    loader = BridgeLoader(Path(args.project))
    registry = loader.load_all()
    
    if args.json:
        print(loader.to_json())
    elif args.list:
        print(f"Commands ({len(registry.commands)}):")
        for name, cmd in registry.commands.items():
            desc = cmd.description[:50] if cmd.description else ""
            ctx = f" [context:{cmd.context}]" if cmd.context != "main" else ""
            print(f"  /{name} [{cmd.scope}]{ctx} - {desc}")
        
        print(f"\nSubagents ({len(registry.subagents)}):")
        for name, agent in registry.subagents.items():
            desc = agent.description[:50] if agent.description else ""
            hooks = " [hooks]" if agent.hooks else ""
            print(f"  @{name} [{agent.scope}]{hooks} - {desc}")
        
        print(f"\nSkills ({len(registry.skills)}):")
        for name, skill in registry.skills.items():
            desc = skill.description[:50] if skill.description else ""
            ctx = f" [context:{skill.context_mode}]" if skill.context_mode != "main" else ""
            agent = f" [agent:{skill.agent}]" if skill.agent else ""
            print(f"  {name}{ctx}{agent} - {desc}")
        
        print(f"\nPlugins ({len(registry.plugins)}):")
        for name, plugin in registry.plugins.items():
            desc = plugin.description[:50] if plugin.description else ""
            print(f"  {name} v{plugin.version} - {desc}")
    else:
        print(f"Loaded: {len(registry.commands)} commands, {len(registry.subagents)} subagents, "
              f"{len(registry.skills)} skills, {len(registry.plugins)} plugins")


if __name__ == "__main__":
    main()

# ... (rest of loader.py)

def load_system_prompt(self) -> str:
    """Load the bridged system prompt from CLAUDE.md files."""
    from .system_prompt import SystemPromptManager
    manager = SystemPromptManager(self.project_root)
    return manager.get_system_prompt()
