"""
API Testing Agent - Execute API Tests (NO LOOPS, NO RETRIES)

This agent executes predefined API test cases.
NO LOOPS - Execute once, continue on failure, group failures at end.
"""

import os
import json
import time
from typing import Dict, List, Any, Union
import requests
from ai_agent.langfuse_tracker import tracker
import yaml


# SAFETY LIMITS
MAX_EXECUTION_TIME_MINUTES = 10
REQUEST_TIMEOUT_SECONDS = 30


class APITestingAgent:
    """
    Execute API tests from predefined test plan.
    NO LOOPS - Execute once, continue on failure, analyze at end.
    """
    
    def __init__(self):
        self.start_time = None
        self.session = requests.Session()
    
    def execute_tests(
        self,
        test_cases: Union[List[Dict], str],
        base_url: str
    ) -> Dict[str, Any]:
        """
        Execute API tests (NO LOOPS - single pass).
        
        Args:
            test_cases: List of API test cases or YAML string
            base_url: Base API URL
            
        Returns:
            Execution results with failure grouping
        """
        self.start_time = time.time()
        
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
            "failure_groups": []
        }
        
        with tracker.trace_agent("api_testing_agent"):
            # Execute each test (NO LOOPS - single pass)
            for idx, test_case in enumerate(test_cases, 1):
                # Check timeout
                if self._is_timeout():
                    summary["test_results"].append({
                        "test_number": idx,
                        "name": test_case.get("name", f"API Test {idx}"),
                        "status": "skipped",
                        "reason": f"Timeout: Exceeded {MAX_EXECUTION_TIME_MINUTES} minutes"
                    })
                    continue
                
                # Execute single test (NO RETRIES)
                result = self._execute_single_test(test_case, base_url, idx)
                summary["test_results"].append(result)
                
                if result["status"] == "passed":
                    summary["passed"] += 1
                else:
                    summary["failed"] += 1
        
        summary["execution_time_seconds"] = round(time.time() - self.start_time, 2)
        summary["failure_groups"] = self._group_failures(summary["test_results"])
        
        tracker.flush()
        return summary
    
    def _execute_single_test(
        self,
        test_case: Dict,
        base_url: str,
        test_number: int
    ) -> Dict[str, Any]:
        """
        Execute single API test (NO RETRIES).
        If validation fails, mark as failed and continue.
        """
        test_name = test_case.get("name", f"API Test {test_number}")
        
        result = {
            "test_number": test_number,
            "name": test_name,
            "description": test_case.get("description", ""),
            "status": "passed",
            "failure_reason": None,
            "error_type": None,
            "response_time_ms": 0,
            "status_code": None
        }
        
        try:
            # Build request
            method = test_case.get("method", "GET").upper()
            endpoint = test_case.get("endpoint", "/")
            if not endpoint.startswith("http"):
                url = base_url.rstrip("/") + "/" + endpoint.lstrip("/")
            else:
                url = endpoint
            
            headers = test_case.get("headers", {})
            body = test_case.get("body", None)
            expected_status = test_case.get("expected_status", 200)
            
            # Execute request
            start = time.time()
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=body if isinstance(body, dict) else None,
                data=body if isinstance(body, str) else None,
                timeout=REQUEST_TIMEOUT_SECONDS
            )
            result["response_time_ms"] = round((time.time() - start) * 1000, 2)
            result["status_code"] = response.status_code
            
            # Validate status code
            if response.status_code != expected_status:
                result["status"] = "failed"
                result["failure_reason"] = f"Expected status {expected_status}, got {response.status_code}"
                result["error_type"] = "status_mismatch"
                return result
            
            # Validate response body if specified
            expected_body = test_case.get("expected_body", None)
            if expected_body:
                try:
                    response_json = response.json()
                    if isinstance(expected_body, dict):
                        for key, value in expected_body.items():
                            if key not in response_json or response_json[key] != value:
                                result["status"] = "failed"
                                result["failure_reason"] = f"Response body mismatch: {key} = {response_json.get(key)} (expected {value})"
                                result["error_type"] = "body_mismatch"
                                return result
                except json.JSONDecodeError:
                    result["status"] = "failed"
                    result["failure_reason"] = "Invalid JSON response"
                    result["error_type"] = "invalid_json"
                    return result
            
        except requests.Timeout:
            result["status"] = "failed"
            result["failure_reason"] = f"Request timeout after {REQUEST_TIMEOUT_SECONDS}s"
            result["error_type"] = "timeout"
        except requests.ConnectionError as e:
            result["status"] = "failed"
            result["failure_reason"] = f"Connection error: {str(e)}"
            result["error_type"] = "connection_error"
        except Exception as e:
            result["status"] = "failed"
            result["failure_reason"] = str(e)
            result["error_type"] = "unknown_error"
        
        return result
    
    def _is_timeout(self) -> bool:
        """Check if total execution time exceeded."""
        elapsed = time.time() - self.start_time
        return elapsed > (MAX_EXECUTION_TIME_MINUTES * 60)
    
    def _group_failures(self, test_results: List[Dict]) -> List[Dict]:
        """Group failed tests by similar error patterns."""
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
                "failure_reason": failure["failure_reason"],
                "status_code": failure.get("status_code")
            })
        
        # Sort by count (most common first)
        failure_groups = sorted(
            groups.values(),
            key=lambda x: x["count"],
            reverse=True
        )
        
        return failure_groups
    
    def _get_recommendation(self, error_type: str) -> str:
        """Get fix recommendation based on error type."""
        recommendations = {
            "status_mismatch": "Check API implementation - expected status code doesn't match actual. Verify endpoint logic.",
            "body_mismatch": "Response body structure changed. Update test expectations or fix API response format.",
            "timeout": "API response is slow. Optimize API performance or increase timeout value.",
            "connection_error": "Cannot connect to API server. Check base URL and server availability.",
            "invalid_json": "API returning non-JSON response. Check content-type and response format.",
            "unknown_error": "Review error details and test configuration."
        }
        return recommendations.get(error_type, "Review test case and error details.")


def execute_api_tests(test_cases: Union[List[Dict], str], base_url: str) -> Dict[str, Any]:
    """
    Execute API tests (NO LOOPS - single pass execution).
    
    Args:
        test_cases: List of API test cases or YAML string
        base_url: Base API URL
        
    Returns:
        Execution results with failure grouping
    """
    agent = APITestingAgent()
    return agent.execute_tests(test_cases, base_url)


if __name__ == "__main__":
    # Example usage
    example_tests = [
        {
            "name": "Get users endpoint",
            "description": "Test GET /api/users returns 200",
            "method": "GET",
            "endpoint": "/api/users",
            "expected_status": 200
        },
        {
            "name": "Create user",
            "description": "Test POST /api/users creates user",
            "method": "POST",
            "endpoint": "/api/users",
            "headers": {"Content-Type": "application/json"},
            "body": {"name": "Test User", "email": "test@example.com"},
            "expected_status": 201
        }
    ]
    
    result = execute_api_tests(example_tests, "https://api.example.com")
    print(json.dumps(result, indent=2))
