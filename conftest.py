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
        slow_mo=100,
        args=["--no-sandbox", "--disable-gpu"]
    )
    yield browser
    browser.close()


@pytest.fixture(scope="session")
def browser_context(browser):
    """
    Create browser context with saved authentication state if available.
    
    Note: This uses session-level context. For fresh context per test,
    use the 'fresh_page' fixture instead.
    """
    # Try to use existing storage state
    if os.path.exists(STORAGE_PATH) and is_storage_state_fresh(STORAGE_PATH, SESSION_EXPIRY_SECONDS):
        context = browser.new_context(storage_state=STORAGE_PATH)
        print(f"✅ Loaded existing session from {STORAGE_PATH}")
    else:
        context = browser.new_context()
        print("🔑 Creating new browser context (login may be required)")
    
    yield context
    
    # Save storage state for next session
    try:
        context.storage_state(path=STORAGE_PATH)
    except Exception as e:
        print(f"⚠️ Could not save storage state: {e}")
    
    context.close()


@pytest.fixture(scope="function")
def page(browser_context) -> Page:
    """
    Create a new page for each test function.
    Uses shared browser context (maintains login state).
    """
    page = browser_context.new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
    yield page
    page.close()


@pytest.fixture(scope="function")
def fresh_page(browser_context) -> Page:
    """
    Create a fresh page with cleared storage (for login/logout tests).
    """
    page = browser_context.new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded")
    
    try:
        # Clear storage for fresh state
        page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        browser_context.clear_cookies()
    except Exception as e:
        print(f"⚠️ Skipping storage clear: {e}")
    
    yield page
    page.close()


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
def screenshot_on_failure(request, page):
    """Automatically take screenshot on test failure."""
    yield
    
    test_name = request.node.name
    
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        # Test failed - take screenshot
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        screenshot_dir = "screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, f"{test_name}_{timestamp}.png")
        
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"❌ Failed to take screenshot: {e}")
    else:
        print(f"✅ Test {test_name} PASSED")


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
