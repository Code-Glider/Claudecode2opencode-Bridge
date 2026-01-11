#!/usr/bin/env python3
"""
Claude Code → OpenCode Bridge: Tool Shims

Provides emulation of Claude Code-specific tools that don't have 
direct OpenCode equivalents.
"""

import sys
import json
from typing import List, Optional, Dict, Any


class AskFollowupQuestion:
    """
    Emulates Claude Code's AskFollowupQuestion tool.
    
    In Claude Code, this presents a multi-choice question to the user.
    In OpenCode, we simulate this by printing the question and reading stdin.
    """
    
    @staticmethod
    def ask(
        header: str,
        question: str,
        options: List[str],
        allow_freeform: bool = True
    ) -> str:
        """
        Present a question to the user with multiple choice options.
        
        Args:
            header: Title/header for the question
            question: The question text
            options: List of option strings
            allow_freeform: Whether to allow a custom response
        
        Returns:
            The selected option or user's freeform response
        """
        print(f"\n{'='*50}")
        print(f"  {header}")
        print(f"{'='*50}")
        print(f"\n{question}\n")
        
        for i, option in enumerate(options, start=1):
            print(f"  [{i}] {option}")
        
        if allow_freeform:
            print(f"  [0] Enter custom response")
        
        print()
        
        while True:
            try:
                choice = input("Your choice: ").strip()
                
                # Check if it's a number
                if choice.isdigit():
                    choice_num = int(choice)
                    if choice_num == 0 and allow_freeform:
                        return input("Enter your response: ").strip()
                    elif 1 <= choice_num <= len(options):
                        return options[choice_num - 1]
                    else:
                        print(f"Please enter a number between 1 and {len(options)}")
                else:
                    # Treat as freeform if allowed
                    if allow_freeform:
                        return choice
                    else:
                        print("Please enter a valid option number")
                        
            except EOFError:
                # Non-interactive mode, return first option
                return options[0] if options else ""
            except KeyboardInterrupt:
                print("\nCancelled")
                return ""
    
    @staticmethod
    def format_for_agent(
        header: str,
        question: str,
        options: List[str]
    ) -> str:
        """
        Format the question for agent consumption (non-interactive).
        Returns a formatted prompt that the agent can present.
        """
        formatted = f"\n## {header}\n\n{question}\n\n**Options:**\n"
        for i, option in enumerate(options, start=1):
            formatted += f"{i}. {option}\n"
        formatted += "\nPlease select an option by number or provide your own response."
        return formatted


class SkillExecutor:
    """
    Emulates Claude Code's Skill tool.
    
    Executes a skill or slash command within the current conversation context.
    """
    
    def __init__(self, registry):
        self.registry = registry
    
    def execute(self, skill_name: str, arguments: str = "") -> Dict[str, Any]:
        """
        Execute a skill by name.
        
        Args:
            skill_name: Name of the skill to execute
            arguments: Optional arguments string
        
        Returns:
            Dict with skill content and metadata
        """
        # Check if it's a skill
        if skill_name in self.registry.skills:
            skill = self.registry.skills[skill_name]
            return {
                "type": "skill",
                "name": skill.name,
                "content": skill.content,
                "allowed_tools": skill.allowed_tools,
                "supporting_files": [str(f) for f in skill.supporting_files],
                "context_mode": skill.context_mode
            }
        
        # Check if it's a command
        if skill_name in self.registry.commands:
            cmd = self.registry.commands[skill_name]
            return {
                "type": "command",
                "name": cmd.name,
                "content": cmd.content,
                "allowed_tools": cmd.allowed_tools,
                "description": cmd.description
            }
        
        return {
            "error": f"Skill or command '{skill_name}' not found"
        }


class NotebookEdit:
    """
    Emulates Claude Code's NotebookEdit tool for Jupyter notebooks.
    
    Since OpenCode may not have native notebook support, we provide
    a file-based editing approach.
    """
    
    @staticmethod
    def edit_cell(
        notebook_path: str,
        cell_index: int,
        new_content: str,
        cell_type: str = "code"
    ) -> Dict[str, Any]:
        """
        Edit a cell in a Jupyter notebook.
        
        Args:
            notebook_path: Path to the .ipynb file
            cell_index: Index of the cell to edit
            new_content: New content for the cell
            cell_type: "code" or "markdown"
        
        Returns:
            Result of the operation
        """
        import json
        from pathlib import Path
        
        try:
            path = Path(notebook_path)
            if not path.exists():
                return {"error": f"Notebook not found: {notebook_path}"}
            
            notebook = json.loads(path.read_text(encoding="utf-8"))
            
            cells = notebook.get("cells", [])
            if cell_index < 0 or cell_index >= len(cells):
                return {"error": f"Cell index {cell_index} out of range (0-{len(cells)-1})"}
            
            # Update the cell
            cells[cell_index]["source"] = new_content.splitlines(keepends=True)
            cells[cell_index]["cell_type"] = cell_type
            
            # Write back
            path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
            
            return {
                "success": True,
                "message": f"Updated cell {cell_index} in {notebook_path}"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def add_cell(
        notebook_path: str,
        content: str,
        cell_type: str = "code",
        position: int = -1
    ) -> Dict[str, Any]:
        """Add a new cell to a notebook."""
        import json
        from pathlib import Path
        
        try:
            path = Path(notebook_path)
            if not path.exists():
                return {"error": f"Notebook not found: {notebook_path}"}
            
            notebook = json.loads(path.read_text(encoding="utf-8"))
            
            new_cell = {
                "cell_type": cell_type,
                "source": content.splitlines(keepends=True),
                "metadata": {},
            }
            
            if cell_type == "code":
                new_cell["outputs"] = []
                new_cell["execution_count"] = None
            
            cells = notebook.get("cells", [])
            if position < 0:
                cells.append(new_cell)
            else:
                cells.insert(position, new_cell)
            
            notebook["cells"] = cells
            path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
            
            return {
                "success": True,
                "message": f"Added new {cell_type} cell to {notebook_path}"
            }
            
        except Exception as e:
            return {"error": str(e)}


class TaskRunner:
    """
    Emulates Claude Code's Task tool for running subagents.
    
    In the bridge context, this prepares the subagent configuration
    for OpenCode to execute.
    """
    
    def __init__(self, registry):
        self.registry = registry
    
    def prepare_task(
        self,
        agent_name: str,
        prompt: str,
        background: bool = False
    ) -> Dict[str, Any]:
        """
        Prepare a subagent task for execution.
        
        Args:
            agent_name: Name of the subagent to run
            prompt: The task prompt
            background: Whether to run in background
        
        Returns:
            Task configuration for the agent
        """
        # Find the subagent
        if agent_name in self.registry.subagents:
            agent = self.registry.subagents[agent_name]
            return {
                "type": "subagent",
                "name": agent.name,
                "system_prompt": agent.prompt,
                "user_prompt": prompt,
                "tools": agent.tools,
                "model": agent.model,
                "permission_mode": agent.permission_mode,
                "background": background
            }
        
        # Built-in agents
        if agent_name.lower() in ["explore", "plan", "general"]:
            return {
                "type": "builtin",
                "name": agent_name,
                "user_prompt": prompt,
                "background": background
            }
        
        return {
            "error": f"Subagent '{agent_name}' not found"
        }


# Entry point for CLI testing
def main():
    print("Testing AskFollowupQuestion shim...")
    
    result = AskFollowupQuestion.format_for_agent(
        header="Project Type",
        question="What type of project are you building?",
        options=["Web Application", "CLI Tool", "Library", "API Service"]
    )
    
    print(result)


if __name__ == "__main__":
    main()
