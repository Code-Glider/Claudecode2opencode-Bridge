#!/usr/bin/env python3
"""
Claude Code → OpenCode Bridge: System Prompt Manager

Reads and manages system prompts from CLAUDE.md files, similar to how
OpenCode natively handles AGENTS.md/GEMINI.md.

Behavior:
1. Scans project root for CLAUDE.md
2. Scans user home for ~/.claude/CLAUDE.md
3. Merges them (project overrides user)
4. Injects context from .claude/project-context.md if present
5. Inserts into the conversation as a system message
"""

from pathlib import Path
from typing import Optional, List, Dict
import os

class SystemPromptManager:
    """Manages system prompts from CLAUDE.md files."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.home_dir = Path.home()
        
    def get_system_prompt(self) -> str:
        """
        Construct the full system prompt from all sources.
        
        Priority (merged):
        1. ~/.claude/CLAUDE.md (Global instructions)
        2. ./CLAUDE.md (Project instructions)
        3. ./.claude/project-context.md (Project context/status)
        """
        sections = []
        
        # 1. Global Instructions
        global_claude = self.home_dir / ".claude" / "CLAUDE.md"
        if global_claude.exists():
            content = global_claude.read_text(encoding="utf-8").strip()
            if content:
                sections.append(f"## GLOBAL INSTRUCTIONS\n{content}")
                
        # 2. Project Instructions
        project_claude = self.project_root / "CLAUDE.md"
        if project_claude.exists():
            content = project_claude.read_text(encoding="utf-8").strip()
            if content:
                sections.append(f"## PROJECT INSTRUCTIONS\n{content}")
        
        # 3. Project Context
        project_context = self.project_root / ".claude" / "project-context.md"
        if project_context.exists():
            content = project_context.read_text(encoding="utf-8").strip()
            if content:
                sections.append(f"## PROJECT CONTEXT\n{content}")
                
        if not sections:
            return ""
            
        return "\n\n".join(sections)
    
    def get_opencode_instruction_config(self) -> Dict[str, str]:
        """
        Get the configuration for OpenCode's instructions.json.
        This allows persistent bridging of the CLAUDE.md content.
        """
        prompt = self.get_system_prompt()
        if not prompt:
            return {}
            
        return {
            "instructions": prompt
        }


def main():
    """Test system prompt loading."""
    manager = SystemPromptManager()
    prompt = manager.get_system_prompt()
    
    if prompt:
        print("=== Loaded System Prompt ===")
        print(f"Length: {len(prompt)} chars")
        print("Sources detected:")
        if (Path.home() / ".claude" / "CLAUDE.md").exists():
            print("- Global (~/.claude/CLAUDE.md)")
        if Path("CLAUDE.md").exists():
            print("- Project (CLAUDE.md)")
        if Path(".claude/project-context.md").exists():
            print("- Context (.claude/project-context.md)")
        print("\nPreview:")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    else:
        print("No CLAUDE.md files found.")

if __name__ == "__main__":
    main()
