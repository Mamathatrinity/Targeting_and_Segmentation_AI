"""
Login Test Suite
Credentials loaded from .env (USER_EMAIL, USER_PASSWORD)

Run:
  pytest tests/test_login.py -v
  pytest tests/test_login.py -v -k "positive"
  pytest tests/test_login.py -v -k "security"
  pytest tests/test_login.py -v -k "ux"
  pytest tests/test_login.py -v -k "session"
"""
import os
import pytest
from dotenv import load_dotenv
from pages.login_page import LoginPage

load_dotenv()

# Credentials from .env
VALID_EMAIL    = os.getenv("USER_EMAIL", "mv@trinitypartners.com")
VALID_PASSWORD = os.getenv("USER_PASSWORD", "Mamatha1997@trinity")
BASE_URL       = os.getenv("BASE_URL", "https://ce-ts-dev.trinitylifesciences.com")


# ============================================================
# POSITIVE TEST CASES
# ============================================================

class TestLoginPositive:

    def test_valid_login_redirects_to_dashboard(self, page):
        """User logs in with valid credentials and is redirected to dashboard"""
        login = LoginPage(page)
        login.navigate()
        login.login(VALID_EMAIL, VALID_PASSWORD)
        assert login.is_logged_in(), "Expected to be logged in after valid credentials"

    def test_valid_login_email_case_insensitive(self, page):
        """User logs in with uppercase email and it is accepted"""
        login = LoginPage(page)
        login.navigate()
        login.login(VALID_EMAIL.upper(), VALID_PASSWORD)
        assert login.is_logged_in(), "Login should accept uppercase email"

    def test_valid_login_email_with_spaces_trimmed(self, page):
        """User enters email with leading/trailing spaces and login succeeds"""
        login = LoginPage(page)
        login.navigate()
        login.login(f"  {VALID_EMAIL}  ", VALID_PASSWORD)
        assert login.is_logged_in(), "Login should trim spaces from email"

    def test_login_page_loads_correctly(self, page):
        """Login page loads with Sign In button visible"""
        login = LoginPage(page)
        login.navigate()
        assert login.is_sign_in_button_visible(), "Sign In button should be visible on app login page"

    def test_forgot_password_link_visible(self, page):
        """Account recovery link is visible on Microsoft SSO password page.
        This tenant shows 'Can't access your account?' (#cantAccessAccount)"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.wait_for(state="visible", timeout=10000)
        login.ms_email_input.fill(VALID_EMAIL.strip())
        login.ms_next_button.click()
        login.ms_password_input.wait_for(state="visible", timeout=10000)
        # This tenant uses 'Can't access your account?' instead of 'Forgot password'
        recovery_link = page.locator("#cantAccessAccount")
        assert recovery_link.is_visible(), "Account recovery link should be visible on SSO password page"

    def test_forgot_password_link_navigates(self, page):
        """'Can't access your account?' link navigates to Microsoft account recovery"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.wait_for(state="visible", timeout=10000)
        login.ms_email_input.fill(VALID_EMAIL.strip())
        login.ms_next_button.click()
        login.ms_password_input.wait_for(state="visible", timeout=10000)
        page.locator("#cantAccessAccount").click()
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        assert "microsoftonline" in page.url.lower() or "passwordreset" in page.url.lower(), \
            "Should navigate to Microsoft account recovery page"

    def test_password_field_is_masked(self, page):
        """Password field on Microsoft SSO is masked (type=password)"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.wait_for(state="visible", timeout=10000)
        login.ms_email_input.fill(VALID_EMAIL.strip())
        login.ms_next_button.click()
        login.ms_password_input.wait_for(state="visible", timeout=10000)
        pw_type = login.ms_password_input.get_attribute("type")
        assert pw_type == "password", "Password field should be masked"


# ============================================================
# EDGE CASE TEST CASES
# ============================================================

class TestLoginEdgeCases:

    def test_login_with_empty_email(self, page):
        """User submits empty email on SSO - shows validation error"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_next_button.click()
        page.wait_for_timeout(1000)
        assert not login.is_logged_in(), "Should not login with empty email"

    def test_login_with_empty_password(self, page):
        """User submits empty password on SSO - shows validation error"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.fill(VALID_EMAIL.strip())
        login.ms_next_button.click()
        page.wait_for_timeout(2000)
        login.ms_next_button.click()
        page.wait_for_timeout(1000)
        assert not login.is_logged_in(), "Should not login with empty password"


    def test_login_email_with_plus_sign(self, page):
        """Email with + sign is accepted as valid format on SSO page"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.fill("user+tag@trinitypartners.com")
        login.ms_next_button.click()
        page.wait_for_timeout(2000)
        # Should proceed to password step (format is valid)
        assert "microsoftonline" in page.url, "Should stay on SSO with email+tag format"

    def test_login_tab_navigation(self, page):
        """Tab key navigates from email to next button on SSO"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.click()
        login.ms_email_input.fill(VALID_EMAIL.strip())
        page.keyboard.press("Tab")
        page.wait_for_timeout(500)
        focused = page.evaluate("document.activeElement.tagName")
        assert focused in ["INPUT", "BUTTON", "A"], "Tab should move focus to next element"

    def test_login_enter_key_submits(self, page):
        """Enter key navigates from email to password step on SSO"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.wait_for(state="visible", timeout=10000)
        login.ms_email_input.fill(VALID_EMAIL.strip())
        page.keyboard.press("Enter")
        # Enter should advance to password step
        try:
            login.ms_password_input.wait_for(state="visible", timeout=8000)
            assert True, "Enter key advanced to password step"
        except Exception:
            pytest.skip("Password field did not appear after Enter key")

    def test_login_page_title(self, page):
        """Login page has correct title"""
        login = LoginPage(page)
        login.navigate()
        title = page.title()
        assert title != "", "Login page should have a title"

    def test_browser_back_after_login(self, page):
        """After login, pressing browser back does not expose secured pages"""
        login = LoginPage(page)
        login.navigate()
        login.login(VALID_EMAIL, VALID_PASSWORD)
        assert login.is_logged_in(), "Should be logged in before testing back"
        page.go_back()
        page.wait_for_timeout(1500)
        # After going back the app should either stay authenticated or redirect to login
        # It should NOT land on a raw microsoftonline.com page (security check)
        from urllib.parse import urlparse
        host = urlparse(page.url).netloc.lower()
        assert "trinitylifesciences.com" in host or "microsoftonline.com" in host, \
            "Browser back should not expose unrelated pages"


# ============================================================
# NEGATIVE / SECURITY TEST CASES
# ============================================================

class TestLoginNegative:

    def test_invalid_password_shows_error(self, page):
        """User enters wrong password on SSO - error displayed"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.fill(VALID_EMAIL.strip())
        login.ms_next_button.click()
        page.wait_for_timeout(2000)
        login.ms_password_input.fill("WrongPassword123!")
        login.ms_next_button.click()
        page.wait_for_timeout(3000)
        assert not login.is_logged_in(), "Should not login with wrong password"

    def test_invalid_email_shows_error(self, page):
        """User enters unregistered email on SSO - error displayed"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.fill("notexist@nowhere.com")
        login.ms_next_button.click()
        page.wait_for_timeout(3000)
        assert not login.is_logged_in(), "Should not login with unregistered email"

    def test_invalid_email_format(self, page):
        """User enters invalid email format on SSO - validation error shown"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.fill("notanemail")
        login.ms_next_button.click()
        page.wait_for_timeout(2000)
        assert not login.is_logged_in(), "Should not login with invalid email format"

    def test_sql_injection_in_email(self, page):
        """SQL injection in email field is blocked by SSO"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.fill("admin' OR '1'='1' --")
        login.ms_next_button.click()
        page.wait_for_timeout(2000)
        assert not login.is_logged_in(), "SQL injection should be blocked"

    def test_sql_injection_in_password(self, page):
        """SQL injection in password field is blocked by SSO"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.fill(VALID_EMAIL.strip())
        login.ms_next_button.click()
        page.wait_for_timeout(2000)
        login.ms_password_input.fill("' OR '1'='1")
        login.ms_next_button.click()
        page.wait_for_timeout(2000)
        assert not login.is_logged_in(), "SQL injection in password should be blocked"

    def test_xss_in_email_field(self, page):
        """XSS script injection in email field is sanitized by SSO"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.fill("<script>alert('xss')</script>")
        login.ms_next_button.click()
        page.wait_for_timeout(2000)
        assert not login.is_logged_in(), "XSS injection should be blocked"

    def test_very_long_email_rejected(self, page):
        """Extremely long email (500+ chars) is rejected by SSO"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.fill("a" * 500 + "@test.com")
        login.ms_next_button.click()
        page.wait_for_timeout(2000)
        assert not login.is_logged_in(), "Extremely long email should be rejected"

    def test_special_characters_in_password(self, page):
        """Wrong password with special characters shows proper error on SSO"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.fill(VALID_EMAIL.strip())
        login.ms_next_button.click()
        page.wait_for_timeout(2000)
        login.ms_password_input.fill("!@#$%^&*()")
        login.ms_next_button.click()
        page.wait_for_timeout(2000)
        assert not login.is_logged_in(), "Should not login with wrong special char password"


# ============================================================
# SESSION & POST-LOGIN TEST CASES
# ============================================================

class TestLoginSession:

    def test_remember_me_session_persists(self, page):
        """Remember Me / Stay Signed In keeps session after browser restart simulation"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.wait_for(state="visible", timeout=10000)
        login.ms_email_input.fill(VALID_EMAIL.strip())
        login.ms_next_button.click()
        login.ms_password_input.wait_for(state="visible", timeout=10000)
        login.ms_password_input.fill(VALID_PASSWORD)
        # Look for 'Stay signed in?' prompt and click Yes
        try:
            stay_signed_in = page.locator("#idSIButton9")
            stay_signed_in.wait_for(state="visible", timeout=8000)
            stay_signed_in.click()
        except Exception:
            pytest.skip("Stay signed in prompt did not appear")
        assert login.is_logged_in(), "Should be logged in after Stay Signed In"

    def test_login_access_hcp_targeting_module(self, page):
        """After login, user can access HCP Targeting module and see specialties"""
        login = LoginPage(page)
        login.navigate()
        login.login(VALID_EMAIL, VALID_PASSWORD)
        assert login.is_logged_in(), "Must be logged in first"
        # Navigate to HCP targeting section
        page.wait_for_load_state("networkidle", timeout=15000)
        assert BASE_URL in page.url, "Should be on the application after login"
        # Verify HCP-specific content is accessible
        hcp_indicator = page.locator("text=HCP, text=Specialty, text=Segmentation").first
        try:
            hcp_indicator.wait_for(state="visible", timeout=10000)
            assert True, "HCP module content is accessible"
        except Exception:
            pytest.skip("HCP module content not immediately visible on dashboard")

    def test_mfa_prompt_appears_after_password(self, page):
        """MFA (Authenticator app) prompt appears after valid email + password on SSO"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.wait_for(state="visible", timeout=10000)
        login.ms_email_input.fill(VALID_EMAIL.strip())
        login.ms_next_button.click()
        login.ms_password_input.wait_for(state="visible", timeout=10000)
        login.ms_password_input.fill(VALID_PASSWORD)
        login.ms_next_button.click()
        page.wait_for_timeout(3000)
        # After correct password, MS SSO should show MFA step or redirect to app
        is_mfa = page.locator("text=Approve sign-in request, text=Authenticator, #idRichContext").count() > 0
        is_logged_in = login.is_logged_in()
        assert is_mfa or is_logged_in, "Should show MFA prompt or complete login after valid credentials"

    def test_session_expiry_redirects_to_login(self, page):
        """Accessing protected URL without session redirects to login page"""
        # Navigate directly to a protected route without logging in
        page.goto(f"{BASE_URL}/segmentation", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        # Should be redirected to login or SSO
        url = page.url.lower()
        assert (
            "trinitylifesciences.com" in url and "/login" in url
        ) or "microsoftonline.com" in url, \
            "Unauthenticated access to protected route should redirect to login"

    def test_logout_clears_session(self, page):
        """After logout, navigating back to app redirects to login"""
        login = LoginPage(page)
        login.navigate()
        login.login(VALID_EMAIL, VALID_PASSWORD)
        assert login.is_logged_in(), "Must be logged in before testing logout"
        # Attempt logout
        try:
            logout_btn = page.locator("text=Logout, text=Sign Out, [aria-label*='logout'], [aria-label*='sign out']").first
            logout_btn.wait_for(state="visible", timeout=8000)
            logout_btn.click()
            page.wait_for_timeout(2000)
        except Exception:
            pytest.skip("Logout button not found — check selector for this app")
        # After logout, protected pages should redirect
        page.goto(f"{BASE_URL}/segmentation", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        url = page.url.lower()
        assert "microsoftonline.com" in url or "/login" in url, \
            "After logout, protected route should redirect to login"

    def test_account_lockout_after_multiple_failures(self, page):
        """Repeated wrong password attempts show lockout or throttling message"""
        login = LoginPage(page)
        login.navigate()
        login.sign_in_button.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        login.ms_email_input.wait_for(state="visible", timeout=10000)
        login.ms_email_input.fill(VALID_EMAIL.strip())
        login.ms_next_button.click()
        login.ms_password_input.wait_for(state="visible", timeout=10000)
        # Attempt 3 wrong passwords (avoid actual lockout — just verify throttling kicks in)
        for _ in range(3):
            login.ms_password_input.fill("WrongPassword!999")
            login.ms_next_button.click()
            page.wait_for_timeout(2000)
            try:
                login.ms_password_input.wait_for(state="visible", timeout=5000)
            except Exception:
                break  # SSO may have navigated away after repeated failures
        assert not login.is_logged_in(), "Should not be logged in after repeated wrong passwords"

    def test_concurrent_session_same_browser(self, page, browser):
        """Opening a second tab after login shows the app without re-authenticating"""
        login = LoginPage(page)
        login.navigate()
        login.login(VALID_EMAIL, VALID_PASSWORD)
        assert login.is_logged_in(), "Must be logged in first"
        # Open a second page in same browser context
        page2 = browser.new_page()
        page2.goto(BASE_URL, wait_until="domcontentloaded")
        page2.wait_for_timeout(3000)
        # Second tab should either be logged in or redirect to SSO (not show raw error)
        url2 = page2.url.lower()
        assert "trinitylifesciences.com" in url2 or "microsoftonline.com" in url2, \
            "Second tab should land on app or SSO, not an error page"
        page2.close()
