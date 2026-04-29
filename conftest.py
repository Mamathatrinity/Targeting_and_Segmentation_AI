"""
Pytest configuration file with fixtures for AI-powered testing.

Provides:
- Browser context and page fixtures
- AI agent fixtures (Planner, Designer, Executor, Validator)
- MCP client fixture for browser automation
- Session management and authentication
"""

import sys
import os
import json
import pytest
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, BrowserContext

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import AI agents and tools
from ai_agent.agents.planner import PlannerAgent
from ai_agent.agents.designer import DesignerAgent
from ai_agent.agents.validator import ValidatorAgent
from ai_agent.tools.ui_extractor import UIExtractor
from ai_agent.tools.executor import TestExecutor
from mcp_server.client import MCPClient

load_dotenv()

# Configuration
BASE_URL = os.getenv("BASE_URL", "https://your-app-url.com")
STORAGE_PATH = "storage_state.json"
SESSION_EXPIRY_SECONDS = 3600  # 1 hour


def is_storage_state_fresh(file_path: str, expiry_seconds: int) -> bool:
    """Check if storage state file is fresh (not expired)."""
    if not os.path.exists(file_path):
        return False
    import time
    return (time.time() - os.path.getmtime(file_path)) < expiry_seconds


# ============================================
# Browser Fixtures
# ============================================

@pytest.fixture(scope="session")
def playwright_instance():
    """Start Playwright instance for the session."""
    playwright = sync_playwright().start()
    yield playwright
    playwright.stop()


@pytest.fixture(scope="session")
def browser(playwright_instance):
    """Launch browser for the session."""
    browser = playwright_instance.chromium.launch(
        headless=False,
        slow_mo=100,   # 100ms: actions are visible but not artificially slow
        args=["--no-sandbox", "--disable-gpu", "--incognito", "--start-maximized"]
    )
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def page(browser) -> Page:
    """
    Fresh unauthenticated page per test — for login tests.
    Each test gets its own browser context starting from logged-out state.
    """
    context = browser.new_context(ignore_https_errors=True)
    pg = context.new_page()
    yield pg
    pg.close()
    context.close()


@pytest.fixture(scope="session")
def authenticated_page(browser) -> Page:
    """
    Authenticated page that reuses session across all tests.
    Login once with MFA, then all tests use the saved session.
    Use this for non-login tests to avoid MFA prompts.
    """
    # Check if we have a fresh saved session
    if is_storage_state_fresh(STORAGE_PATH, SESSION_EXPIRY_SECONDS):
        context = browser.new_context(storage_state=STORAGE_PATH, ignore_https_errors=True)
        pg = context.new_page()
        yield pg
        pg.close()
        context.close()
        return
    
    # No saved session - need to login with MFA once
    context = browser.new_context(ignore_https_errors=True)
    pg = context.new_page()
    
    # Perform login
    from pages.login_page import LoginPage
    login = LoginPage(pg)
    email = os.getenv("USER_EMAIL", "mv@trinitypartners.com")
    password = os.getenv("USER_PASSWORD", "Mamatha1997@trinity")
    login.login(email, password)
    
    # Save authenticated session
    context.storage_state(path=STORAGE_PATH)
    
    yield pg
    pg.close()
    context.close()


@pytest.fixture(scope="function")
def fresh_page(browser) -> Page:
    """Alias for page — completely fresh unauthenticated context per test."""
    context = browser.new_context(ignore_https_errors=True)
    pg = context.new_page()
    yield pg
    pg.close()
    context.close()


# ============================================
# MCP Client Fixture
# ============================================

@pytest.fixture(scope="session")
def mcp_client():
    """
    MCP client for browser automation.
    Connects to the MCP HTTP server running on port 8080.
    """
    client = MCPClient()
    yield client
    # Client cleanup handled by session end


# ============================================
# AI Agent Fixtures
# ============================================

@pytest.fixture(scope="session")
def planner_agent():
    """AI agent for generating test scenarios."""
    return PlannerAgent()


@pytest.fixture(scope="session")
def designer_agent():
    """AI agent for converting scenarios into executable test steps."""
    return DesignerAgent()


@pytest.fixture(scope="session")
def validator_agent():
    """AI agent for analyzing test results with root cause analysis."""
    return ValidatorAgent()


@pytest.fixture(scope="session")
def ui_extractor(mcp_client):
    """Tool for extracting UI elements via MCP."""
    return UIExtractor(mcp_client)


@pytest.fixture(scope="session")
def test_executor(mcp_client):
    """Tool for executing test steps via MCP."""
    return TestExecutor(mcp_client)


@pytest.fixture(scope="function")
def ai_test_framework(planner_agent, designer_agent, validator_agent, ui_extractor, test_executor):
    """
    Complete AI testing framework with all agents and tools.
    
    Returns dict with:
    - planner: PlannerAgent
    - designer: DesignerAgent
    - validator: ValidatorAgent
    - ui_extractor: UIExtractor
    - executor: TestExecutor
    """
    return {
        "planner": planner_agent,
        "designer": designer_agent,
        "validator": validator_agent,
        "ui_extractor": ui_extractor,
        "executor": test_executor
    }


# ============================================
# Screenshot on Failure
# ============================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to make test result available to fixtures."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request):
    """Automatically take screenshot on test failure."""
    yield

    if not (hasattr(request.node, "rep_call") and request.node.rep_call.failed):
        print(f"[PASS] Test {request.node.name} PASSED")
        return

    # Try to get the page fixture — only tests that use it will have it
    try:
        pg = request.getfixturevalue("page")
    except pytest.FixtureLookupError:
        try:
            pg = request.getfixturevalue("authenticated_page")
        except pytest.FixtureLookupError:
            return  # No page fixture — skip screenshot

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, f"{request.node.name}_{timestamp}.png")
    try:
        pg.screenshot(path=screenshot_path, full_page=True)
        print(f"[SCREENSHOT] Saved: {screenshot_path}")
    except Exception as e:
        print(f"[ERROR] Failed to take screenshot: {e}")


# ============================================
# Test Data Fixtures (Dynamic - No Static Files)
# ============================================

@pytest.fixture(scope="function")
def test_context():
    """
    Dynamic test context that AI agents can populate.
    
    Use this to store generated test data, scenarios, and results
    instead of static JSON files.
    """
    return {
        "scenarios": [],
        "test_steps": [],
        "results": [],
        "ui_elements": {}
    }
