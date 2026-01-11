"""
Auth Manager for Dev Browser

Handles credential storage and automatic re-login when sessions expire.
Credentials are loaded from the service's local .env file.

Usage:
    from auth_manager import AuthManager, SiteConfig

    auth = AuthManager()

    # Check if logged in, auto-login if not
    await auth.ensure_logged_in(client, "linkedin")
"""

import os
import re
import hmac
import struct
import time
import hashlib
import base64
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from dotenv import load_dotenv
from playwright.async_api import Page


# Load .env from this service's directory
SERVICE_DIR = Path(__file__).parent
load_dotenv(SERVICE_DIR / ".env")


@dataclass
class SiteConfig:
    """Configuration for a site's auto-login."""
    name: str
    email: str
    password: str
    login_url: str
    logged_out_indicators: list[str] = field(default_factory=list)
    email_selector: Optional[str] = None  # CSS selector or None for ARIA lookup
    password_selector: Optional[str] = None
    submit_selector: Optional[str] = None
    totp_secret: Optional[str] = None  # For 2FA
    post_login_wait: float = 3.0  # Seconds to wait after login


# Pre-configured sites with known login flows
KNOWN_SITES: dict[str, dict] = {
    "linkedin": {
        "login_url": "https://www.linkedin.com/login",
        "logged_out_indicators": ["sign in", "join now", "linkedin login"],
        "email_selector": "#username",
        "password_selector": "#password",
        "submit_selector": "button[type='submit']",
        "post_login_wait": 5.0,
    },
    "upwork": {
        "login_url": "https://www.upwork.com/ab/account-security/login",
        "logged_out_indicators": ["log in", "sign up", "work with the best"],
        "email_selector": "#login_username",
        "password_selector": "#login_password",
        "submit_selector": "#login_password_continue",
        "post_login_wait": 5.0,
    },
    "twitter": {
        "login_url": "https://twitter.com/i/flow/login",
        "logged_out_indicators": ["sign in", "log in", "create your account"],
        "email_selector": None,  # Dynamic, use ARIA
        "password_selector": None,
        "submit_selector": None,
        "post_login_wait": 5.0,
    },
    "google": {
        "login_url": "https://accounts.google.com/signin",
        "logged_out_indicators": ["sign in", "create account", "use your google account"],
        "email_selector": "input[type='email']",
        "password_selector": "input[type='password']",
        "submit_selector": None,  # Multi-step, handled specially
        "post_login_wait": 5.0,
    },
    "facebook": {
        "login_url": "https://www.facebook.com/login",
        "logged_out_indicators": ["log in", "create new account", "forgotten password"],
        "email_selector": "#email",
        "password_selector": "#pass",
        "submit_selector": "button[name='login']",
        "post_login_wait": 5.0,
    },
    "instagram": {
        "login_url": "https://www.instagram.com/accounts/login/",
        "logged_out_indicators": ["log in", "sign up", "don't have an account"],
        "email_selector": "input[name='username']",
        "password_selector": "input[name='password']",
        "submit_selector": "button[type='submit']",
        "post_login_wait": 5.0,
    },
    "github": {
        "login_url": "https://github.com/login",
        "logged_out_indicators": ["sign in", "create an account", "sign up"],
        "email_selector": "#login_field",
        "password_selector": "#password",
        "submit_selector": "input[type='submit']",
        "post_login_wait": 3.0,
    },
}


def generate_totp(secret: str) -> str:
    """
    Generate a TOTP code from a base32-encoded secret.

    Args:
        secret: Base32-encoded TOTP secret

    Returns:
        6-digit TOTP code
    """
    # Decode base32 secret
    key = base64.b32decode(secret.upper().replace(" ", ""))

    # Get current time step (30 second intervals)
    counter = int(time.time() // 30)

    # Pack counter as big-endian 64-bit integer
    counter_bytes = struct.pack(">Q", counter)

    # Calculate HMAC-SHA1
    hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()

    # Dynamic truncation
    offset = hmac_hash[-1] & 0x0F
    code_int = struct.unpack(">I", hmac_hash[offset:offset + 4])[0] & 0x7FFFFFFF

    # Get 6-digit code
    return str(code_int % 1000000).zfill(6)


class AuthManager:
    """
    Manages authentication for Dev Browser pages.

    Loads credentials from the service's .env file and handles
    automatic re-login when sessions expire.
    """

    def __init__(self):
        self.sites: dict[str, SiteConfig] = {}
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load credentials from environment variables."""
        # Load known sites
        for site_name, site_defaults in KNOWN_SITES.items():
            env_prefix = site_name.upper()
            email = os.getenv(f"{env_prefix}_EMAIL")
            password = os.getenv(f"{env_prefix}_PASSWORD")

            if email and password:
                self.sites[site_name] = SiteConfig(
                    name=site_name,
                    email=email,
                    password=password,
                    login_url=site_defaults["login_url"],
                    logged_out_indicators=site_defaults["logged_out_indicators"],
                    email_selector=site_defaults.get("email_selector"),
                    password_selector=site_defaults.get("password_selector"),
                    submit_selector=site_defaults.get("submit_selector"),
                    totp_secret=os.getenv(f"{env_prefix}_2FA_SECRET"),
                    post_login_wait=site_defaults.get("post_login_wait", 3.0),
                )

        # Load custom sites (scan for SITENAME_LOGIN_URL pattern)
        for key in os.environ:
            if key.endswith("_LOGIN_URL"):
                site_name = key.replace("_LOGIN_URL", "").lower()
                if site_name not in self.sites:
                    email = os.getenv(f"{site_name.upper()}_EMAIL")
                    password = os.getenv(f"{site_name.upper()}_PASSWORD")
                    login_url = os.getenv(key)
                    indicator = os.getenv(f"{site_name.upper()}_LOGGED_OUT_INDICATOR", "sign in")

                    if email and password and login_url:
                        self.sites[site_name] = SiteConfig(
                            name=site_name,
                            email=email,
                            password=password,
                            login_url=login_url,
                            logged_out_indicators=[indicator],
                            totp_secret=os.getenv(f"{site_name.upper()}_2FA_SECRET"),
                        )

    def get_site(self, site_name: str) -> Optional[SiteConfig]:
        """Get configuration for a site."""
        return self.sites.get(site_name.lower())

    def list_configured_sites(self) -> list[str]:
        """List all sites with configured credentials."""
        return list(self.sites.keys())

    async def is_logged_out(self, page: Page, site_name: str) -> bool:
        """
        Check if the user is logged out based on page content.

        Args:
            page: Playwright page
            site_name: Name of the site

        Returns:
            True if logged out, False if logged in
        """
        site = self.get_site(site_name)
        if not site:
            return False

        try:
            content = await page.content()
            content_lower = content.lower()

            for indicator in site.logged_out_indicators:
                if indicator.lower() in content_lower:
                    return True

            return False
        except Exception:
            return False

    async def login(self, page: Page, site_name: str) -> bool:
        """
        Perform login for a site.

        Args:
            page: Playwright page
            site_name: Name of the site

        Returns:
            True if login succeeded, False otherwise
        """
        site = self.get_site(site_name)
        if not site:
            raise ValueError(f"No credentials configured for site: {site_name}")

        try:
            # Navigate to login page
            await page.goto(site.login_url, wait_until="networkidle")
            await page.wait_for_timeout(1000)

            # Fill email
            if site.email_selector:
                await page.fill(site.email_selector, site.email)
            else:
                # Try common email field patterns
                email_filled = await self._fill_field_by_type(
                    page,
                    ["email", "username", "login"],
                    site.email
                )
                if not email_filled:
                    raise Exception("Could not find email field")

            # Fill password
            if site.password_selector:
                await page.fill(site.password_selector, site.password)
            else:
                password_filled = await self._fill_field_by_type(
                    page,
                    ["password"],
                    site.password
                )
                if not password_filled:
                    raise Exception("Could not find password field")

            # Submit form
            if site.submit_selector:
                await page.click(site.submit_selector)
            else:
                # Try pressing Enter or finding submit button
                await page.keyboard.press("Enter")

            # Wait for navigation
            await page.wait_for_timeout(int(site.post_login_wait * 1000))

            # Handle 2FA if configured
            if site.totp_secret:
                await self._handle_2fa(page, site)

            # Verify login succeeded
            if await self.is_logged_out(page, site_name):
                return False

            return True

        except Exception as e:
            print(f"Login failed for {site_name}: {e}")
            return False

    async def _fill_field_by_type(
        self,
        page: Page,
        field_types: list[str],
        value: str
    ) -> bool:
        """Try to fill a field by common patterns."""
        for field_type in field_types:
            selectors = [
                f"input[type='{field_type}']",
                f"input[name*='{field_type}']",
                f"input[id*='{field_type}']",
                f"input[placeholder*='{field_type}']",
            ]

            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=1000):
                        await element.fill(value)
                        return True
                except Exception:
                    continue

        return False

    async def _handle_2fa(self, page: Page, site: SiteConfig) -> None:
        """Handle 2FA if a TOTP secret is configured."""
        if not site.totp_secret:
            return

        try:
            # Wait for 2FA input to appear
            await page.wait_for_timeout(2000)

            # Generate TOTP code
            code = generate_totp(site.totp_secret)

            # Try to find 2FA input
            selectors = [
                "input[name*='code']",
                "input[name*='otp']",
                "input[name*='totp']",
                "input[name*='2fa']",
                "input[type='tel']",
                "input[autocomplete='one-time-code']",
            ]

            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=1000):
                        await element.fill(code)
                        await page.keyboard.press("Enter")
                        await page.wait_for_timeout(3000)
                        return
                except Exception:
                    continue

        except Exception as e:
            print(f"2FA handling failed: {e}")

    async def ensure_logged_in(
        self,
        page: Page,
        site_name: str,
        navigate_to: Optional[str] = None
    ) -> bool:
        """
        Ensure the user is logged in, performing login if necessary.

        This is the main method to use for auto-login functionality.

        Args:
            page: Playwright page
            site_name: Name of the site
            navigate_to: Optional URL to navigate to after ensuring login

        Returns:
            True if logged in (or login succeeded), False otherwise
        """
        site = self.get_site(site_name)
        if not site:
            raise ValueError(f"No credentials configured for site: {site_name}")

        # Check current state
        if await self.is_logged_out(page, site_name):
            print(f"Session expired for {site_name}, attempting re-login...")
            success = await self.login(page, site_name)
            if not success:
                return False
            print(f"Re-login successful for {site_name}")

        # Navigate to requested URL if provided
        if navigate_to:
            await page.goto(navigate_to, wait_until="networkidle")

            # Check again after navigation
            if await self.is_logged_out(page, site_name):
                print(f"Logged out after navigation, retrying login...")
                return await self.login(page, site_name)

        return True


# Singleton instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get the singleton AuthManager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
