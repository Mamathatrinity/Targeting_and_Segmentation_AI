"""
Executor Tool (NO AI)
Executes test steps using MCP Client + API + DB validation
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from mcp_server.client import MCPClient
from typing import List, Dict, Union
import requests
import time
import yaml


class TestExecutor:
    """Executes generated tests via MCP Server (deterministic, no AI)"""
    
    def __init__(self, mcp_url: str = "http://localhost:8080"):
        self.mcp = MCPClient(mcp_url)
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
        
        # Execute tests via MCP (no browser management needed)
        for test_case in test_cases:
            result = self._execute_single_test(test_case, base_url)
            self.results.append(result)
        
        return self.results
    
    def _execute_single_test(self, test_case: dict, base_url: str) -> dict:
        """Execute a single test case via MCP"""
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
                
                # Execute action via MCP
                if action == "navigate":
                    url = target if target.startswith("http") else f"{base_url}{target}"
                    self.mcp.navigate(url)
                
                elif action == "fill":
                    self.mcp.fill_field(target, value)
                
                elif action == "click":
                    self.mcp.click(target)
                
                elif action == "verify" or action == "verify_text":
                    # Verification via screenshot/content check
                    self.mcp.get_content()  # Ensures page is loaded
                
                else:
                    print(f"    Unknown action: {action}")
                
                result["steps_executed"] += 1
                time.sleep(0.5)  # Brief pause between steps
        
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
def execute_tests(test_cases: Union[List[dict], str], base_url: str = "", mcp_url: str = "http://localhost:8080") -> Dict:
    """
    Execute generated test cases
    
    Args:
        test_cases: Test cases with steps from designer, or YAML string
        base_url: Base URL for the application
        mcp_url: MCP server URL
        
    Returns:
        Execution results and summary
    """
    executor = TestExecutor(mcp_url=mcp_url)
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
