"""
Agent-Based Test Execution
Faster execution using AI agents with parallel execution and smart failure handling
"""
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from ai_agent.agents.advanced.ui_automation_agent import UIAutomationAgent
from ai_agent.tools.executor import TestExecutor

load_dotenv()

def load_test_cases(json_path: str):
    """Load test cases from JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('test_cases', [])

def run_with_ui_agent(base_url: str, test_cases: list, headless: bool = False):
    """
    Execute tests using UI Automation Agent with FRESH INCOGNITO LOGIN
    - Fresh browser context for each test
    - Faster execution (reduced timeouts)
    - Smart failure grouping
    - Pattern-based recommendations
    - Continues on failure (no stopping)
    """
    print("=" * 80)
    print("🤖 AGENT-BASED EXECUTION (Fresh Incognito Mode)")
    print("=" * 80)
    print(f"Total test cases: {len(test_cases)}")
    print(f"Base URL: {base_url}")
    print(f"Mode: Fresh incognito browser for each test")
    print()
    
    agent = UIAutomationAgent()
    
    # Convert test cases to agent format
    agent_tests = []
    for tc in test_cases:
        agent_test = {
            "name": tc.get("test_case_id", "Unknown"),
            "description": tc.get("description", ""),
            "steps": tc.get("steps", []),
            "expected_result": tc.get("expected_result", "")
        }
        agent_tests.append(agent_test)
    
    # Execute with agent (single pass, continue on failure)
    start_time = time.time()
    results = agent.execute_tests(agent_tests, base_url, headless=headless)
    execution_time = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['total_tests']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"⏱️  Execution Time: {execution_time:.2f}s ({execution_time/60:.1f} min)")
    print(f"⚡ Average per test: {execution_time/results['total_tests']:.1f}s")
    
    # Show failure groups if any
    if results.get('failure_groups'):
        print("\n" + "=" * 80)
        print("🔍 FAILURE PATTERNS")
        print("=" * 80)
        for group in results['failure_groups']:
            pattern = group.get('pattern', group.get('error_type', 'Unknown pattern'))
            tests = group.get('tests', group.get('test_cases', []))
            print(f"\n{pattern}:")
            print(f"  Affected tests: {len(tests)}")
            if isinstance(tests[0], dict):
                test_names = [t.get('name', t.get('test_name', 'Unknown')) for t in tests]
            else:
                test_names = tests
            print(f"  Tests: {', '.join(test_names[:5])}")
            if len(tests) > 5:
                print(f"  ... and {len(tests) - 5} more")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"reports/agent_execution_{timestamp}.json"
    os.makedirs("reports", exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed report: {report_path}")
    
    return results

def run_with_pytest_fresh(base_url: str):
    """
    Execute tests using pytest with FRESH CONTEXT
    - Fresh incognito browser for each test
    - Standard pytest execution
    - Requires MFA approval for each test
    """
    print("=" * 80)
    print("🧪 PYTEST EXECUTION (Fresh Incognito)")
    print("=" * 80)
    print("Running pytest with fresh browser contexts...")
    print("⚠️  Note: Each test requires fresh login (may need MFA approval)")
    print()
    
    import subprocess
    result = subprocess.run(
        ["pytest", "tests/test_login.py", "-v", "--html=reports/pytest_report.html", "--self-contained-html"],
        capture_output=False
    )
    
    return result.returncode == 0

def main():
    """Main execution"""
    base_url = os.getenv("BASE_URL", "https://ce-ts-dev.trinitylifesciences.com")
    
    print("\n" + "=" * 80)
    print("🚀 TEST EXECUTION WITH AI AGENTS (FRESH INCOGNITO)")
    print("=" * 80)
    print()
    print("Choose execution mode:")
    print()
    print("1. 🤖 AI Agent - RECOMMENDED (UIAutomationAgent)")
    print("   ✅ Fresh incognito browser for each test")
    print("   ✅ Continues on failure (no stopping)")
    print("   ✅ Smart failure pattern detection")
    print("   ✅ Faster execution (reduced timeouts)")
    print("   ✅ Groups similar failures")
    print("   ⚠️  Requires MFA approval during execution")
    print()
    print("2. 🧪 Standard Pytest")
    print("   ✅ Fresh incognito browser for each test")
    print("   ✅ Detailed HTML reports")
    print("   ❌ Stops on first failure")
    print("   ❌ Slower (waits 120s for MFA each test)")
    print("   ⚠️  Requires MFA approval for each test")
    print()
    print("3. 🔄 Both (Agent analysis + Pytest report)")
    print()
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        test_cases = load_test_cases("outputs/login_COMPLETE.json")
        run_with_ui_agent(base_url, test_cases, headless=False)
    
    elif choice == "2":
        run_with_pytest_fresh(base_url)
    
    elif choice == "3":
        # Run agent first for analysis
        test_cases = load_test_cases("outputs/login_COMPLETE.json")
        agent_results = run_with_ui_agent(base_url, test_cases, headless=False)
        
        # Then run pytest for detailed reporting
        print("\n" + "=" * 80)
        print("Running pytest for detailed HTML report...")
        print("=" * 80)
        run_with_pytest_fresh(base_url)
    
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()
