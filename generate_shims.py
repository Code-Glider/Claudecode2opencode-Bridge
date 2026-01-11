#!/usr/bin/env python3
"""
Claude Code → OpenCode Bridge: Shim Generator

Generates native OpenCode slash command wrappers (.agent/commands/*.md)
that forward execution to the bridge agent. This makes bridge commands
visible in the IDE's autocomplete menu.
"""

import os
import shutil
from pathlib import Path
from loader import BridgeLoader

OPENCODE_COMMANDS_DIR = Path.home() / ".config/opencode/commands"
# Or local project .agent/commands if you prefer project-local shims
# OPENCODE_COMMANDS_DIR = Path(".agent/commands")

def generate_shims():
    """Generate shims for all loaded commands."""
    loader = BridgeLoader()
    registry = loader.load_all()
    
    # Ensure output directory exists (using global user config for now)
    # Note: OpenCode uses ~/.config/opencode/agent/commands usually, 
    # but let's try to put them where they will be found.
    # The user manual says we installed the agent to ~/.config/opencode/agent/cc2oc-bridge.md
    
    # Let's create a local .agent/commands directory for this project first
    # This is safer than messing with global config
    params = {
        "output_dir": Path(".agent/commands"),
        "scope": "project" 
    }
    
    if not params["output_dir"].exists():
        params["output_dir"].mkdir(parents=True)
        
    print(f"Generating shims in {params['output_dir']}...")
    
    count = 0
    for name, cmd in registry.commands.items():
        # Sanitize name for filename (replace : with _)
        safe_name = name.replace(":", "_")
        shim_path = params["output_dir"] / f"{safe_name}.md"
        
        # Create argument placeholder
        arg_str = "$ARGUMENTS" if "ARGUMENTS" in cmd.content else ""
        
        # Escape description for YAML
        desc = cmd.description.replace('"', '\\"').replace('\n', ' ')
        
        shim_content = f"""---
description: {desc} (Bridge)
---
@cc2oc-bridge run {name} {arg_str}
"""
        shim_path.write_text(shim_content)
        count += 1
        print(f"  + Created /{safe_name} -> {name}")
        
    print(f"\nGenerated {count} command shims.")
    print(f"Refreshed OpenCode to see them.")

if __name__ == "__main__":
    generate_shims()
