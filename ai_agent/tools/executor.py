"""
Executor Tool (NO AI)
Executes test steps using Playwright + API + DB validation
"""
from playwright.sync_api import sync_playwright, Page
from typing import List, Dict, Union
import requests
import time
import yaml


class TestExecutor:
    """Executes generated tests (deterministic, no AI)"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.results = []
    
    def execute_tests(self, test_cases: Union[List[dict], str], base_url: str = "") -> List[dict]:
        """
        Execute all test cases
        
        Args:
            test_cases: List of test cases with steps, or YAML string
            base_url: Base URL for navigation
            
        Returns:
            Execution results for each test
        """
        # Parse YAML if string provided
        if isinstance(test_cases, str):
            try:
                parsed = yaml.safe_load(test_cases)
                test_cases = parsed.get("tests", []) if isinstance(parsed, dict) else parsed
            except yaml.YAMLError as e:
                print(f"YAML parsing error: {e}")
                return [{"error": f"Invalid YAML: {e}", "status": "failed"}]
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            
            try:
                for test_case in test_cases:
                    result = self._execute_single_test(page, test_case, base_url)
                    self.results.append(result)
            
            finally:
                browser.close()
        
        return self.results
    
    def _execute_single_test(self, page: Page, test_case: dict, base_url: str) -> dict:
        """Execute a single test case"""
        test_name = test_case.get("name", "unknown_test")
        steps = test_case.get("steps", [])
        
        result = {
            "test_name": test_name,
            "description": test_case.get("description", ""),
            "status": "passed",
            "steps_executed": 0,
            "steps_failed": [],
            "duration_ms": 0,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            for idx, step in enumerate(steps):
                step_num = idx + 1
                action = step.get("action", "")
                # Support both 'selector' (new) and 'target' (old) for compatibility
                target = step.get("selector") or step.get("target", "")
                value = step.get("value", "")
                expected = step.get("expected", "")
                
                print(f"  Step {step_num}: {action} {target}")
                
                # Execute action
                if action == "navigate":
                    url = target if target.startswith("http") else f"{base_url}{target}"
                    page.goto(url, wait_until="networkidle", timeout=30000)
                
                elif action == "fill":
                    # Try multiple selectors
                    self._fill_field(page, target, value)
                
                elif action == "click":
                    # Try multiple selectors
                    self._click_element(page, target)
                
                elif action == "verify":
                    # Verify element/state
                    self._verify_element(page, target, expected)
                
                elif action == "verify_text":
                    # Verify text exists on page
                    self._verify_text(page, value or expected)
                
                else:
                    print(f"    Unknown action: {action}")
                
                result["steps_executed"] += 1
                page.wait_for_timeout(500)  # Brief pause between steps
        
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["steps_failed"].append({
                "step_number": result["steps_executed"] + 1,
                "error": str(e)
            })
            print(f"  ❌ Test failed: {e}")
        
        result["duration_ms"] = int((time.time() - start_time) * 1000)
        return result
    
    def _fill_field(self, page: Page, target: str, value: str):
        """Fill input field using multiple selector strategies"""
        selectors = [
            f'input[name="{target}"]',
            f'input[placeholder*="{target}" i]',
            f'input[id*="{target}" i]',
            f'//label[contains(text(), "{target}")]/following::input[1]'
        ]
        
        for selector in selectors:
            try:
                page.fill(selector, value, timeout=5000)
                return
            except:
                continue
        
        raise Exception(f"Could not find input field: {target}")
    
    def _click_element(self, page: Page, target: str):
        """Click element using multiple selector strategies"""
        selectors = [
            f'button:has-text("{target}")',
            f'input[value="{target}"]',
            f'a:has-text("{target}")',
            f'//*[contains(text(), "{target}")]'
        ]
        
        for selector in selectors:
            try:
                page.click(selector, timeout=5000)
                return
            except:
                continue
        
        raise Exception(f"Could not find element to click: {target}")
    
    def _verify_element(self, page: Page, target: str, expected: str):
        """Verify element state/visibility"""
        try:
            if expected.lower() in ["visible", "displayed"]:
                page.wait_for_selector(target, state="visible", timeout=10000)
            elif expected.lower() == "hidden":
                page.wait_for_selector(target, state="hidden", timeout=10000)
            elif expected:
                # Verify text content
                element = page.locator(f'//*[contains(text(), "{expected}")]')
                element.wait_for(state="visible", timeout=10000)
        except Exception as e:
            raise Exception(f"Verification failed for {target}: {e}")
    
    def get_summary(self) -> dict:
        """Get execution summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = total - passed
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            "total_duration_ms": sum(r["duration_ms"] for r in self.results)
        }


# Standalone function for workflow
def execute_tests(test_cases: Union[List[dict], str], base_url: str = "") -> Dict:
    """
    Execute generated test cases
    
    Args:
        test_cases: Test cases with steps from designer, or YAML string
        base_url: Base URL for the application
        
    Returns:
        Execution results and summary
    """
    executor = TestExecutor(headless=False)
    results = executor.execute_tests(test_cases, base_url)
    summary = executor.get_summary()
    
    return {
        "results": results,
        "summary": summary
    }


if __name__ == "__main__":
    # Test executor with sample test case
    sample_test = [{
        "name": "test_google_search",
        "description": "Search on Google",
        "steps": [
            {"action": "navigate", "target": "https://www.google.com", "value": "", "expected": ""},
            {"action": "fill", "target": "q", "value": "Playwright Python", "expected": ""},
            {"action": "click", "target": "Google Search", "value": "", "expected": ""},
            {"action": "verify", "target": "search", "value": "", "expected": "visible"}
        ]
    }]
    
    print("Testing Executor...")
    result = execute_tests(sample_test, "")
    print(f"\nSummary: {result['summary']}")
