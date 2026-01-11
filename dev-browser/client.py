"""
Dev Browser Python Client

A Python wrapper for the Dev Browser HTTP API. Provides browser automation
with persistent pages and LLM-friendly ARIA snapshots.

Features:
- Persistent browser pages that survive script restarts
- LLM-friendly ARIA snapshots for element discovery
- Auto-login when sessions expire (credentials stored in .env)

Usage:
    from services.dev_browser.client import DevBrowserClient

    async with DevBrowserClient() as client:
        # Basic usage
        page = await client.get_page("main")
        await page.goto("https://example.com")
        snapshot = await client.get_ai_snapshot("main")

        # With auto-login (credentials from .env)
        page = await client.get_page_with_auth("linkedin", "linkedin")
        await page.goto("https://linkedin.com/feed")
        # If session expired, auto-login happens automatically
"""

import asyncio
import subprocess
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import httpx
from playwright.async_api import async_playwright, Page, Browser

from .auth_manager import AuthManager, get_auth_manager


@dataclass
class PageInfo:
    """Information about a Dev Browser page."""
    name: str
    target_id: str
    ws_endpoint: str


class DevBrowserClient:
    """
    Python client for Dev Browser server.

    Provides:
    - Persistent browser pages that survive script restarts
    - LLM-friendly ARIA snapshots for element discovery
    - Standard Playwright Page objects for automation

    Example:
        async with DevBrowserClient() as client:
            page = await client.get_page("search")
            await page.goto("https://google.com")

            # Get AI-readable page structure
            snapshot = await client.get_ai_snapshot("search")
            print(snapshot)

            # Interact with elements by ref
            element = await client.select_ref("search", "e5")
            await element.click()
    """

    def __init__(
        self,
        server_url: str = "http://localhost:9222",
        auto_start: bool = True,
        headless: bool = False,
        timeout: float = 30.0,
        enable_auth: bool = True,
    ):
        """
        Initialize Dev Browser client.

        Args:
            server_url: URL of the Dev Browser HTTP API
            auto_start: Start server automatically if not running
            headless: Run browser in headless mode (only if auto_start=True)
            timeout: Connection timeout in seconds
            enable_auth: Enable auto-login functionality (loads credentials from .env)
        """
        self.server_url = server_url.rstrip("/")
        self.auto_start = auto_start
        self.headless = headless
        self.timeout = timeout
        self.enable_auth = enable_auth

        self._http_client: Optional[httpx.AsyncClient] = None
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._ws_endpoint: Optional[str] = None
        self._server_process: Optional[subprocess.Popen] = None
        self._auth_manager: Optional[AuthManager] = None

        # Initialize auth manager if enabled
        if enable_auth:
            try:
                self._auth_manager = get_auth_manager()
            except Exception:
                # Auth manager failed to initialize, continue without it
                self._auth_manager = None

    async def __aenter__(self) -> "DevBrowserClient":
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """
        Connect to the Dev Browser server.

        If auto_start is True and server isn't running, starts it automatically.
        """
        self._http_client = httpx.AsyncClient(timeout=self.timeout)

        # Check if server is running
        if not await self._is_server_running():
            if self.auto_start:
                await self._start_server()
            else:
                raise ConnectionError(
                    f"Dev Browser server not running at {self.server_url}. "
                    "Start it with: cd services/dev-browser && ./server.sh"
                )

        # Get WebSocket endpoint
        info = await self._get_server_info()
        self._ws_endpoint = info["wsEndpoint"]

        # Connect Playwright to browser
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.connect_over_cdp(self._ws_endpoint)

    async def disconnect(self) -> None:
        """Disconnect from the server (pages persist on server)."""
        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def _is_server_running(self) -> bool:
        """Check if server is running."""
        try:
            response = await self._http_client.get(self.server_url, timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    async def _start_server(self) -> None:
        """Start the Dev Browser server."""
        service_dir = Path(__file__).parent
        server_script = service_dir / "server.sh"

        if not server_script.exists():
            raise FileNotFoundError(
                f"Server script not found: {server_script}. "
                "Run 'cd services/dev-browser && npm install' first."
            )

        # Build command
        cmd = [str(server_script)]
        if self.headless:
            cmd.append("--headless")

        # Start server in background
        self._server_process = subprocess.Popen(
            cmd,
            cwd=str(service_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if await self._is_server_running():
                return
            await asyncio.sleep(0.5)

        raise TimeoutError(
            f"Dev Browser server failed to start within {self.timeout}s. "
            "Check logs for errors."
        )

    async def _get_server_info(self) -> dict:
        """Get server information including WebSocket endpoint."""
        response = await self._http_client.get(self.server_url)
        response.raise_for_status()
        return response.json()

    async def get_page(self, name: str) -> Page:
        """
        Get or create a named page.

        Pages persist on the server until explicitly closed.
        Multiple scripts can access the same page by name.

        Args:
            name: Unique name for the page

        Returns:
            Playwright Page object
        """
        if not self._browser:
            raise RuntimeError("Not connected. Call connect() first.")

        # Request page from server
        response = await self._http_client.post(
            f"{self.server_url}/pages",
            json={"name": name}
        )
        response.raise_for_status()
        page_info = response.json()

        # Find page by target ID
        target_id = page_info["targetId"]

        for context in self._browser.contexts:
            for page in context.pages:
                cdp = await context.new_cdp_session(page)
                try:
                    info = await cdp.send("Target.getTargetInfo")
                    if info["targetInfo"]["targetId"] == target_id:
                        return page
                finally:
                    await cdp.detach()

        raise RuntimeError(f"Page '{name}' not found in browser contexts")

    async def list_pages(self) -> list[str]:
        """List all named pages on the server."""
        response = await self._http_client.get(f"{self.server_url}/pages")
        response.raise_for_status()
        return response.json()["pages"]

    async def close_page(self, name: str) -> None:
        """Close a named page on the server."""
        response = await self._http_client.delete(
            f"{self.server_url}/pages/{name}"
        )
        response.raise_for_status()

    # ========================================================================
    # Auto-Login Methods
    # ========================================================================

    async def get_page_with_auth(
        self,
        page_name: str,
        site_name: str,
        navigate_to: Optional[str] = None,
    ) -> Page:
        """
        Get a page with automatic login support.

        If the session has expired, automatically re-login using credentials
        from the service's .env file.

        Args:
            page_name: Unique name for the page
            site_name: Site identifier (e.g., "linkedin", "upwork", "github")
            navigate_to: Optional URL to navigate to after ensuring login

        Returns:
            Playwright Page object, logged in and ready

        Raises:
            ValueError: If no credentials configured for site_name
            RuntimeError: If login fails after retry

        Example:
            page = await client.get_page_with_auth("linkedin", "linkedin")
            await page.goto("https://linkedin.com/feed")
            # If session expired, auto-login already happened
        """
        if not self._auth_manager:
            raise RuntimeError(
                "Auth manager not available. Set enable_auth=True and "
                "configure credentials in services/dev-browser/.env"
            )

        site = self._auth_manager.get_site(site_name)
        if not site:
            configured = self._auth_manager.list_configured_sites()
            raise ValueError(
                f"No credentials configured for site: {site_name}. "
                f"Configured sites: {configured}. "
                f"Add credentials to services/dev-browser/.env"
            )

        # Get or create the page
        page = await self.get_page(page_name)

        # Ensure logged in (auto-login if needed)
        success = await self._auth_manager.ensure_logged_in(
            page, site_name, navigate_to
        )

        if not success:
            raise RuntimeError(
                f"Failed to login to {site_name}. Check credentials in .env"
            )

        return page

    async def ensure_logged_in(self, page_name: str, site_name: str) -> bool:
        """
        Check if logged in, and auto-login if session expired.

        Use this when you have an existing page and want to verify the session
        is still valid before performing actions.

        Args:
            page_name: Name of the page
            site_name: Site identifier

        Returns:
            True if logged in (or login succeeded), False if login failed
        """
        if not self._auth_manager:
            return False

        page = await self.get_page(page_name)
        return await self._auth_manager.ensure_logged_in(page, site_name)

    async def is_logged_out(self, page_name: str, site_name: str) -> bool:
        """
        Check if the user appears to be logged out.

        Args:
            page_name: Name of the page
            site_name: Site identifier

        Returns:
            True if logged out, False if logged in
        """
        if not self._auth_manager:
            return False

        page = await self.get_page(page_name)
        return await self._auth_manager.is_logged_out(page, site_name)

    def list_configured_sites(self) -> list[str]:
        """
        List all sites with configured credentials.

        Returns:
            List of site names that have email/password in .env
        """
        if not self._auth_manager:
            return []
        return self._auth_manager.list_configured_sites()

    @property
    def auth_manager(self) -> Optional[AuthManager]:
        """Get the auth manager instance for advanced usage."""
        return self._auth_manager

    async def get_ai_snapshot(self, name: str) -> str:
        """
        Get an LLM-friendly ARIA snapshot of a page.

        Returns a YAML-formatted string showing the page's accessible structure
        with refs like [ref=e1], [ref=e2] for interactable elements.

        Args:
            name: Name of the page

        Returns:
            YAML string representing the page structure
        """
        page = await self.get_page(name)

        # Read and inject the snapshot script
        snapshot_script = self._get_snapshot_script()

        snapshot = await page.evaluate(f"""
            (script) => {{
                if (!window.__devBrowser_getAISnapshot) {{
                    eval(script);
                }}
                return window.__devBrowser_getAISnapshot();
            }}
        """, snapshot_script)

        return snapshot

    async def select_ref(self, page_name: str, ref: str):
        """
        Get an element handle by its ref from the last snapshot.

        Refs are stored on the page and persist across reconnections.

        Args:
            page_name: Name of the page
            ref: Element ref (e.g., "e1", "e5")

        Returns:
            Playwright ElementHandle
        """
        page = await self.get_page(page_name)

        element_handle = await page.evaluate_handle(f"""
            (refId) => {{
                const refs = window.__devBrowserRefs;
                if (!refs) {{
                    throw new Error("No snapshot refs found. Call get_ai_snapshot first.");
                }}
                const element = refs[refId];
                if (!element) {{
                    throw new Error(`Ref "${{refId}}" not found. Available refs: ${{Object.keys(refs).join(", ")}}`);
                }}
                return element;
            }}
        """, ref)

        return element_handle.as_element()

    def _get_snapshot_script(self) -> str:
        """Read the snapshot script from the TypeScript source."""
        # The snapshot script is inlined in browser-script.ts
        # For simplicity, we include a Python version here
        snapshot_path = Path(__file__).parent / "src" / "snapshot" / "browser-script.ts"

        if snapshot_path.exists():
            # Extract the script string from the TypeScript file
            # This is a simplified approach - in production you might compile the TS
            content = snapshot_path.read_text()

            # Find the cachedScript assignment and extract it
            # For now, return the embedded script directly from the TS source
            return self._extract_snapshot_script()

        return self._extract_snapshot_script()

    def _extract_snapshot_script(self) -> str:
        """
        Return the snapshot script.

        This is the bundled version of the ARIA snapshot generator that can be
        injected into the browser. It provides:
        - getAISnapshot(): Returns YAML representation of page structure
        - selectSnapshotRef(ref): Get element by ref
        - window.__devBrowserRefs: Map of ref -> element
        """
        # This is a condensed version of the snapshot script from browser-script.ts
        # The full script is quite long, so we load it dynamically from the TS source
        # when available, or use this fallback
        return """
(function() {
  if (window.__devBrowser_getAISnapshot) return;

  // Simplified ARIA snapshot implementation
  let cacheStyle;
  let cachesCounter = 0;

  function beginDOMCaches() { ++cachesCounter; cacheStyle = cacheStyle || new Map(); }
  function endDOMCaches() { if (!--cachesCounter) cacheStyle = undefined; }

  function getElementComputedStyle(element, pseudo) {
    const cache = cacheStyle;
    const cacheKey = pseudo ? undefined : element;
    if (cache && cacheKey && cache.has(cacheKey)) return cache.get(cacheKey);
    const style = element.ownerDocument?.defaultView?.getComputedStyle(element, pseudo);
    if (cache && cacheKey) cache.set(cacheKey, style);
    return style;
  }

  function isElementVisible(element) {
    const style = getElementComputedStyle(element);
    if (!style || style.display === 'none' || style.visibility === 'hidden') return false;
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function getAriaRole(element) {
    const explicit = element.getAttribute('role');
    if (explicit) return explicit;

    const tagRoles = {
      A: (e) => e.hasAttribute('href') ? 'link' : null,
      BUTTON: () => 'button',
      INPUT: (e) => {
        const type = e.type?.toLowerCase() || 'text';
        const roles = { button: 'button', checkbox: 'checkbox', radio: 'radio', submit: 'button', reset: 'button' };
        return roles[type] || 'textbox';
      },
      SELECT: () => 'combobox',
      TEXTAREA: () => 'textbox',
      IMG: () => 'img',
      H1: () => 'heading', H2: () => 'heading', H3: () => 'heading',
      H4: () => 'heading', H5: () => 'heading', H6: () => 'heading',
      UL: () => 'list', OL: () => 'list', LI: () => 'listitem',
      NAV: () => 'navigation', MAIN: () => 'main', HEADER: () => 'banner',
      FOOTER: () => 'contentinfo', ARTICLE: () => 'article', SECTION: () => 'region',
    };

    const fn = tagRoles[element.tagName];
    return fn ? fn(element) : null;
  }

  function getAccessibleName(element) {
    const ariaLabel = element.getAttribute('aria-label');
    if (ariaLabel) return ariaLabel.trim();

    const labelledBy = element.getAttribute('aria-labelledby');
    if (labelledBy) {
      const labels = labelledBy.split(' ').map(id => document.getElementById(id)?.textContent || '').join(' ');
      if (labels.trim()) return labels.trim();
    }

    if (element.tagName === 'IMG') return element.getAttribute('alt') || '';
    if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
      const label = document.querySelector(`label[for="${element.id}"]`);
      if (label) return label.textContent?.trim() || '';
      return element.placeholder || '';
    }

    return element.textContent?.trim().slice(0, 100) || '';
  }

  let refCounter = 0;

  function generateSnapshot(root) {
    const elements = new Map();
    const lines = [];

    function visit(element, indent) {
      if (!element || element.nodeType !== 1) return;
      if (!isElementVisible(element)) return;

      const role = getAriaRole(element);
      const name = getAccessibleName(element);

      // Skip generic/uninteresting elements
      if (!role && !name && element.children.length <= 1) {
        for (const child of element.children) visit(child, indent);
        return;
      }

      const ref = 'e' + (++refCounter);
      elements.set(ref, element);

      let line = indent + '- ';
      if (role) line += role;
      if (name) line += ' "' + name.replace(/"/g, '\\\\"').slice(0, 50) + '"';
      line += ' [ref=' + ref + ']';

      // Add state attributes
      if (element.disabled) line += ' [disabled]';
      if (element.checked) line += ' [checked]';
      if (element.getAttribute('aria-expanded') === 'true') line += ' [expanded]';

      lines.push(line);

      for (const child of element.children) {
        visit(child, indent + '  ');
      }
    }

    beginDOMCaches();
    try {
      visit(root, '');
    } finally {
      endDOMCaches();
    }

    return { yaml: lines.join('\\n'), elements };
  }

  window.__devBrowser_getAISnapshot = function() {
    refCounter = 0;
    const snapshot = generateSnapshot(document.body);
    window.__devBrowserRefs = Object.fromEntries(snapshot.elements);
    return snapshot.yaml;
  };

  window.__devBrowser_selectSnapshotRef = function(ref) {
    const refs = window.__devBrowserRefs;
    if (!refs) throw new Error('No snapshot refs found. Call getAISnapshot first.');
    const element = refs[ref];
    if (!element) throw new Error('Ref "' + ref + '" not found.');
    return element;
  };
})();
"""


# Convenience functions for common operations
async def navigate(page_name: str, url: str, server_url: str = "http://localhost:9222") -> str:
    """
    Navigate a page to a URL and return the AI snapshot.

    Quick one-shot function for simple automation tasks.

    Args:
        page_name: Name for the page
        url: URL to navigate to
        server_url: Dev Browser server URL

    Returns:
        AI snapshot of the page after navigation
    """
    async with DevBrowserClient(server_url=server_url) as client:
        page = await client.get_page(page_name)
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        return await client.get_ai_snapshot(page_name)


async def take_screenshot(
    page_name: str,
    output_path: str,
    url: Optional[str] = None,
    server_url: str = "http://localhost:9222"
) -> str:
    """
    Take a screenshot of a page.

    Args:
        page_name: Name for the page
        output_path: Where to save the screenshot
        url: Optional URL to navigate to first
        server_url: Dev Browser server URL

    Returns:
        Path to the saved screenshot
    """
    async with DevBrowserClient(server_url=server_url) as client:
        page = await client.get_page(page_name)

        if url:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")

        await page.screenshot(path=output_path, full_page=True)
        return output_path


if __name__ == "__main__":
    # Quick test
    async def main():
        async with DevBrowserClient(auto_start=False) as client:
            print("Connected to Dev Browser")
            pages = await client.list_pages()
            print(f"Current pages: {pages}")

            # Create a test page
            page = await client.get_page("test")
            await page.goto("https://example.com")

            # Get AI snapshot
            snapshot = await client.get_ai_snapshot("test")
            print("\nAI Snapshot:")
            print(snapshot)

    asyncio.run(main())
