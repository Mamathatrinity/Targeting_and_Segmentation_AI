"""
UI Automation Agent - Execute UI Tests (NO LOOPS, NO RETRIES)

This agent executes predefined UI test steps.
AI is used for ANALYSIS only, NOT for execution decisions.

SAFE APPROACH:
- Execute test list once (no loops)
- If test fails → Continue to next test
- At end → Group failures by similarity
- Provide pattern-based recommendations
"""

import os
import json
import time
from typing import Dict, List, Any, Union
from playwright.sync_api import sync_playwright, Page
from ai_agent.langfuse_tracker import get_tracker
import yaml


# SAFETY LIMITS (NO LOOPS ALLOWED)
MAX_EXECUTION_TIME_MINUTES = 10  # Total execution time limit
ACTION_TIMEOUT_SECONDS = 10  # Individual action timeout


class UIAutomationAgent:
    """
    Execute UI tests from predefined test plan.
    NO LOOPS - Execute once, continue on failure, analyze at end.
    """
    
    def __init__(self):
        self.start_time = None
        self.results = []
    
    def execute_tests(
        self, 
        test_cases: Union[List[Dict], str], 
        base_url: str,
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Execute UI tests from predefined test plan.
        NO LOOPS - Execute each test once, continue on failure.
        
        Args:
            test_cases: List of test cases or YAML string
            base_url: Base URL for the application
            headless: Run browser in headless mode
            
        Returns:
            Execution results with failure grouping
        """
        self.start_time = time.time()
        self.results = []
        
        # Parse YAML if string provided
        if isinstance(test_cases, str):
            try:
                test_cases = yaml.safe_load(test_cases)
                if isinstance(test_cases, dict) and "test_cases" in test_cases:
                    test_cases = test_cases["test_cases"]
            except yaml.YAMLError as e:
                return {
                    "error": f"Invalid YAML: {str(e)}",
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                }
        
        summary = {
            "total_tests": len(test_cases),
            "passed": 0,
            "failed": 0,
            "execution_time_seconds": 0,
            "test_results": [],
            "failure_groups": []  # Group similar failures
        }
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            
            # Execute each test (NO LOOPS - single pass)
            for idx, test_case in enumerate(test_cases, 1):
                # Check timeout
                if self._is_timeout():
                    summary["test_results"].append({
                        "test_number": idx,
                        "name": test_case.get("name", f"Test {idx}"),
                        "status": "skipped",
                        "reason": f"Timeout: Exceeded {MAX_EXECUTION_TIME_MINUTES} minutes"
                    })
                    continue
                
                # Execute single test (NO RETRIES)
                result = self._execute_single_test(page, test_case, base_url, idx)
                summary["test_results"].append(result)
                
                if result["status"] == "passed":
                    summary["passed"] += 1
                else:
                    summary["failed"] += 1
                
                # Brief pause between tests
                time.sleep(0.5)
            
            browser.close()
        
        summary["execution_time_seconds"] = round(time.time() - self.start_time, 2)
        
        # Group failures by similarity
        summary["failure_groups"] = self._group_failures(summary["test_results"])
        
        # Flush tracker if enabled
        tracker = get_tracker()
        if tracker and tracker.enabled:
            tracker.flush()
        
        return summary
    
    def _execute_single_test(
        self, 
        page: Page, 
        test_case: Dict, 
        base_url: str,
        test_number: int
    ) -> Dict[str, Any]:
        """
        Execute a single test case (NO RETRIES).
        If any step fails, mark test as failed and continue.
        
        Returns:
            Test result with status and details
        """
        test_name = test_case.get("name", f"Test {test_number}")
        steps = test_case.get("steps", [])
        
        result = {
            "test_number": test_number,
            "name": test_name,
            "description": test_case.get("description", ""),
            "status": "passed",
            "steps_executed": 0,
            "steps_total": len(steps),
            "failure_reason": None,
            "failed_step": None,
            "error_type": None
        }
        
        try:
            for step_idx, step in enumerate(steps, 1):
                action = step.get("action")
                
                # Execute action (NO RETRIES - fail fast)
                try:
                    if action == "navigate":
                        url = step.get("url", "")
                        if not url.startswith("http"):
                            url = base_url.rstrip("/") + "/" + url.lstrip("/")
                        page.goto(url, timeout=ACTION_TIMEOUT_SECONDS * 1000)
                    
                    elif action == "fill":
                        selector = step.get("selector") or step.get("target")
                        value = step.get("value", "")
                        page.fill(selector, value, timeout=ACTION_TIMEOUT_SECONDS * 1000)
                    
                    elif action == "click":
                        selector = step.get("selector") or step.get("target")
                        page.click(selector, timeout=ACTION_TIMEOUT_SECONDS * 1000)
                    
                    elif action == "verify_text":
                        text = step.get("text") or step.get("value", "")
                        element = page.get_by_text(text, exact=False)
                        if not element.is_visible(timeout=ACTION_TIMEOUT_SECONDS * 1000):
                            raise Exception(f"Text not found: {text}")
                    
                    elif action == "wait":
                        seconds = min(step.get("seconds", 1), 5)
                        time.sleep(seconds)
                    
                    result["steps_executed"] += 1
                
                except Exception as step_error:
                    # Test failed - record details and STOP (no retry)
                    result["status"] = "failed"
                    result["failure_reason"] = str(step_error)
                    result["failed_step"] = step_idx
                    result["error_type"] = self._classify_error(str(step_error))
                    break  # Stop executing this test, move to next
        
        except Exception as e:
            result["status"] = "failed"
            result["failure_reason"] = str(e)
            result["error_type"] = "test_error"
        
        return result
    
    def _is_timeout(self) -> bool:
        """Check if total execution time exceeded."""
        elapsed = time.time() - self.start_time
        return elapsed > (MAX_EXECUTION_TIME_MINUTES * 60)
    
    def _classify_error(self, error_message: str) -> str:
        """
        Classify error type for grouping similar failures.
        
        Returns:
            Error category for grouping
        """
        error_lower = error_message.lower()
        
        if "timeout" in error_lower or "waiting" in error_lower:
            return "timeout"
        elif "not found" in error_lower or "no element" in error_lower:
            return "element_not_found"
        elif "selector" in error_lower:
            return "invalid_selector"
        elif "navigation" in error_lower or "net::" in error_lower:
            return "navigation_error"
        elif "text not found" in error_lower or "visible" in error_lower:
            return "assertion_failed"
        else:
            return "unknown_error"
    
    def _group_failures(self, test_results: List[Dict]) -> List[Dict]:
        """
        Group failed tests by similar error patterns.
        
        Returns:
            List of failure groups with recommendations
        """
        failures = [t for t in test_results if t["status"] == "failed"]
        
        if not failures:
            return []
        
        # Group by error type
        groups = {}
        for failure in failures:
            error_type = failure.get("error_type", "unknown")
            if error_type not in groups:
                groups[error_type] = {
                    "error_type": error_type,
                    "count": 0,
                    "failed_tests": [],
                    "recommendation": self._get_recommendation(error_type)
                }
            
            groups[error_type]["count"] += 1
            groups[error_type]["failed_tests"].append({
                "test_name": failure["name"],
                "test_number": failure["test_number"],
                "failure_reason": failure["failure_reason"]
            })
        
        # Convert to list and sort by count (most common failures first)
        failure_groups = sorted(
            groups.values(),
            key=lambda x: x["count"],
            reverse=True
        )
        
        return failure_groups
    
    def _get_recommendation(self, error_type: str) -> str:
        """Get fix recommendation based on error type."""
        recommendations = {
            "timeout": "Increase timeout values or add explicit waits before actions. Page may be slow to load.",
            "element_not_found": "Update selectors - elements may have changed. Use more stable selectors (id, data-testid).",
            "invalid_selector": "Fix CSS selectors - use browser DevTools to validate selectors work.",
            "navigation_error": "Check URL validity and network connectivity. Server may be down.",
            "assertion_failed": "Expected text may have changed. Update verification text or check page state.",
            "unknown_error": "Review error details and check test environment configuration."
        }
        return recommendations.get(error_type, "Review test case and error details.")
    


def execute_ui_tests(test_cases: Union[List[Dict], str], base_url: str) -> Dict[str, Any]:
    """
    Execute UI tests (NO LOOPS - single pass execution).
    
    Args:
        test_cases: List of test cases or YAML string
        base_url: Base URL for the application
        
    Returns:
        Execution results with failure grouping
    """
    agent = UIAutomationAgent()
    return agent.execute_tests(test_cases, base_url, headless=True)


if __name__ == "__main__":
    # Example usage
    example_tests = [
        {
            "name": "Login test",
            "description": "Test login functionality",
            "steps": [
                {"action": "navigate", "url": "/login"},
                {"action": "fill", "selector": "input[name='email']", "value": "test@example.com"},
                {"action": "fill", "selector": "input[name='password']", "value": "password123"},
                {"action": "click", "selector": "button[type='submit']"},
                {"action": "verify_text", "text": "Welcome"}
            ]
        }
    ]
    
    result = execute_ui_tests(example_tests, "https://example.com")
    print(json.dumps(result, indent=2))
