"""
Claude Code → OpenCode Bridge: Shims Package

Provides emulation of Claude Code-specific tools.
"""

from .tools import (
    AskFollowupQuestion,
    SkillExecutor,
    NotebookEdit,
    TaskRunner
)

__all__ = [
    "AskFollowupQuestion",
    "SkillExecutor", 
    "NotebookEdit",
    "TaskRunner"
]
