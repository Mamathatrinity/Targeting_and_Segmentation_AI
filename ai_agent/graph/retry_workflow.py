"""
LangGraph Retry Workflow
Controlled flow with ONE retry cycle on failure.

Graph:
  generate → execute → check_failure
                          ├─ all_pass  → END
                          └─ has_fails → fix → retry_execute → END

Rules (from PDF pages 395-431):
  - Max 1 retry (never infinite loops)
  - Retry only for selector/timing failures (AI can heal those)
  - Logic/data failures go straight to END with analysis
  - Uses MergedPlannerStrategy (1 LLM call) + MergedValidatorDecision (1 LLM call)
  - SelectorHealer called per failed test during fix node
"""

from langgraph.graph import StateGraph, END
from typing import Dict, List, TypedDict, Optional
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import AIConfig
from langfuse_tracker import get_tracker

# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------
class RetryWorkflowState(TypedDict):
    """State that flows through all nodes."""
    # Inputs
    url: str
    module_name: str
    business_context: str
    previous_failures: List[str]

    # Generated data
    ui_data: Dict
    plan: Dict                  # merged strategy + scenarios

    # Test execution
    test_cases: List[Dict]
    execution_results: Dict     # first run
    retry_results: Dict         # second run (only populated on retry)

    # Analysis
    validation: Dict            # merged validator + decision output
    healed_selectors: Dict      # {test_name: {old_selector: new_selector}}

    # Flow control
    retry_count: int            # 0 or 1
    should_retry: bool
    tests_to_retry: List[str]

    # Final
    status: str
    final_report: Dict


# ---------------------------------------------------------------------------
# Workflow class
# ---------------------------------------------------------------------------
class RetryWorkflow:
    """
    LangGraph-controlled test workflow with one-shot self-healing retry.
    """

    MAX_RETRY = 1  # Hard limit – never more than one retry

    def __init__(self):
        self.graph = self._build_graph()

    # ------------------------------------------------------------------
    def _build_graph(self):
        wf = StateGraph(RetryWorkflowState)

        # Nodes
        wf.add_node("extract_ui",       self._extract_ui_node)
        wf.add_node("generate",         self._generate_node)
        wf.add_node("design",           self._design_node)
        wf.add_node("execute",          self._execute_node)
        wf.add_node("check_failure",    self._check_failure_node)
        wf.add_node("fix",              self._fix_node)
        wf.add_node("retry_execute",    self._retry_execute_node)
        wf.add_node("finalize",         self._finalize_node)

        # Fixed edges
        wf.add_edge("extract_ui",  "generate")
        wf.add_edge("generate",    "design")
        wf.add_edge("design",      "execute")
        wf.add_edge("execute",     "check_failure")

        # Conditional: retry or finish
        wf.add_conditional_edges(
            "check_failure",
            self._retry_decision,
            {
                "retry": "fix",
                "end":   "finalize",
            }
        )

        # Retry path
        wf.add_edge("fix",           "retry_execute")
        wf.add_edge("retry_execute", "finalize")

        # End
        wf.add_edge("finalize", END)

        wf.set_entry_point("extract_ui")
        return wf.compile()

    # ------------------------------------------------------------------
    # ── Decision function for conditional edge ────────────────────────
    # ------------------------------------------------------------------
    def _retry_decision(self, state: RetryWorkflowState) -> str:
        """Return 'retry' or 'end'."""
        if (
            state.get("should_retry")
            and state.get("retry_count", 0) < self.MAX_RETRY
            and state.get("tests_to_retry")
        ):
            return "retry"
        return "end"

    # ------------------------------------------------------------------
    # ── Nodes ─────────────────────────────────────────────────────────
    # ------------------------------------------------------------------

    def _extract_ui_node(self, state: RetryWorkflowState) -> RetryWorkflowState:
        print("\n" + "="*60)
        print("NODE 1: UI EXTRACTION")
        print("="*60)
        try:
            from ai_agent.tools.ui_extractor import extract_ui
            ui_data = extract_ui(state["url"], headless=False)
        except Exception as e:
            print(f"  ⚠️  UI extraction failed ({e}). Using minimal placeholder.")
            ui_data = {
                "title": state.get("module_name", "Unknown"),
                "url": state["url"],
                "summary": {},
                "sample_elements": {},
                "user_description": state.get("business_context", ""),
            }
        print(f"  ✓ URL: {ui_data.get('url', state['url'])}")
        state["ui_data"] = ui_data
        return state

    # ------------------------------------------------------------------
    def _generate_node(self, state: RetryWorkflowState) -> RetryWorkflowState:
        """Merged Planner+Strategy – 1 LLM call."""
        print("\n" + "="*60)
        print("NODE 2: MERGED PLAN GENERATION (1 LLM call)")
        print("="*60)

        from ai_agent.agents.merged_planner_strategy import MergedPlannerStrategyAgent
        agent = MergedPlannerStrategyAgent()
        plan = agent.generate(
            ui_data=state["ui_data"],
            module_name=state.get("module_name", "general"),
            business_context=state.get("business_context", ""),
            previous_failures=state.get("previous_failures", []),
        )
        print(f"  ✓ Priority={plan.get('priority')} | Depth={plan.get('depth')}")
        state["plan"] = plan
        return state

    # ------------------------------------------------------------------
    def _design_node(self, state: RetryWorkflowState) -> RetryWorkflowState:
        """Designer agent – converts scenarios → step-by-step test cases."""
        print("\n" + "="*60)
        print("NODE 3: TEST DESIGN")
        print("="*60)

        try:
            from ai_agent.agents.designer import designer_agent
            test_cases = designer_agent(state["plan"], state["ui_data"])
        except Exception as e:
            print(f"  ⚠️  Designer failed ({e}). Using scenario list as test cases.")
            scenarios = state["plan"]
            test_cases = (
                [{"scenario": s, "type": "positive", "steps": []}
                 for s in scenarios.get("positive_scenarios", [])] +
                [{"scenario": s, "type": "edge", "steps": []}
                 for s in scenarios.get("edge_cases", [])] +
                [{"scenario": s, "type": "negative", "steps": []}
                 for s in scenarios.get("negative_scenarios", [])]
            )

        # Apply MAX_TESTS guard
        if len(test_cases) > AIConfig.MAX_TESTS:
            print(f"  ⚠️  Capping to {AIConfig.MAX_TESTS} tests")
            test_cases = test_cases[:AIConfig.MAX_TESTS]

        print(f"  ✓ {len(test_cases)} test cases designed")
        state["test_cases"] = test_cases
        return state

    # ------------------------------------------------------------------
    def _execute_node(self, state: RetryWorkflowState) -> RetryWorkflowState:
        """Run test cases (no AI)."""
        print("\n" + "="*60)
        print("NODE 4: TEST EXECUTION (NO AI)")
        print("="*60)

        try:
            from ai_agent.tools.executor import execute_tests
            url_parts = state["url"].split("/")
            base_url = f"{url_parts[0]}//{url_parts[2]}"
            results = execute_tests(state["test_cases"], base_url)
        except Exception as e:
            print(f"  ⚠️  Executor error: {e}")
            results = {
                "summary": {"total_tests": 0, "passed": 0, "failed": 0, "pass_rate": "0%"},
                "results": [],
                "error": str(e),
            }

        s = results.get("summary", {})
        print(f"  ✓ Total={s.get('total_tests',0)} | "
              f"Passed={s.get('passed',0)} | Failed={s.get('failed',0)} | "
              f"Rate={s.get('pass_rate','0%')}")

        state["execution_results"] = results
        state["retry_count"] = state.get("retry_count", 0)
        return state

    # ------------------------------------------------------------------
    def _check_failure_node(self, state: RetryWorkflowState) -> RetryWorkflowState:
        """Merged Validator+Decision – 1 LLM call. Sets should_retry flag."""
        print("\n" + "="*60)
        print("NODE 5: VALIDATION + DECISION (1 LLM call)")
        print("="*60)

        from ai_agent.agents.merged_validator_decision import MergedValidatorDecisionAgent
        agent = MergedValidatorDecisionAgent()
        validation = agent.analyze(
            execution_results=state["execution_results"],
            module_name=state.get("module_name", "general"),
        )

        state["validation"] = validation

        # Decide retry: only selector/timing failures are healable
        tests_to_retry = validation.get("tests_to_rerun", [])
        healable_categories = {"selector", "timing"}

        # Filter: only retry if failures are healable types
        healable = [
            fd["test_name"]
            for fd in validation.get("failure_details", [])
            if fd.get("category") in healable_categories
            and fd["test_name"] in tests_to_retry
        ]

        should_retry = (
            bool(healable)
            and state.get("retry_count", 0) < self.MAX_RETRY
        )

        state["should_retry"] = should_retry
        state["tests_to_retry"] = healable

        print(f"  ✓ Status={validation.get('overall_status')} | "
              f"ShouldRetry={should_retry} | HealableTests={len(healable)}")
        return state

    # ------------------------------------------------------------------
    def _fix_node(self, state: RetryWorkflowState) -> RetryWorkflowState:
        """AI Selector Healing – fix broken selectors before retry."""
        print("\n" + "="*60)
        print("NODE 6: AI SELECTOR HEALING")
        print("="*60)

        from ai_agent.tools.selector_healer import SelectorHealer
        healer = SelectorHealer()

        healed = {}
        tests_to_retry = state.get("tests_to_retry", [])
        execution_results = state.get("execution_results", {})
        results_list = execution_results.get("results", [])

        for result in results_list:
            test_name = result.get("test_name", "")
            if test_name not in tests_to_retry:
                continue
            error_msg = result.get("error", "")
            if not error_msg:
                continue

            # Extract selector from error message
            failed_selector = healer.extract_selector_from_error(error_msg)
            if not failed_selector:
                continue

            print(f"  🔧 Healing: {test_name}")
            print(f"     Broken selector: {failed_selector}")

            # Use last known page HTML if available
            page_html = result.get("page_html", "")
            element_context = f"Element needed for test: {test_name}"

            heal_result = healer.heal(
                failed_selector=failed_selector,
                page_html=page_html,
                element_context=element_context,
            )

            if heal_result.get("new_selector"):
                print(f"     ✅ Healed → {heal_result['new_selector']} "
                      f"(confidence={heal_result.get('confidence', '?')})")
                healed[test_name] = {
                    "old": failed_selector,
                    "new": heal_result["new_selector"],
                    "confidence": heal_result.get("confidence", 0),
                }
            else:
                print(f"     ❌ Could not heal {test_name}")

        # Patch test cases with healed selectors
        if healed:
            patched = healer.patch_test_cases(state["test_cases"], healed)
            state["test_cases"] = patched
            print(f"  ✓ Healed {len(healed)} test(s)")
        else:
            print("  ℹ️  No selectors healed (no page HTML available or no patterns matched)")

        state["healed_selectors"] = healed
        state["retry_count"] = state.get("retry_count", 0) + 1
        return state

    # ------------------------------------------------------------------
    def _retry_execute_node(self, state: RetryWorkflowState) -> RetryWorkflowState:
        """Re-run only the previously failed tests after healing."""
        print("\n" + "="*60)
        print(f"NODE 7: RETRY EXECUTION (attempt {state.get('retry_count', 1)})")
        print("="*60)

        tests_to_retry = set(state.get("tests_to_retry", []))
        retry_cases = [
            tc for tc in state["test_cases"]
            if tc.get("scenario", tc.get("name", "")) in tests_to_retry
        ]

        if not retry_cases:
            print("  ⚠️  No test cases matched retry list – skipping")
            state["retry_results"] = state["execution_results"]
            return state

        print(f"  Retrying {len(retry_cases)} test(s)...")

        try:
            from ai_agent.tools.executor import execute_tests
            url_parts = state["url"].split("/")
            base_url = f"{url_parts[0]}//{url_parts[2]}"
            retry_results = execute_tests(retry_cases, base_url)
        except Exception as e:
            print(f"  ⚠️  Retry executor error: {e}")
            retry_results = {
                "summary": {"total_tests": 0, "passed": 0, "failed": 0, "pass_rate": "0%"},
                "results": [],
            }

        s = retry_results.get("summary", {})
        print(f"  ✓ Retry: Total={s.get('total_tests',0)} | "
              f"Passed={s.get('passed',0)} | Failed={s.get('failed',0)}")

        state["retry_results"] = retry_results
        return state

    # ------------------------------------------------------------------
    def _finalize_node(self, state: RetryWorkflowState) -> RetryWorkflowState:
        """Merge results and produce final report."""
        print("\n" + "="*60)
        print("NODE 8: FINALIZE")
        print("="*60)

        first_run = state.get("execution_results", {})
        retry_run = state.get("retry_results", {})
        validation = state.get("validation", {})

        # Merge: take retry results where available
        merged_results = list(first_run.get("results", []))
        if retry_run:
            retry_map = {r["test_name"]: r for r in retry_run.get("results", [])}
            for i, r in enumerate(merged_results):
                if r["test_name"] in retry_map:
                    merged_results[i] = retry_map[r["test_name"]]

        total = len(merged_results)
        passed = sum(1 for r in merged_results if r.get("status") == "passed")
        failed = total - passed

        final_report = {
            "module": state.get("module_name", "general"),
            "url": state["url"],
            "strategy": {
                "priority": state["plan"].get("priority"),
                "depth": state["plan"].get("depth"),
                "focus_areas": state["plan"].get("focus_areas", []),
                "rationale": state["plan"].get("rationale", ""),
            },
            "test_summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            },
            "retry": {
                "performed": state.get("retry_count", 0) > 0,
                "healed_selectors": state.get("healed_selectors", {}),
            },
            "validation": {
                "overall_status": validation.get("overall_status"),
                "recommendations": validation.get("recommendations", []),
                "summary": validation.get("summary", ""),
            },
            "test_results": merged_results,
        }

        print(f"  ✓ Module: {final_report['module']}")
        print(f"  ✓ Total={total} | Passed={passed} | Failed={failed} | "
              f"Rate={final_report['test_summary']['pass_rate']}")
        if final_report["retry"]["performed"]:
            healed_count = len(final_report["retry"]["healed_selectors"])
            print(f"  ✓ Retry performed | Healed={healed_count} selectors")

        state["final_report"] = final_report
        state["status"] = "complete"
        return state

    # ------------------------------------------------------------------
    # ── Public run method ────────────────────────────────────────────
    # ------------------------------------------------------------------
    def run(
        self,
        url: str,
        module_name: str = "general",
        business_context: str = "",
        previous_failures: Optional[List[str]] = None,
    ) -> Dict:
        """
        Run the full retry workflow.

        Args:
            url: Target URL
            module_name: Module identifier (e.g. 'segmentation')
            business_context: Plain-language description of what to test
            previous_failures: Failures from previous runs (for strategy)

        Returns:
            final_report dict
        """
        print("\n" + "="*60)
        print("RETRY WORKFLOW STARTED")
        print(f"  Module: {module_name}")
        print(f"  URL: {url}")
        print("="*60)

        initial_state: RetryWorkflowState = {
            "url": url,
            "module_name": module_name,
            "business_context": business_context,
            "previous_failures": previous_failures or [],
            "ui_data": {},
            "plan": {},
            "test_cases": [],
            "execution_results": {},
            "retry_results": {},
            "validation": {},
            "healed_selectors": {},
            "retry_count": 0,
            "should_retry": False,
            "tests_to_retry": [],
            "status": "initialized",
            "final_report": {},
        }

        final_state = self.graph.invoke(initial_state)

        # Flush Langfuse
        tracker = get_tracker()
        tracker.flush()

        print("\n" + "="*60)
        print("RETRY WORKFLOW COMPLETE")
        print("="*60)

        return final_state.get("final_report", {})


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------
def run_retry_workflow(
    url: str,
    module_name: str = "general",
    business_context: str = "",
    previous_failures: Optional[List[str]] = None,
) -> Dict:
    """Run the LangGraph retry workflow."""
    wf = RetryWorkflow()
    return wf.run(url, module_name, business_context, previous_failures)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    result = run_retry_workflow(
        url="https://ce-ts-dev.trinitylifesciences.com/",
        module_name="segmentation",
        business_context="Test segment creation and rule builder",
    )
    print(json.dumps(result, indent=2, default=str))
