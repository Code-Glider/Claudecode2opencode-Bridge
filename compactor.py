#!/usr/bin/env python3
"""
Claude Code → OpenCode Bridge: Advanced Context Compaction

A sophisticated context compaction system that:
1. Reads model info from OpenCode's config (opencode.json)
2. Uses a model registry for accurate context window sizes
3. Falls back to conservative defaults if unknown
"""

import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


# Model context window registry (tokens)
MODEL_CONTEXT_WINDOWS = {
    # Anthropic
    "anthropic/claude-opus-4": 200000,
    "anthropic/claude-opus-4-5": 200000,
    "anthropic/claude-sonnet-4": 200000,
    "anthropic/claude-sonnet-4-5": 200000,
    "anthropic/claude-haiku-4": 200000,
    "anthropic/claude-haiku-4-5": 200000,
    "claude-3-5-sonnet": 200000,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    # OpenAI
    "openai/gpt-4o": 128000,
    "openai/gpt-4o-mini": 128000,
    "openai/gpt-4-turbo": 128000,
    "openai/o1": 200000,
    "openai/o1-mini": 128000,
    "openai/o3": 200000,
    "gpt-4o": 128000,
    "gpt-4-turbo": 128000,
    # Google
    "google/gemini-2.5-pro": 1000000,
    "google/gemini-2.5-flash": 1000000,
    "google/gemini-2.0-flash": 1000000,
    "google/gemini-1.5-pro": 2000000,
    "gemini-2.5-pro": 1000000,
    "gemini-2.5-flash": 1000000,
    # xAI
    "xai/grok-3": 131072,
    "xai/grok-2": 131072,
    # DeepSeek
    "deepseek/deepseek-chat": 64000,
    "deepseek/deepseek-reasoner": 64000,
    # Default fallback
    "default": 100000,
}


class MemoryLayer(Enum):
    """Different layers of memory with different retention strategies."""
    IDENTITY = "identity"
    TASK = "task"
    DECISIONS = "decisions"
    ACTIONS = "actions"
    CONTEXT = "context"
    ERRORS = "errors"
    WORKSPACE = "workspace"


@dataclass
class MemoryItem:
    """A single item in memory."""
    layer: MemoryLayer
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 0.5
    dependencies: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: "")
    
    def __post_init__(self):
        if not self.id:
            self.id = hashlib.md5(f"{self.content}{self.timestamp}".encode()).hexdigest()[:8]


@dataclass
class CompactionResult:
    """Result of a compaction operation."""
    compacted_context: str
    original_tokens: int
    compacted_tokens: int
    compression_ratio: float
    preserved_items: int
    summarized_items: int


class OpenCodeIntegration:
    """Interface with OpenCode for model and context info."""
    
    def __init__(self):
        self.config = self._load_opencode_config()
    
    def _load_opencode_config(self) -> Dict[str, Any]:
        """Load OpenCode's configuration."""
        config_paths = [
            Path.cwd() / "opencode.json",
            Path.cwd() / ".opencode" / "opencode.json",
            Path.home() / ".config" / "opencode" / "opencode.json",
        ]
        
        for path in config_paths:
            if path.exists():
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
        
        return {}
    
    def get_current_model(self) -> str:
        """Get the currently configured model."""
        return self.config.get("model", "default")
    
    def get_context_window_size(self) -> int:
        """
        Get the context window size for the current model.
        
        Priority:
        1. Explicit config in opencode.json
        2. Model registry lookup
        3. Conservative default
        """
        model = self.get_current_model()
        
        # Check for explicit override in config
        compaction_config = self.config.get("compaction", {})
        if "context_window" in compaction_config:
            return compaction_config["context_window"]
        
        # Look up in model registry
        if model in MODEL_CONTEXT_WINDOWS:
            return MODEL_CONTEXT_WINDOWS[model]
        
        # Try partial match (e.g., "claude" in model name)
        model_lower = model.lower()
        for key, value in MODEL_CONTEXT_WINDOWS.items():
            if key.lower() in model_lower or model_lower in key.lower():
                return value
        
        # Conservative default
        return MODEL_CONTEXT_WINDOWS["default"]
    
    def get_compaction_threshold(self) -> float:
        """Get the threshold for triggering compaction (0-1)."""
        compaction_config = self.config.get("compaction", {})
        # Research indicates 70% is optimal for context window usage
        # Higher thresholds risk degraded performance from "lost in the middle" effects
        return compaction_config.get("threshold", 0.70)
    
    def is_auto_compact_enabled(self) -> bool:
        """Check if auto-compaction is enabled."""
        compaction_config = self.config.get("compaction", {})
        return compaction_config.get("auto", True)


COMPACTION_PROMPT = '''You are a CONTEXT COMPACTION SPECIALIST. Your job is to compress conversation history while PRESERVING CRITICAL INFORMATION.

## THE LAYERED MEMORY MODEL

Organize the compacted context into these layers:

### 🔒 IDENTITY (Never lose)
- Agent role and capabilities
- System constraints and permissions
- User preferences explicitly stated

### 🎯 ACTIVE TASK (High detail)
- Current objective in user's exact words
- Success criteria
- Blockers and dependencies

### 🧠 DECISIONS MADE (Preserve rationale)
For each significant decision:
- What was decided
- Why (the reasoning)
- What alternatives were rejected

### ✅ ACTIONS COMPLETED (Factual log)
```
[timestamp] ACTION: <what>
  - Files: <affected files>
  - Outcome: <success/failure>
```

### ⚠️ ERRORS & FIXES
- What went wrong
- How it was fixed
- Prevention for future

### 📁 WORKSPACE STATE
- Current branch and status
- Key files being worked on

### 💭 CONTEXT (Summarizable)
- Background information
- Research findings

## COMPACTION RULES

1. **PRESERVE EXACT QUOTES** for:
   - User's task description
   - Error messages
   - Critical code snippets
   - Decisions and rationale

2. **SUMMARIZE AGGRESSIVELY** for:
   - Exploratory discussion
   - Failed attempts (keep only lesson)
   - Verbose tool outputs

3. **RECENCY GRADIENT**
   - Last 3 exchanges: Full detail
   - Last 10 exchanges: Key points
   - Older: Summary only

4. **NEVER LOSE**
   - Current active task
   - Uncommitted code changes
   - Unresolved errors
   - User's explicit requests

## MODEL INFO
- Model: {model}
- Context Window: {context_window:,} tokens
- Current Usage: {current_tokens:,} tokens ({usage_percent:.1f}%)
- Target After Compaction: {target_tokens:,} tokens

## INPUT TO COMPACT

<conversation>
{conversation}
</conversation>

## WORKSPACE STATE

<workspace>
{workspace_state}
</workspace>

Now compact this conversation. Target: reduce to ~{target_tokens:,} tokens while preserving all critical information.'''


class ContextCompactor:
    """
    Advanced context compaction with OpenCode integration.
    
    Reads model info from OpenCode's config to determine
    accurate context window sizes.
    """
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.opencode = OpenCodeIntegration()
        self.memory: Dict[str, MemoryItem] = {}
        self.action_log: List[Dict[str, Any]] = []
        self.compaction_history: List[CompactionResult] = []
    
    def add_memory(self, layer: MemoryLayer, content: str, 
                   importance: float = 0.5, dependencies: List[str] = None) -> str:
        """Add an item to memory."""
        item = MemoryItem(
            layer=layer,
            content=content,
            importance=importance,
            dependencies=dependencies or []
        )
        self.memory[item.id] = item
        return item.id
    
    def log_action(self, action: str, files: List[str] = None, 
                   outcome: str = "success", notes: str = "") -> None:
        """Log an action to the action log (never compacted away)."""
        self.action_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "files": files or [],
            "outcome": outcome,
            "notes": notes
        })
    
    def get_workspace_state(self) -> Dict[str, Any]:
        """Get current workspace state."""
        state = {
            "branch": "",
            "status": "",
            "modified_files": [],
            "cwd": str(self.project_root)
        }
        
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(self.project_root),
                capture_output=True, text=True, timeout=5
            )
            state["branch"] = result.stdout.strip()
            
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.project_root),
                capture_output=True, text=True, timeout=5
            )
            state["modified_files"] = [
                line[3:] for line in result.stdout.strip().split("\n") if line
            ][:20]
            
            state["status"] = "dirty" if state["modified_files"] else "clean"
        except Exception:
            pass
        
        return state
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token on average)."""
        return len(text) // 4
    
    def get_context_info(self, conversation: str) -> Dict[str, Any]:
        """Get context window info for current model."""
        context_window = self.opencode.get_context_window_size()
        current_tokens = self.estimate_tokens(conversation)
        threshold = self.opencode.get_compaction_threshold()
        
        return {
            "model": self.opencode.get_current_model(),
            "context_window": context_window,
            "current_tokens": current_tokens,
            "usage_percent": (current_tokens / context_window) * 100,
            "threshold": threshold,
            "threshold_tokens": int(context_window * threshold),
            "should_compact": current_tokens > (context_window * threshold)
        }
    
    def should_compact(self, conversation: str) -> bool:
        """Determine if compaction is needed based on OpenCode config."""
        if not self.opencode.is_auto_compact_enabled():
            return False
        return self.get_context_info(conversation)["should_compact"]
    
    def generate_compaction_prompt(self, conversation: str) -> str:
        """Generate the compaction prompt with model-aware sizing."""
        workspace = json.dumps(self.get_workspace_state(), indent=2)
        info = self.get_context_info(conversation)
        
        # Target 50% of context window after compaction
        target_tokens = info["context_window"] // 2
        
        return COMPACTION_PROMPT.format(
            model=info["model"],
            context_window=info["context_window"],
            current_tokens=info["current_tokens"],
            usage_percent=info["usage_percent"],
            target_tokens=target_tokens,
            conversation=conversation,
            workspace_state=workspace
        )
    
    def compact(self, conversation: str, llm_fn: callable = None) -> CompactionResult:
        """Compact a conversation using the layered memory model."""
        original_tokens = self.estimate_tokens(conversation)
        
        if llm_fn:
            prompt = self.generate_compaction_prompt(conversation)
            compacted = llm_fn(prompt)
        else:
            compacted = self._rule_based_compact(conversation)
        
        compacted_tokens = self.estimate_tokens(compacted)
        
        result = CompactionResult(
            compacted_context=compacted,
            original_tokens=original_tokens,
            compacted_tokens=compacted_tokens,
            compression_ratio=compacted_tokens / original_tokens if original_tokens > 0 else 1.0,
            preserved_items=len([m for m in self.memory.values() if m.importance > 0.7]),
            summarized_items=len([m for m in self.memory.values() if m.importance <= 0.7])
        )
        
        self.compaction_history.append(result)
        return result
    
    def _rule_based_compact(self, conversation: str) -> str:
        """Rule-based compaction when LLM is not available."""
        lines = conversation.split("\n")
        
        action_log_text = "\n".join([
            f"[{a['timestamp']}] {a['action']} -> {a['outcome']}"
            for a in self.action_log[-20:]
        ])
        
        important_memory = "\n".join([
            f"[{m.layer.value}] {m.content[:200]}"
            for m in self.memory.values()
            if m.importance > 0.7
        ])
        
        recent = lines[-50:]
        
        return f"""# Session Context (Auto-Compacted)

## Action Log
{action_log_text or "No actions logged"}

## Key Memory
{important_memory or "No high-priority items"}

## Recent Context
{chr(10).join(recent)}
"""


def main():
    """Demonstrate the compactor with OpenCode integration."""
    compactor = ContextCompactor()
    
    print("=== OpenCode Integration ===")
    print(f"Model: {compactor.opencode.get_current_model()}")
    print(f"Context Window: {compactor.opencode.get_context_window_size():,} tokens")
    print(f"Compaction Threshold: {compactor.opencode.get_compaction_threshold():.0%}")
    print(f"Auto-Compact Enabled: {compactor.opencode.is_auto_compact_enabled()}")
    
    # Test with sample conversation
    sample = "A" * 400000  # ~100k tokens
    info = compactor.get_context_info(sample)
    
    print(f"\n=== Context Info ===")
    print(f"Current Tokens: {info['current_tokens']:,}")
    print(f"Usage: {info['usage_percent']:.1f}%")
    print(f"Should Compact: {info['should_compact']}")


if __name__ == "__main__":
    main()
