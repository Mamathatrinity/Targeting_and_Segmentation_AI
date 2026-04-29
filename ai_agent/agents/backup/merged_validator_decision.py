"""
Merged Validator + Decision Engine Agent
Combines result validation (root cause analysis) + test prioritisation
into a SINGLE LLM call — saves 1 API round-trip per execution cycle.

Decision rules that don't need an LLM (critical keywords, etc.) are
still applied locally (zero cost) before the LLM call.
"""

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import AIConfig
from langfuse_tracker import get_tracker
from ai_agent.utils.cache import get_cached_response, set_cached_response


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class FailureDetail(BaseModel):
    test_name: str
    root_cause: str
    category: Literal["selector", "timing", "data", "auth", "logic", "network", "unknown"]
    fix_suggestion: str


class MergedValidationOutput(BaseModel):
    """Single LLM response: validation analysis + prioritised next actions."""

    # ── Validation portion ────────────────────────────────────────────────────
    overall_status: Literal["passed", "partial", "failed"] = Field(
        description="Overall test run status"
    )
    failure_details: List[FailureDetail] = Field(
        description="Root cause for each failed test (max 5)"
    )
    recommendations: List[str] = Field(
        description="Up to 3 actionable recommendations"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence in the analysis"
    )

    # ── Decision portion ──────────────────────────────────────────────────────
    tests_to_rerun: List[str] = Field(
        description="Test names that should be retried (selector/timing failures)"
    )
    tests_to_skip_next: List[str] = Field(
        description="Test names to skip next run (low value or persistent failures)"
    )
    priority_tests_next_run: List[str] = Field(
        description="Tests to run first in the next cycle (highest impact)"
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    summary: str = Field(
        description="One sentence summary of what happened and what to do next"
    )


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
MERGED_VALIDATOR_PROMPT = """\
You are a senior QA analyst reviewing automated test results for a pharmaceutical
HCP targeting platform (CE-TS).

Your job: provide root-cause analysis AND decide which tests to rerun, skip, or prioritise.

TEST RESULTS SUMMARY:
{results_summary}

FAILED TESTS (details):
{failed_tests_detail}

MODULE UNDER TEST: {module_name}

INSTRUCTIONS:
1. For each failed test: identify root_cause and category (selector/timing/data/auth/logic/network/unknown).
2. Give a fix_suggestion for each failure.
3. List up to 3 recommendations.
4. Decide:
   - tests_to_rerun: transient failures (selector healing possible, timing issues)
   - tests_to_skip_next: flaky / low-value tests that waste time
   - priority_tests_next_run: most important tests for next cycle
5. Write a one-sentence summary.
6. Only include tests in failure_details that actually failed (max 5).

{format_instructions}
"""


# ---------------------------------------------------------------------------
# Local rule-based decision helper (zero LLM cost)
# ---------------------------------------------------------------------------
_CRITICAL_KEYWORDS = {"login", "auth", "security", "payment", "mfa", "sso"}
_HIGH_KEYWORDS = {"segment", "targeting", "filter", "rule", "universe"}
_LOW_KEYWORDS = {"color", "style", "layout", "font", "tooltip"}


def _local_priority(test_name: str) -> int:
    """Return 1-5 priority without LLM."""
    name = test_name.lower()
    if any(k in name for k in _CRITICAL_KEYWORDS):
        return 1
    if any(k in name for k in _HIGH_KEYWORDS):
        return 2
    if any(k in name for k in _LOW_KEYWORDS):
        return 4
    return 3


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class MergedValidatorDecisionAgent:
    """
    Replaces ValidatorAgent + DecisionEngine with a single LLM call.
    Pure-rule decisions (priority sorting) still happen locally.
    """

    def __init__(self):
        AIConfig.validate()

        self.llm = AzureChatOpenAI(
            azure_deployment=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            openai_api_version=AIConfig.AZURE_OPENAI_API_VERSION,
            azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
            api_key=AIConfig.AZURE_OPENAI_API_KEY,
            temperature=AIConfig.TEMPERATURE,
            max_tokens=AIConfig.MAX_TOKENS_VALIDATOR,
        )

        self.parser = PydanticOutputParser(pydantic_object=MergedValidationOutput)
        self.prompt = PromptTemplate(
            template=MERGED_VALIDATOR_PROMPT,
            input_variables=["results_summary", "failed_tests_detail", "module_name"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )

    # ------------------------------------------------------------------
    def analyze(self, execution_results: Dict, module_name: str = "general") -> Dict:
        """
        Validate results + make decisions in one LLM call.

        Args:
            execution_results: Output from executor (summary + results list)
            module_name: Module that was tested

        Returns:
            Dict with validation analysis + decisions
        """
        tracker = get_tracker()

        # ── 1. Prepare compact summaries (token efficiency) ────────────────
        summary = execution_results.get("summary", {})
        results = execution_results.get("results", [])

        results_summary = {
            "total": summary.get("total_tests", len(results)),
            "passed": summary.get("passed", sum(1 for r in results if r.get("status") == "passed")),
            "failed": summary.get("failed", sum(1 for r in results if r.get("status") == "failed")),
            "pass_rate": summary.get("pass_rate", "0%"),
        }

        # Limit to 5 failures (token control)
        failed_detail = [
            {
                "name": r["test_name"],
                "error": r.get("error", "Unknown error")[:200],
                "failed_steps": r.get("steps_failed", [])[:3],
            }
            for r in results if r.get("status") == "failed"
        ][:5]

        # ── 2. If zero failures: skip LLM entirely ─────────────────────────
        if not failed_detail:
            print("[MergedValidator] ✅ All tests passed – skipping LLM call")
            all_names = [r["test_name"] for r in results]
            # Sort by local priority for next run
            all_names.sort(key=lambda n: _local_priority(n))
            return {
                "overall_status": "passed",
                "failure_details": [],
                "recommendations": ["All tests passed. Consider adding more edge cases."],
                "confidence": "high",
                "tests_to_rerun": [],
                "tests_to_skip_next": [],
                "priority_tests_next_run": all_names[:5],
                "summary": f"All {results_summary['total']} tests passed for {module_name}.",
            }

        # ── 3. Format prompt ───────────────────────────────────────────────
        formatted_prompt = self.prompt.format(
            results_summary=json.dumps(results_summary, indent=2),
            failed_tests_detail=json.dumps(failed_detail, indent=2),
            module_name=module_name,
        )

        # ── 4. Cache check ─────────────────────────────────────────────────
        cached = get_cached_response(formatted_prompt)
        if cached:
            response_content = cached
            print("[MergedValidator] ✅ Cache hit")
        else:
            print(f"[MergedValidator] 🤖 Calling GPT-4o to analyse {results_summary['failed']} failures...")
            response = self.llm.invoke(formatted_prompt)
            response_content = response.content
            set_cached_response(formatted_prompt, response_content)

        # ── 5. Langfuse ────────────────────────────────────────────────────
        tracker.generation(
            name="merged_validator_decision",
            model=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            prompt=formatted_prompt,
            completion=response_content,
            metadata={
                "module": module_name,
                "failed_count": results_summary["failed"],
                "cached": bool(cached),
                "stage": "merged_validation",
            },
        )

        # ── 6. Parse ────────────────────────────────────────────────────────
        try:
            result = self.parser.parse(response_content)
            output = result.dict()
        except Exception as e:
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                try:
                    output = json.loads(json_match.group())
                except Exception:
                    output = self._fallback_output(results_summary, failed_detail, str(e))
            else:
                output = self._fallback_output(results_summary, failed_detail, str(e))

        # ── 7. Enrich with local priority sort ─────────────────────────────
        all_tests = [r["test_name"] for r in results]
        all_tests.sort(key=lambda n: _local_priority(n))
        if not output.get("priority_tests_next_run"):
            output["priority_tests_next_run"] = all_tests[:5]

        print(f"[MergedValidator] Status={output.get('overall_status')} | "
              f"Rerun={len(output.get('tests_to_rerun', []))} | "
              f"Skip={len(output.get('tests_to_skip_next', []))}")

        return output

    # ------------------------------------------------------------------
    @staticmethod
    def _fallback_output(summary: Dict, failed: List, error: str) -> Dict:
        return {
            "overall_status": "partial" if summary.get("passed", 0) > 0 else "failed",
            "failure_details": [
                {"test_name": f["name"], "root_cause": f["error"],
                 "category": "unknown", "fix_suggestion": "Investigate manually"}
                for f in failed
            ],
            "recommendations": ["Review logs manually", "Rerun failed tests"],
            "confidence": "low",
            "tests_to_rerun": [f["name"] for f in failed],
            "tests_to_skip_next": [],
            "priority_tests_next_run": [],
            "summary": f"Analysis fallback (parse error: {error})",
        }


# ---------------------------------------------------------------------------
# Standalone convenience function
# ---------------------------------------------------------------------------
def merged_validate(execution_results: Dict, module_name: str = "general") -> Dict:
    """Drop-in for calling validator_agent + decision_engine separately."""
    agent = MergedValidatorDecisionAgent()
    return agent.analyze(execution_results, module_name)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_results = {
        "summary": {"total_tests": 5, "passed": 3, "failed": 2, "pass_rate": "60%"},
        "results": [
            {"test_name": "test_login_valid", "status": "passed", "error": None},
            {"test_name": "test_segment_add_rule", "status": "failed",
             "error": "TimeoutError: Timeout 30000ms exceeded waiting for selector '#add-rule-btn'"},
            {"test_name": "test_segment_save", "status": "failed",
             "error": "AssertionError: Expected 'Segment saved' but got empty text"},
            {"test_name": "test_login_mfa", "status": "passed", "error": None},
            {"test_name": "test_universe_filter", "status": "passed", "error": None},
        ],
    }

    result = merged_validate(sample_results, module_name="segmentation")
    print(json.dumps(result, indent=2))
