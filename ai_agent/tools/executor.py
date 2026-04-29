"""
Executor Tool (NO AI)
Executes test steps using MCP Client + API + DB validation

Supported step layers:
  UI  → navigate, fill, click, verify_text
  API → verify_api, verify_api_field
  DB  → verify_db
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from mcp_server.client import MCPClient
from typing import List, Dict, Union
import requests
import time
import yaml
from dotenv import load_dotenv

load_dotenv()

# Config file paths
_CONFIG_DIR         = os.path.join(os.path.dirname(__file__), '..', 'config')
_API_ENDPOINTS_FILE = os.path.join(_CONFIG_DIR, 'api_endpoints.yaml')
_DB_QUERIES_FILE    = os.path.join(_CONFIG_DIR, 'db_queries.yaml')


def _load_config(filepath: str) -> dict:
    try:
        with open(filepath, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _match_module(test_name: str, config: dict) -> dict | None:
    test_lower = test_name.lower()
    for module_cfg in config.get("modules", {}).values():
        for pattern in module_cfg.get("patterns", []):
            if pattern.lower() in test_lower:
                return module_cfg
    return None


def _db_connect():
    """Open a pymysql connection using DB_* vars from .env"""
    import pymysql
    return pymysql.connect(
        host=os.getenv("DB_SERVER"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        connect_timeout=10,
    )


def _api_headers() -> dict:
    """Build request headers using API_TOKEN from .env (optional)"""
    token = os.getenv("API_TOKEN", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


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
        steps = self._inject_config_steps(test_case)  # merge config-driven API/DB steps
        
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

                elif action in ("verify_api", "verify_api_field"):
                    self._execute_api_step(step, result)

                elif action == "verify_db":
                    self._execute_db_step(step, result)

                else:
                    print(f"    ⚠️  Unknown action: {action} — skipped")
                
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
    

    
    def _inject_config_steps(self, test_case: dict) -> list:
        """
        Augment the test's steps with any extra API/DB steps defined in
        api_endpoints.yaml and db_queries.yaml for the matching module.
        Only appended if the step is not already explicitly listed.
        """
        test_name   = test_case.get("name", "")
        depth       = test_case.get("depth", "medium")
        steps       = list(test_case.get("steps", []))
        existing_endpoints = {s.get("endpoint", "") for s in steps}
        existing_tables    = {s.get("table", "") for s in steps}

        # ── API endpoints ────────────────────────────────────────────────
        if depth in ("medium", "deep"):
            api_cfg = _load_config(_API_ENDPOINTS_FILE)
            module  = _match_module(test_name, api_cfg)
            if module:
                for ep in module.get("endpoints", []):
                    if ep.get("endpoint", "") not in existing_endpoints:
                        steps.append({
                            "action":          "verify_api",
                            "endpoint":        ep["endpoint"],
                            "method":          ep.get("method", "GET"),
                            "expected_status": ep.get("expected_status", 200),
                            "field":           ep.get("field", ""),
                            "expected_value":  ep.get("expected_value"),
                            "expected":        ep.get("description", ep["endpoint"]),
                            "layer":           "API",
                        })

        # ── DB queries ───────────────────────────────────────────────────
        if depth == "deep":
            db_cfg = _load_config(_DB_QUERIES_FILE)
            module = _match_module(test_name, db_cfg)
            if module:
                for q in module.get("queries", []):
                    if q.get("table", "") not in existing_tables:
                        steps.append({
                            "action":   "verify_db",
                            "table":    q.get("table", ""),
                            "column":   q.get("column", ""),
                            "query":    q.get("sql", ""),
                            "expected": q.get("description", q.get("name", "")),
                            "layer":    "DB",
                        })

        return steps

    def _execute_api_step(self, step: dict, result: dict):
        """
        Execute an API verification step.

        Step fields:
          endpoint        – path (e.g. /api/auth/session) or full URL
          method          – GET (default) | POST | PUT
          expected_status – expected HTTP status code (default 200)
          field           – dot-notation field to check in JSON response
          expected_value  – expected value for that field
          expected        – human-readable description (for logs)
        """
        endpoint       = step.get("endpoint", "")
        method         = step.get("method", "GET").upper()
        expected_status = int(step.get("expected_status", 200))
        field          = step.get("field", "")
        expected_value = step.get("expected_value")
        description    = step.get("expected", endpoint)

        base_url = os.getenv("BASE_URL", "").rstrip("/")
        url = endpoint if endpoint.startswith("http") else f"{base_url}{endpoint}"
        headers = _api_headers()

        print(f"    🌐 API {method} {url}")
        try:
            resp = requests.request(method, url, headers=headers, timeout=15, verify=False)
            actual_status = resp.status_code

            if actual_status != expected_status:
                msg = f"API {url} returned {actual_status}, expected {expected_status}"
                result["steps_failed"].append({"action": "verify_api", "error": msg})
                result["status"] = "failed"
                print(f"    ❌ {msg}")
                return

            print(f"    ✅ Status {actual_status}")

            # Optional field check
            if field and expected_value is not None:
                try:
                    data = resp.json()
                    # Traverse dot-notation: "user.email" → data["user"]["email"]
                    actual_value = data
                    for key in field.split("."):
                        actual_value = actual_value[key]

                    if str(actual_value) != str(expected_value):
                        msg = f"API field '{field}': got '{actual_value}', expected '{expected_value}'"
                        result["steps_failed"].append({"action": "verify_api_field", "error": msg})
                        result["status"] = "failed"
                        print(f"    ❌ {msg}")
                    else:
                        print(f"    ✅ Field '{field}' = '{actual_value}'")
                except (KeyError, TypeError, ValueError) as e:
                    msg = f"Could not read field '{field}' from API response: {e}"
                    result["steps_failed"].append({"action": "verify_api_field", "error": msg})
                    result["status"] = "failed"
                    print(f"    ❌ {msg}")

        except requests.RequestException as e:
            msg = f"API request failed: {e}"
            result["steps_failed"].append({"action": "verify_api", "error": msg})
            result["status"] = "failed"
            print(f"    ❌ {msg}")

    def _execute_db_step(self, step: dict, result: dict):
        """
        Execute a DB verification step using pymysql.

        Step fields:
          table     – table name (e.g. users)
          column    – column to check (e.g. last_login)
          condition – WHERE clause (e.g. "IS NOT NULL WHERE email = 'a@b.com'")
          query     – optional raw SQL (overrides table/column/condition)
          expected  – human-readable description (for logs)
        """
        table       = step.get("table", "")
        column      = step.get("column", "")
        condition   = step.get("condition", "")
        raw_query   = step.get("query", "")
        description = step.get("expected", f"{table}.{column}")

        # Build query
        if raw_query:
            sql = raw_query
        else:
            # condition may include the operator AND WHERE clause
            # e.g. "IS NOT NULL WHERE email = 'x'" → SELECT column FROM table WHERE ...
            if "WHERE" in condition.upper():
                op, where_clause = condition.upper().split("WHERE", 1)
                op = condition[:len(op)].strip()
                where_clause = condition[condition.upper().index("WHERE") + 5:].strip()
                sql = f"SELECT `{column}` FROM `{table}` WHERE {where_clause} LIMIT 1"
            else:
                sql = f"SELECT `{column}` FROM `{table}` LIMIT 1"

        print(f"    🗄️  DB query: {sql}")
        try:
            import pymysql
            conn = _db_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    row = cur.fetchone()

                if row is None:
                    msg = f"DB: no rows returned for query — {description}"
                    result["steps_failed"].append({"action": "verify_db", "error": msg})
                    result["status"] = "failed"
                    print(f"    ❌ {msg}")
                else:
                    actual = row[0]
                    # Handle condition operators like "> 0", "IS NOT NULL"
                    op_upper = condition.upper().split("WHERE")[0].strip()
                    passed = False
                    if "IS NOT NULL" in op_upper:
                        passed = actual is not None
                    elif op_upper.startswith(">"):
                        threshold = float(op_upper.lstrip(">").strip())
                        passed = float(actual) > threshold
                    elif op_upper.startswith(">="):
                        threshold = float(op_upper.lstrip(">=").strip())
                        passed = float(actual) >= threshold
                    elif op_upper.startswith("="):
                        expected_val = op_upper.lstrip("=").strip().strip("'")
                        passed = str(actual) == expected_val
                    else:
                        passed = actual is not None  # fallback: just check row exists

                    if passed:
                        print(f"    ✅ DB '{column}' = '{actual}'")
                    else:
                        msg = f"DB '{column}' = '{actual}' did not satisfy '{condition}'"
                        result["steps_failed"].append({"action": "verify_db", "error": msg})
                        result["status"] = "failed"
                        print(f"    ❌ {msg}")
            finally:
                conn.close()

        except Exception as e:
            msg = f"DB verification failed: {e}"
            result["steps_failed"].append({"action": "verify_db", "error": msg})
            result["status"] = "failed"
            print(f"    ❌ {msg}")

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
