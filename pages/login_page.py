"""
Login Page Object Model
Handles Microsoft SSO (Azure AD) login flow for the application
"""
import os
from playwright.sync_api import Page


class LoginPage:
    
    APP_URL   = os.getenv("BASE_URL", "https://ce-ts-dev.trinitylifesciences.com").rstrip("/")
    LOGIN_URL = APP_URL + "/login"

    def __init__(self, page: Page):
        self.page = page
        # App login page
        self.sign_in_button   = page.get_by_role("button", name="Sign In")
        self.cookie_close_btn = page.get_by_role("button", name="Close this dialog")
        # Microsoft SSO page (redirected after clicking Sign In)
        self.ms_email_input   = page.locator("#i0116")           # name="loginfmt"
        self.ms_next_button   = page.locator("#idSIButton9")     # Next / Sign in button
        self.ms_password_input = page.locator("#i0118")          # name="passwd"
        self.ms_error_message = page.locator("#idA_IL_ForgotPassword, .alert-error, [id*='error']")

    def navigate(self):
        """Go to app login page and dismiss cookie banner if present"""
        self.page.goto(self.APP_URL, wait_until="domcontentloaded", timeout=30000)
        try:
            self.cookie_close_btn.click(timeout=3000)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def login(self, email: str, password: str, skip_mfa_wait: bool = False):
        """
        Full login flow: App → Sign In button → Microsoft SSO → MFA → Dashboard
        
        Args:
            skip_mfa_wait: If True, skip MFA waiting (for agent-based execution)
        """
        self.navigate()
        # Click Sign In to go to Microsoft SSO
        self.sign_in_button.click()
        # Wait for MS email input to appear (SSO page loaded)
        self.ms_email_input.wait_for(state="visible", timeout=15000)
        # Fill Microsoft email
        self.ms_email_input.fill(email.strip())
        self.ms_next_button.click()
        # Wait for password field
        self.ms_password_input.wait_for(state="visible", timeout=10000)
        # Fill Microsoft password
        self.ms_password_input.fill(password)
        self.ms_next_button.click()
        
        if skip_mfa_wait:
            # Agent mode: Try to proceed quickly without MFA wait
            try:
                self.page.get_by_text("Stay signed in?").wait_for(state="visible", timeout=5000)
                with self.page.expect_navigation(wait_until="commit", timeout=5000):
                    self.page.get_by_role("button", name="Yes").click()
            except Exception:
                return
        else:
            # Normal mode: Wait for MFA approval then 'Stay signed in?' prompt.
            # Azure AD sometimes skips the prompt if MFA session is cached — handle both paths.
            try:
                self.page.get_by_text("Stay signed in?").wait_for(state="visible", timeout=120000)
                with self.page.expect_navigation(wait_until="commit", timeout=25000):
                    self.page.get_by_role("button", name="Yes").click()
            except Exception:
                # Prompt didn't appear — either already redirected to app or MFA skipped
                pass
        
        # Small pause for SPA client-side redirects to settle (code → # → / → /universe-summary)
        self.page.wait_for_timeout(1500)

    def is_logged_in(self) -> bool:
        """Check if we're back on the app by inspecting the hostname only (not full URL).
        The SSO callback URL contains microsoftonline.com in query params, so we must
        check the hostname/netloc rather than the full URL string."""
        from urllib.parse import urlparse
        host = urlparse(self.page.url).netloc.lower()
        return "trinitylifesciences.com" in host

    def is_on_dashboard(self) -> bool:
        try:
            self.page.wait_for_url("**/dashboard**", timeout=10000)
            return True
        except Exception:
            return self.is_logged_in()

    def get_error_message(self) -> str:
        try:
            self.ms_error_message.wait_for(timeout=3000)
            return self.ms_error_message.text_content() or ""
        except Exception:
            return ""

    def is_sign_in_button_visible(self) -> bool:
        try:
            self.sign_in_button.wait_for(timeout=5000)
            return self.sign_in_button.is_visible()
        except Exception:
            return False
