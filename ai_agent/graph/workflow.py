"""
LangGraph Workflow
Controlled multi-agent workflow: Planner → Designer → Executor → Validator → END
NO LOOPS, NO RETRIES
"""
from langgraph.graph import StateGraph, END
from typing import Dict, TypedDict
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import AIConfig
from langfuse_tracker import get_tracker


# State definition for workflow
class WorkflowState(TypedDict):
    """State passed between agents"""
    url: str
    ui_data: Dict
    scenarios: Dict
    test_cases: list
    execution_results: Dict
    validation_analysis: Dict
    status: str
    # New fields for integrated agents
    api_url: str
    data_source: str
    test_mode: str  # 'ui_only', 'full', 'api_only', 'data_only'
    api_results: Dict
    data_results: Dict


class AITestingWorkflow:
    """Controlled workflow with LangGraph"""
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build fixed workflow graph using StateGraph
        
        Flow: Planner → Designer → Executor → Validator → END
        """
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (agents/tools)
        workflow.add_node("ui_extractor", self._ui_extractor_node)
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("designer", self._designer_node)
        workflow.add_node("executor", self._executor_node)
        workflow.add_node("validator", self._validator_node)
        
        # New integrated agents (optional)
        workflow.add_node("ui_automation", self._ui_automation_node)
        workflow.add_node("api_testing", self._api_testing_node)
        workflow.add_node("data_validation", self._data_validation_node)
        
        # Define FIXED edges (NO conditionals, NO loops)
        workflow.add_edge("ui_extractor", "planner")
        workflow.add_edge("planner", "designer")
        workflow.add_edge("designer", "executor")
        workflow.add_edge("executor", "validator")
        workflow.add_edge("validator", END)  # 🚨 ALWAYS END HERE
        
        # Set entry point
        workflow.set_entry_point("ui_extractor")
        
        return workflow.compile()
    
    def _ui_extractor_node(self, state: WorkflowState) -> WorkflowState:
        """Node 1: Extract UI elements"""
        print("\n" + "="*60)
        print("STEP 1: UI EXTRACTION")
        print("="*60)
        
        from tools.ui_extractor import extract_ui
        
        ui_data = extract_ui(state["url"], headless=False)
        print(f"✓ Extracted UI from: {ui_data['url']}")
        print(f"  - Title: {ui_data['title']}")
        print(f"  - Elements: {ui_data.get('summary', {})}")
        
        state["ui_data"] = ui_data
        state["status"] = "ui_extracted"
        return state
    
    def _planner_node(self, state: WorkflowState) -> WorkflowState:
        """Node 2: Generate test scenarios (LLM)"""
        print("\n" + "="*60)
        print("STEP 2: SCENARIO PLANNING (AI)")
        print("="*60)
        
        from agents.planner import planner_agent
        
        scenarios = planner_agent(state["ui_data"])
        print(f"✓ Generated scenarios:")
        print(f"  - Positive: {len(scenarios.get('positive_scenarios', []))}")
        print(f"  - Edge cases: {len(scenarios.get('edge_cases', []))}")
        print(f"  - Negative: {len(scenarios.get('negative_scenarios', []))}")
        
        state["scenarios"] = scenarios
        state["status"] = "scenarios_generated"
        return state
    
    def _designer_node(self, state: WorkflowState) -> WorkflowState:
        """Node 3: Design test steps (LLM)"""
        print("\n" + "="*60)
        print("STEP 3: TEST DESIGN (AI)")
        print("="*60)
        
        from agents.designer import designer_agent
        
        test_cases = designer_agent(state["scenarios"], state["ui_data"])
        print(f"✓ Designed {len(test_cases)} test cases")
        
        # Apply MAX_TESTS limit
        if len(test_cases) > AIConfig.MAX_TESTS:
            print(f"  ⚠ Limiting to {AIConfig.MAX_TESTS} tests")
            test_cases = test_cases[:AIConfig.MAX_TESTS]
        
        state["test_cases"] = test_cases
        state["status"] = "tests_designed"
        return state
    
    def _executor_node(self, state: WorkflowState) -> WorkflowState:
        """Node 4: Execute tests (NO AI)"""
        print("\n" + "="*60)
        print("STEP 4: TEST EXECUTION (NO AI)")
        print("="*60)
        
        from tools.executor import execute_tests
        
        # Extract base URL from original URL
        url_parts = state["url"].split("/")
        base_url = f"{url_parts[0]}//{url_parts[2]}"
        
        execution_results = execute_tests(state["test_cases"], base_url)
        
        summary = execution_results["summary"]
        print(f"✓ Execution complete:")
        print(f"  - Total: {summary['total_tests']}")
        print(f"  - Passed: {summary['passed']}")
        print(f"  - Failed: {summary['failed']}")
        print(f"  - Pass Rate: {summary['pass_rate']}")
        
        state["execution_results"] = execution_results
        state["status"] = "tests_executed"
        return state
    
    def _validator_node(self, state: WorkflowState) -> WorkflowState:
        """Node 5: Validate results (LLM)"""
        print("\n" + "="*60)
        print("STEP 5: RESULT VALIDATION (AI)")
        print("="*60)
        
        from agents.validator import validator_agent
        
        analysis = validator_agent(state["execution_results"])
        print(f"✓ Analysis complete:")
        print(f"  - Status: {analysis.get('status', 'unknown')}")
        print(f"  - Confidence: {analysis.get('confidence', 'unknown')}")
        
        if analysis.get("root_causes"):
            print(f"  - Root causes: {analysis['root_causes']}")
        if analysis.get("recommendations"):
            print(f"  - Recommendations: {analysis['recommendations']}")
        
        state["validation_analysis"] = analysis
        state["status"] = "complete"
        return state
    
    def run(self, url: str) -> Dict:
        """
        Run complete workflow
        
        Args:
            url: Target URL to test
            
        Returns:
            Final state with all results
        """
        print("\n" + "="*60)
        print("AI TESTING WORKFLOW STARTED")
        print("="*60)
        print(f"Target URL: {url}")
        print(f"Max Tests: {AIConfig.MAX_TESTS}")
        print(f"Timeout: {AIConfig.TIMEOUT_MINUTES} minutes")
        
        # Initialize state
        initial_state = {
            "url": url,
            "ui_data": {},
            "scenarios": {},
            "test_cases": [],
            "execution_results": {},
            "validation_analysis": {},
            "status": "initialized"
        }
        
        # Run workflow (FIXED path, no loops)
        final_state = self.graph.invoke(initial_state)
        
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE")
        print("="*60)
        
        # Flush Langfuse tracking data
        tracker = get_tracker()
        tracker.flush()
        
        return final_state


# Standalone function for easy import
def run_workflow(url: str) -> Dict:
    """
    Run AI testing workflow
    
    Args:
        url: Target URL
        
    Returns:
        Complete workflow results
    """
    workflow = AITestingWorkflow()
    return workflow.run(url)


def run_multi_module_workflow(modules: list, base_url: str = "") -> Dict:
    """
    Run AI testing workflow across multiple modules/pages
    
    Args:
        modules: List of module configs with 'name', 'url', 'description'
        base_url: Base URL to prepend to module URLs
        
    Returns:
        Aggregated results from all modules
    """
    print("\n" + "="*60)
    print("MULTI-MODULE WORKFLOW STARTED")
    print("="*60)
    print(f"Modules to test: {len(modules)}")
    print(f"Base URL: {base_url}")
    
    all_results = {
        "modules": [],
        "summary": {
            "total_modules": len(modules),
            "completed": 0,
            "failed": 0,
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0
        }
    }
    
    workflow = AITestingWorkflow()
    
    for idx, module in enumerate(modules, 1):
        module_name = module.get("name", f"module_{idx}")
        module_url = module.get("url", "")
        full_url = f"{base_url}{module_url}" if base_url else module_url
        
        print(f"\n{'='*60}")
        print(f"MODULE {idx}/{len(modules)}: {module_name}")
        print(f"{'='*60}")
        print(f"URL: {full_url}")
        print(f"Description: {module.get('description', 'N/A')}")
        
        try:
            # Run workflow for this module
            result = workflow.run(full_url)
            
            module_result = {
                "name": module_name,
                "url": full_url,
                "status": result.get("status", "unknown"),
                "execution_results": result.get("execution_results", {}),
                "validation_analysis": result.get("validation_analysis", {})
            }
            
            all_results["modules"].append(module_result)
            all_results["summary"]["completed"] += 1
            
            # Aggregate test counts
            exec_summary = result.get("execution_results", {}).get("summary", {})
            all_results["summary"]["total_tests"] += exec_summary.get("total_tests", 0)
            all_results["summary"]["total_passed"] += exec_summary.get("passed", 0)
            all_results["summary"]["total_failed"] += exec_summary.get("failed", 0)
            
            print(f"\n✓ Module '{module_name}' completed")
            
        except Exception as e:
            print(f"\n❌ Module '{module_name}' failed: {e}")
            all_results["summary"]["failed"] += 1
            all_results["modules"].append({
                "name": module_name,
                "url": full_url,
                "status": "error",
                "error": str(e)
            })
    
    # Calculate overall pass rate
    total = all_results["summary"]["total_tests"]
    passed = all_results["summary"]["total_passed"]
    all_results["summary"]["overall_pass_rate"] = f"{(passed/total*100):.1f}%" if total > 0 else "0%"
    
    print("\n" + "="*60)
    print("MULTI-MODULE WORKFLOW COMPLETE")
    print("="*60)
    print(f"Modules Completed: {all_results['summary']['completed']}/{all_results['summary']['total_modules']}")
    print(f"Total Tests: {all_results['summary']['total_tests']}")
    print(f"Overall Pass Rate: {all_results['summary']['overall_pass_rate']}")
    
    # Flush Langfuse
    tracker = get_tracker()
    tracker.flush()
    
    return all_results


if __name__ == "__main__":
    import sys
    
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"
    
    print(f"Testing workflow with: {test_url}")
    results = run_workflow(test_url)
    
    print("\nFinal Status:", results.get("status"))
