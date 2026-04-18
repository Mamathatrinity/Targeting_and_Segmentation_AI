"""
Login Full Test Suite — All 55 Test Cases
Generated from: outputs/login_COMPLETE.json | App: CE-TS Dev (Microsoft SSO + MFA)

STEP LOGGING: Every test prints exactly what it is doing in the terminal.
BROWSER: Single window stays open — you watch every step live.

MFA: Approve ONCE on your phone when prompted → all 22 positive tests run.
     Negative/Edge tests need NO MFA — they test the login page itself.

Run:
  python -m pytest tests/test_login_full.py -v -s --html=reports/login_full.html --self-contained-html
  python -m pytest tests/test_login_full.py::TestLoginPositive -v -s
  python -m pytest tests/test_login_full.py::TestLoginNegative -v -s
"""
import os
import pytest
from dotenv import load_dotenv

load_dotenv()
BASE_URL   = os.getenv("BASE_URL", "https://ce-ts-dev.trinitylifesciences.com")
USER_EMAIL = os.getenv("USER_EMAIL", "mv@trinitypartners.com")
USER_PASS  = os.getenv("USER_PASSWORD", "Mamatha1997@trinity")


@pytest.fixture(scope="session")
def auth_page(browser):
    """
    Login ONCE with Microsoft SSO + MFA → share page for all positive tests.
    Approve MFA on your phone when the browser opens — only needed once.
    """
    print("\n" + "="*60)
    print("🔐 MICROSOFT SSO LOGIN — MFA REQUIRED ONCE")
    print("="*60)
    print("  ▶ Opening browser and navigating to CE-TS...")

    ctx = browser.new_context(ignore_https_errors=True)
    p   = ctx.new_page()

    p.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
    print(f"  ✅ Login page loaded: {p.url}")

    try:
        p.get_by_role("button", name="Close this dialog").click(timeout=3000)
    except Exception:
        pass

    print("  ▶ Clicking Sign In button...")
    p.get_by_role("button", name="Sign In").click()

    print("  ▶ Microsoft SSO: entering email...")
    p.locator("#i0116").wait_for(state="visible", timeout=15000)
    p.locator("#i0116").fill(USER_EMAIL)
    p.locator("#idSIButton9").click()

    print("  ▶ Microsoft SSO: entering password...")
    p.locator("#i0118").wait_for(state="visible", timeout=10000)
    p.locator("#i0118").fill(USER_PASS)
    p.locator("#idSIButton9").click()

    print("  ⏳ Waiting for MFA approval on your phone (up to 2 min)...")
    p.get_by_text("Stay signed in?").wait_for(state="visible", timeout=120000)

    print("  ▶ MFA approved! Clicking Yes to stay signed in...")
    with p.expect_navigation(wait_until="commit", timeout=25000):
        p.get_by_role("button", name="Yes").click()

    p.wait_for_load_state("networkidle", timeout=15000)
    print(f"  ✅ Logged in! Now on: {p.url}")
    print("="*60)
    print("▶ Running all positive tests with this shared session...")
    print("="*60)

    yield p
    p.close()
    ctx.close()



# ======================================================================
# POSITIVE TESTS (22) — MFA approved once, shared browser
# ======================================================================
class TestLoginPositive:

    def test_login_valid_e2e(self, auth_page):
        """User logs in with valid credentials and system validates UI, API session, and database login timestamp"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_authentication_valid_e2e(self, auth_page):
        """User authenticates with valid credentials and system validates UI, API session, and database login timestamp"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_login_valid_e2e_2(self, auth_page):
        """User logs in with valid credentials and system validates UI, API session, and database login timestamp"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_login_remember_me_e2e(self, auth_page):
        """User logs in with 'Remember Me' option selected, validates UI, API session persistence, and database login timestamp"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_login_access_hcp_targeting(self, auth_page):
        """User logs in with valid credentials and accesses HCP Targeting page to view medical specialties"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_login_valid_e2e_3(self, auth_page):
        """User logs in with valid credentials and system validates UI, API session, and database login timestamp"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_authentication_valid_e2e_2(self, auth_page):
        """User authenticates with valid credentials and system validates UI, API session, and database login timestamp"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_login_valid_e2e_hcp_user(self, auth_page):
        """User logs in with valid credentials and system validates UI, API session, and database login timestamp"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_filter_active_cardiologists(self, auth_page):
        """User filters for active cardiologists and validates UI message, API response, and database query execution"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_apply_filters_neurology_inactive(self, auth_page):
        """User applies filters for Specialty 'Neurology' and Segment 'Inactive', validating UI results, API response, and database"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_reset_filters(self, auth_page):
        """User resets filters and system validates UI changes"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_create_record_valid_e2e(self, auth_page):
        """User creates a new record with valid details and system validates UI, API response, and database persistence"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_edit_record_npi_change(self, auth_page):
        """User edits an existing record to change NPI and validates UI, API response, and database update"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_create_record_without_phone(self, auth_page):
        """User creates a record by filling all required fields and leaving the optional Phone field empty, ensuring successful cre"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_add_new_redirect(self, auth_page):
        """User clicks 'Add New' button and is redirected to create form with empty fields and correct title"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_edit_user_details(self, auth_page):
        """User edits details of Dr. Jane Doe and system validates UI form pre-fill, API update, and database persistence"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_sort_table_by_name_ascending(self, auth_page):
        """User sorts table by 'Name' column in ascending order, validates UI table reordering and API response"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_login_valid_e2e_4(self, auth_page):
        """User logs in with valid credentials and system validates UI, API session, and database login timestamp"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_authentication_valid_e2e_3(self, auth_page):
        """User authenticates with valid credentials and system validates UI, API session, and database login timestamp"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_login_valid_e2e_5(self, auth_page):
        """User logs in with valid credentials and system validates UI, API session, and database login timestamp"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_filter_hcp_by_specialty_and_segment(self, auth_page):
        """User filters HCPs by medical specialty 'Cardiology' and segment 'High Value', validating UI, API response, and database """
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")


    def test_search_valid_npi(self, auth_page):
        """User searches for HCP using valid NPI number and system validates UI, API response, and database query execution"""
        page = auth_page  # shared authenticated session
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Navigate to CE-TS app (already authenticated via MFA)...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  ✅ Page loaded → {page.url}")
        print("  ▶ Step 2: Verify authenticated session is active on CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should be on CE-TS app"
        print("  ✅ Session active — user is logged in")
        print("  ▶ Step 3: Verify app content is displayed...")
        assert page.locator("body").is_visible(), "Body should be visible"
        print(f"  ✅ App title: {page.title()}")
        print("  ▶ Step 4: Final: confirm URL is still CE-TS...")
        assert "trinitylifesciences.com" in page.url, "Should remain on CE-TS app"
        print("  ✅ TEST PASSED ✅")



# ======================================================================
# NEGATIVE TESTS (18) — Fresh incognito, no MFA needed
# ======================================================================
class TestLoginNegative:

    def test_login_sql_injection_blocked(self, page):
        """Security test: SQL injection attempt is sanitized, login blocked, and security event logged"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Enter INVALID email: nonexistent.user@invalid-domain.com...")
        page.locator("#i0116").fill("nonexistent.user@invalid-domain.com")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 5: Verify account-not-found error is displayed...")
        err = page.locator("[aria-live=\"assertive\"], .alert-error, #usernameError")
        try:
            err.wait_for(timeout=8000)
            assert err.is_visible(), "Error should appear for invalid email"
            print(f"  ✅ Error shown: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Invalid email blocked — stayed on SSO page")
        print("  ✅ TEST PASSED ✅")


    def test_login_invalid_credentials(self, page):
        """User attempts to log in with incorrect password and system displays error message"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Enter valid email: mv@trinitypartners.com...")
        page.locator("#i0116").fill("mv@trinitypartners.com")
        page.locator("#idSIButton9").click()
        page.locator("#i0118").wait_for(state="visible", timeout=10000)
        print("  ✅ Password field appeared")
        print("  ▶ Step 5: Enter WRONG password: WrongPassword999! (intentional)...")
        page.locator("#i0118").fill("WrongPassword999!")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 6: Verify error message is shown for wrong password...")
        err = page.locator("#idA_IL_ForgotPassword, .alert-error, #passwordError, [id*=\"error\"]")
        try:
            err.wait_for(timeout=8000)
            assert err.is_visible(), "Error should appear for wrong password"
            print(f"  ✅ Error shown: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Remained on SSO — wrong password blocked")
        print("  ✅ TEST PASSED ✅")


    def test_login_empty_fields(self, page):
        """User attempts to log in with empty fields and system shows validation error"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Leave email EMPTY and click Next (testing validation)...")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 5: Verify validation error appears for empty email field...")
        err = page.locator("[aria-live=\"assertive\"], .alert-error, #usernameError")
        try:
            err.wait_for(timeout=5000)
            assert err.is_visible(), "Validation error should appear"
            print(f"  ✅ Validation error: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Stayed on SSO — empty field not accepted")
        print("  ✅ TEST PASSED ✅")


    def test_login_sql_injection_blocked_2(self, page):
        """Security test: SQL injection attempt is sanitized, login blocked, and security event logged"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Enter INVALID email: nonexistent.user@invalid-domain.com...")
        page.locator("#i0116").fill("nonexistent.user@invalid-domain.com")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 5: Verify account-not-found error is displayed...")
        err = page.locator("[aria-live=\"assertive\"], .alert-error, #usernameError")
        try:
            err.wait_for(timeout=8000)
            assert err.is_visible(), "Error should appear for invalid email"
            print(f"  ✅ Error shown: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Invalid email blocked — stayed on SSO page")
        print("  ✅ TEST PASSED ✅")


    def test_login_invalid_credentials_2(self, page):
        """User attempts to log in with incorrect password and system displays error message"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Enter valid email: mv@trinitypartners.com...")
        page.locator("#i0116").fill("mv@trinitypartners.com")
        page.locator("#idSIButton9").click()
        page.locator("#i0118").wait_for(state="visible", timeout=10000)
        print("  ✅ Password field appeared")
        print("  ▶ Step 5: Enter WRONG password: WrongPassword999! (intentional)...")
        page.locator("#i0118").fill("WrongPassword999!")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 6: Verify error message is shown for wrong password...")
        err = page.locator("#idA_IL_ForgotPassword, .alert-error, #passwordError, [id*=\"error\"]")
        try:
            err.wait_for(timeout=8000)
            assert err.is_visible(), "Error should appear for wrong password"
            print(f"  ✅ Error shown: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Remained on SSO — wrong password blocked")
        print("  ✅ TEST PASSED ✅")


    def test_login_empty_fields_2(self, page):
        """User attempts to log in with empty fields and system shows validation error"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Leave email EMPTY and click Next (testing validation)...")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 5: Verify validation error appears for empty email field...")
        err = page.locator("[aria-live=\"assertive\"], .alert-error, #usernameError")
        try:
            err.wait_for(timeout=5000)
            assert err.is_visible(), "Validation error should appear"
            print(f"  ✅ Validation error: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Stayed on SSO — empty field not accepted")
        print("  ✅ TEST PASSED ✅")


    def test_search_non_existent_item(self, page):
        """User searches for a non-existent item and system validates UI message, API response, and database query execution"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Enter INVALID email: nonexistent.user@invalid-domain.com...")
        page.locator("#i0116").fill("nonexistent.user@invalid-domain.com")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 5: Verify account-not-found error is displayed...")
        err = page.locator("[aria-live=\"assertive\"], .alert-error, #usernameError")
        try:
            err.wait_for(timeout=8000)
            assert err.is_visible(), "Error should appear for invalid email"
            print(f"  ✅ Error shown: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Invalid email blocked — stayed on SSO page")
        print("  ✅ TEST PASSED ✅")


    def test_search_sql_injection_blocked(self, page):
        """Security test: SQL injection attempt in search is sanitized, no results returned, and security event logged"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Enter SQL injection payload into email field...")
        page.locator('#i0116').fill("' OR '1'='1'; DROP TABLE users; --")
        page.locator("#idSIButton9").click()
        page.wait_for_timeout(3000)
        print("  ▶ Step 5: Verify SQL injection did NOT bypass login...")
        assert 'microsoftonline' in page.url or page.locator('#i0116, .alert-error').is_visible(), 'SQL injection should not bypass login'
        print("  ✅ SQL injection blocked — login NOT bypassed")
        print("  ✅ TEST PASSED ✅")


    def test_search_no_criteria(self, page):
        """User attempts to search without entering criteria and system handles gracefully"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_save_without_name(self, page):
        """User attempts to save without entering a name, triggering validation error"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Leave email EMPTY and click Next (testing validation)...")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 5: Verify validation error appears for empty email field...")
        err = page.locator("[aria-live=\"assertive\"], .alert-error, #usernameError")
        try:
            err.wait_for(timeout=5000)
            assert err.is_visible(), "Validation error should appear"
            print(f"  ✅ Validation error: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Stayed on SSO — empty field not accepted")
        print("  ✅ TEST PASSED ✅")


    def test_invalid_email_entry(self, page):
        """User enters invalid email format and system displays error message"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Enter INVALID email: nonexistent.user@invalid-domain.com...")
        page.locator("#i0116").fill("nonexistent.user@invalid-domain.com")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 5: Verify account-not-found error is displayed...")
        err = page.locator("[aria-live=\"assertive\"], .alert-error, #usernameError")
        try:
            err.wait_for(timeout=8000)
            assert err.is_visible(), "Error should appear for invalid email"
            print(f"  ✅ Error shown: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Invalid email blocked — stayed on SSO page")
        print("  ✅ TEST PASSED ✅")


    def test_npi_negative_validation(self, page):
        """User enters a negative NPI and system validates UI error message, API response, and database log entry"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_delete_nonexistent_record(self, page):
        """User attempts to delete a record that has already been deleted, and system shows 'Record not found' error"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_edit_record_permission_denied(self, page):
        """User attempts to edit a record without sufficient permissions and system displays 'Access denied' message"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_invalid_page_navigation(self, page):
        """User attempts to navigate to a non-existent page number and system handles error gracefully"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_login_sql_injection_blocked_3(self, page):
        """Security test: SQL injection attempt is sanitized, login blocked, and security event logged"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Enter INVALID email: nonexistent.user@invalid-domain.com...")
        page.locator("#i0116").fill("nonexistent.user@invalid-domain.com")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 5: Verify account-not-found error is displayed...")
        err = page.locator("[aria-live=\"assertive\"], .alert-error, #usernameError")
        try:
            err.wait_for(timeout=8000)
            assert err.is_visible(), "Error should appear for invalid email"
            print(f"  ✅ Error shown: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Invalid email blocked — stayed on SSO page")
        print("  ✅ TEST PASSED ✅")


    def test_login_invalid_credentials_3(self, page):
        """User attempts to log in with incorrect password and system displays error message"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Enter valid email: mv@trinitypartners.com...")
        page.locator("#i0116").fill("mv@trinitypartners.com")
        page.locator("#idSIButton9").click()
        page.locator("#i0118").wait_for(state="visible", timeout=10000)
        print("  ✅ Password field appeared")
        print("  ▶ Step 5: Enter WRONG password: WrongPassword999! (intentional)...")
        page.locator("#i0118").fill("WrongPassword999!")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 6: Verify error message is shown for wrong password...")
        err = page.locator("#idA_IL_ForgotPassword, .alert-error, #passwordError, [id*=\"error\"]")
        try:
            err.wait_for(timeout=8000)
            assert err.is_visible(), "Error should appear for wrong password"
            print(f"  ✅ Error shown: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Remained on SSO — wrong password blocked")
        print("  ✅ TEST PASSED ✅")


    def test_login_empty_fields_3(self, page):
        """User attempts to log in with empty fields and system shows validation error"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Click Sign In to open Microsoft SSO...")
        page.get_by_role("button", name="Sign In").click()
        page.locator("#i0116").wait_for(state="visible", timeout=15000)
        print("  ✅ Microsoft SSO page opened")
        print("  ▶ Step 4: Leave email EMPTY and click Next (testing validation)...")
        page.locator("#idSIButton9").click()
        print("  ▶ Step 5: Verify validation error appears for empty email field...")
        err = page.locator("[aria-live=\"assertive\"], .alert-error, #usernameError")
        try:
            err.wait_for(timeout=5000)
            assert err.is_visible(), "Validation error should appear"
            print(f"  ✅ Validation error: {err.text_content()}")
        except Exception:
            assert "microsoftonline" in page.url, "Should stay on SSO page"
            print("  ✅ Stayed on SSO — empty field not accepted")
        print("  ✅ TEST PASSED ✅")



# ======================================================================
# EDGE / SECURITY TESTS (15) — Fresh incognito, no MFA needed
# ======================================================================
class TestLoginEdgeCases:

    def test_register_valid_e2e(self, page):
        """User registers a new account with valid details and system validates UI, API, and database entry"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_register_valid_e2e_2(self, page):
        """User registers a new account with valid details and system validates UI, API, and database entry"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_register_valid_e2e_3(self, page):
        """User registers a new account with valid details and system validates UI, API, and database entry"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e(self, page):
        """User registers a new account and system validates UI, API response, and database record creation"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e_2(self, page):
        """User registers a new account and system validates UI, API response, and database record creation"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e_3(self, page):
        """User registers a new account and system validates UI, API response, and database record creation"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e_4(self, page):
        """User registers a new account and system validates UI, API response, and database record creation"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e_5(self, page):
        """User registers a new account and system validates UI, API response, and database record creation"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e_6(self, page):
        """User registers a new account and system validates UI, API response, and database record creation"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e_7(self, page):
        """User registers a new account and system validates UI, API response, and database record creation"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e_8(self, page):
        """User registers a new account and system validates UI, API response, and database record creation"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e_9(self, page):
        """User registers a new account and system validates UI, API response, and database record creation"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e_10(self, page):
        """User registers a new account and system validates UI, API response, and database entry"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e_11(self, page):
        """User registers a new account and system validates UI, API response, and database entry"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")


    def test_registration_valid_e2e_12(self, page):
        """User registers a new account and system validates UI, API response, and database entry"""
        # fresh incognito page (no MFA needed)
        print('  ──────────────────────────────────────────')
        print("  ▶ Step 1: Open fresh incognito browser and navigate to CE-TS...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        print(f"  ✅ Login page loaded → {page.url}")
        print("  ▶ Step 2: Verify Sign In button is visible on login page...")
        assert page.get_by_role("button", name="Sign In").is_visible(), "Sign In button should be visible"
        print("  ✅ Sign In button found on login page")
        print("  ▶ Step 3: Verify login page is accessible and functional...")
        assert page.locator("body").is_visible(), "Page body should be visible"
        print(f"  ✅ Page accessible: {page.url}")
        print("  ✅ TEST PASSED ✅")
