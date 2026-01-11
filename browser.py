#!/usr/bin/env python3
"""
Claude Code → OpenCode Bridge: Browser Integration

Integrates with the bundled dev-browser service to provide browser automation
capabilities similar to Claude's "Claude in Chrome" feature.

This provides:
- Persistent browser sessions
- LLM-friendly ARIA snapshots
- Click, type, navigate actions
- Screenshot capture
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


# Dev-browser is now bundled with cc2oc-bridge
DEV_BROWSER_DIR = Path(__file__).parent / "dev-browser"


@dataclass
class BrowserState:
    """Current state of the browser."""
    url: str = ""
    title: str = ""
    aria_snapshot: str = ""
    screenshot_path: Optional[str] = None


class BrowserIntegration:
    """
    Bridge to dev-browser for Claude-like browser control.
    
    This is the OpenCode equivalent of "Claude in Chrome".
    """
    
    def __init__(self):
        self.dev_browser_available = self._check_dev_browser()
        self.client_script = DEV_BROWSER_DIR / "client.py"
    
    def _check_dev_browser(self) -> bool:
        """Check if dev-browser service is available."""
        return DEV_BROWSER_DIR.exists() and (DEV_BROWSER_DIR / "client.py").exists()
    
    def is_available(self) -> bool:
        """Check if browser integration is available."""
        return self.dev_browser_available
    
    def setup(self) -> bool:
        """Setup dev-browser dependencies (run once after clone)."""
        if not self.dev_browser_available:
            print("dev-browser not found")
            return False
        
        try:
            # Install npm dependencies
            subprocess.run(
                ["npm", "install"],
                cwd=str(DEV_BROWSER_DIR),
                check=True
            )
            
            # Install playwright browsers
            subprocess.run(
                ["npx", "playwright", "install", "chromium"],
                cwd=str(DEV_BROWSER_DIR),
                check=True
            )
            
            return True
        except Exception as e:
            print(f"Setup failed: {e}")
            return False
    
    def start_server(self) -> bool:
        """Start the dev-browser server."""
        if not self.dev_browser_available:
            print("dev-browser service not found")
            return False
        
        server_script = DEV_BROWSER_DIR / "server.sh"
        if not server_script.exists():
            print("dev-browser server.sh not found")
            return False
        
        try:
            subprocess.Popen(
                ["bash", str(server_script)],
                cwd=str(DEV_BROWSER_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            print(f"Failed to start dev-browser: {e}")
            return False
    
    def navigate(self, url: str) -> BrowserState:
        """Navigate to a URL."""
        return self._run_action("navigate", {"url": url})
    
    def click(self, selector: str) -> BrowserState:
        """Click on an element."""
        return self._run_action("click", {"selector": selector})
    
    def type_text(self, selector: str, text: str) -> BrowserState:
        """Type text into an element."""
        return self._run_action("type", {"selector": selector, "text": text})
    
    def screenshot(self, path: Optional[str] = None) -> BrowserState:
        """Take a screenshot."""
        return self._run_action("screenshot", {"path": path or ".tmp/screenshot.png"})
    
    def get_aria_snapshot(self) -> str:
        """Get LLM-friendly ARIA snapshot of current page."""
        state = self._run_action("aria_snapshot", {})
        return state.aria_snapshot
    
    def get_state(self) -> BrowserState:
        """Get current browser state."""
        return self._run_action("state", {})
    
    def _run_action(self, action: str, params: Dict[str, Any]) -> BrowserState:
        """Run a browser action via the dev-browser client."""
        if not self.dev_browser_available:
            return BrowserState()
        
        try:
            # Build command
            cmd = ["python3", str(self.client_script), action]
            for key, value in params.items():
                cmd.extend([f"--{key}", str(value)])
            
            result = subprocess.run(
                cmd,
                cwd=str(DEV_BROWSER_DIR),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    return BrowserState(
                        url=data.get("url", ""),
                        title=data.get("title", ""),
                        aria_snapshot=data.get("aria_snapshot", ""),
                        screenshot_path=data.get("screenshot_path")
                    )
                except json.JSONDecodeError:
                    return BrowserState(aria_snapshot=result.stdout)
            else:
                print(f"Browser action failed: {result.stderr}")
                return BrowserState()
                
        except subprocess.TimeoutExpired:
            print("Browser action timed out")
            return BrowserState()
        except Exception as e:
            print(f"Browser action error: {e}")
            return BrowserState()


class BrowserTool:
    """Tool interface for browser integration."""
    
    def __init__(self):
        self.browser = BrowserIntegration()
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute a browser action."""
        if not self.browser.is_available():
            return {
                "error": "Browser not available. Run: python -c 'from browser import BrowserIntegration; BrowserIntegration().setup()'",
                "available": False
            }
        
        actions = {
            "navigate": lambda: self.browser.navigate(kwargs.get("url", "")),
            "click": lambda: self.browser.click(kwargs.get("selector", "")),
            "type": lambda: self.browser.type_text(kwargs.get("selector", ""), kwargs.get("text", "")),
            "screenshot": lambda: self.browser.screenshot(kwargs.get("path")),
            "state": lambda: self.browser.get_state()
        }
        
        if action == "aria":
            return {"aria_snapshot": self.browser.get_aria_snapshot()}
        
        if action not in actions:
            return {"error": f"Unknown action: {action}"}
        
        state = actions[action]()
        return {
            "url": state.url,
            "title": state.title,
            "aria_snapshot": state.aria_snapshot,
            "screenshot_path": state.screenshot_path
        }


def main():
    """Test browser integration."""
    browser = BrowserIntegration()
    
    print(f"dev-browser location: {DEV_BROWSER_DIR}")
    print(f"Available: {browser.is_available()}")
    
    if browser.is_available():
        print(f"Client: {browser.client_script}")
        print("\nTo setup (first time):")
        print("  from browser import BrowserIntegration")
        print("  BrowserIntegration().setup()")


if __name__ == "__main__":
    main()
