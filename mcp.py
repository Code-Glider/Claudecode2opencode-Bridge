#!/usr/bin/env python3
"""
cc2oc-bridge: MCP Integration

Handles Model Context Protocol server configuration passthrough
from Claude Code plugins to OpenCode.

OpenCode MCP format (in opencode.json):
{
  "mcp": {
    "server-name": {
      "type": "local",
      "command": ["npx", "-y", "some-mcp-server"],
      "enabled": true,
      "environment": {}
    }
  }
}

Claude Code MCP format (.mcp.json):
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "some-mcp-server"],
      "env": {}
    }
  }
}
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


def convert_claude_to_opencode_mcp(claude_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Claude Code MCP format to OpenCode format.
    
    Claude: {"mcpServers": {"name": {"command": "npx", "args": [...], "env": {...}}}}
    OpenCode: {"mcp": {"name": {"type": "local", "command": [...], "enabled": true, "environment": {...}}}}
    """
    opencode_mcp = {}
    
    for server_name, server_config in claude_config.get("mcpServers", {}).items():
        # Build command array
        command = server_config.get("command", "")
        args = server_config.get("args", [])
        
        if isinstance(command, str):
            command_array = [command] + args
        else:
            command_array = command
        
        # Convert environment
        environment = server_config.get("env", {})
        
        opencode_mcp[server_name] = {
            "type": "local",
            "command": command_array,
            "enabled": True,
            "environment": environment
        }
    
    return {"mcp": opencode_mcp}


class MCPManager:
    """Manages MCP server configurations for the bridge."""
    
    def __init__(self):
        self.servers: Dict[str, Dict[str, Any]] = {}
    
    def load_from_claude_plugin(self, plugin_path: Path) -> Dict[str, Any]:
        """
        Load MCP configuration from a Claude Code plugin's .mcp.json file.
        """
        mcp_file = plugin_path / ".mcp.json"
        if not mcp_file.exists():
            return {}
        
        try:
            claude_config = json.loads(mcp_file.read_text(encoding="utf-8"))
            opencode_config = convert_claude_to_opencode_mcp(claude_config)
            
            # Register servers
            self.servers.update(opencode_config.get("mcp", {}))
            
            return opencode_config
        except Exception as e:
            print(f"Warning: Failed to load MCP config from {mcp_file}: {e}")
            return {}
    
    def get_opencode_mcp_config(self) -> Dict[str, Any]:
        """Generate OpenCode-compatible MCP configuration."""
        return {"mcp": self.servers}
    
    def export_to_opencode_config(self, opencode_config_path: Path = None) -> bool:
        """
        Export MCP servers to OpenCode's configuration.
        
        Args:
            opencode_config_path: Path to opencode.json (defaults to ~/.config/opencode/opencode.json)
        """
        if not self.servers:
            return False
        
        if opencode_config_path is None:
            opencode_config_path = Path.home() / ".config" / "opencode" / "opencode.json"
        
        try:
            # Load existing config if present
            existing = {}
            if opencode_config_path.exists():
                existing = json.loads(opencode_config_path.read_text(encoding="utf-8"))
            
            # Merge MCP servers
            existing_mcp = existing.get("mcp", {})
            existing_mcp.update(self.servers)
            existing["mcp"] = existing_mcp
            
            # Ensure schema is present
            if "$schema" not in existing:
                existing["$schema"] = "https://opencode.ai/config.json"
            
            # Write back
            opencode_config_path.parent.mkdir(parents=True, exist_ok=True)
            opencode_config_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
            
            print(f"Exported {len(self.servers)} MCP server(s) to {opencode_config_path}")
            return True
        except Exception as e:
            print(f"Error exporting MCP config: {e}")
            return False
    
    def list_servers(self) -> List[str]:
        """List all registered MCP server names."""
        return list(self.servers.keys())


def main():
    """Test MCP conversion."""
    # Example Claude Code config
    claude_config = {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            },
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_TOKEN": "${GITHUB_TOKEN}"
                }
            }
        }
    }
    
    print("Claude Code format:")
    print(json.dumps(claude_config, indent=2))
    
    print("\nConverted to OpenCode format:")
    opencode_config = convert_claude_to_opencode_mcp(claude_config)
    print(json.dumps(opencode_config, indent=2))


if __name__ == "__main__":
    main()
