"""
Merged Planner + Strategy Agent
Combines Strategy (what/depth/focus) + Planner (generate scenarios)
into a SINGLE LLM call — saves 1 API round-trip per module.

RAG Rule (from PDF pages 395-431):
  - Retrieve domain context ONCE before the LLM call
  - Only for complex modules (segmentation, target_lists, universe_summary)
  - k=2 results max
  - Never retrieve inside loops
"""

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import AIConfig
from langfuse_tracker import get_tracker
from ai_agent.utils.cache import get_cached_response, set_cached_response
from ai_agent.rag.rag_store import get_rag_store


# ---------------------------------------------------------------------------
# Output schema – strategy + scenarios in one response
# ---------------------------------------------------------------------------
class MergedPlanOutput(BaseModel):
    """Single LLM response containing both strategy decisions and test scenarios."""

    # ── Strategy portion ──────────────────────────────────────────────────────
    priority: Literal["critical", "high", "medium", "low"] = Field(
        description="Testing priority for this module"
    )
    depth: Literal["light", "medium", "deep"] = Field(
        description="Testing depth"
    )
    focus_areas: List[str] = Field(
        description="Up to 3 key areas to focus on"
    )

    # ── Planner portion ───────────────────────────────────────────────────────
    positive_scenarios: List[str] = Field(
        description="Valid user flows to test (max 5)"
    )
    edge_cases: List[str] = Field(
        description="Edge cases and boundary conditions (max 3)"
    )
    negative_scenarios: List[str] = Field(
        description="Invalid/error flows to test (max 3)"
    )

    # ── Rationale (one sentence, cheap tokens) ────────────────────────────────
    rationale: str = Field(
        description="One sentence: why this strategy and scenario mix"
    )


# ---------------------------------------------------------------------------
# Prompt template (single call does strategy + scenarios)
# ---------------------------------------------------------------------------
MERGED_PROMPT_TEMPLATE = """\
You are an expert test architect for a pharmaceutical HCP targeting platform (CE-TS).
Your job: decide the testing strategy AND generate test scenarios in a SINGLE response.

MODULE: {module_name}
BUSINESS CONTEXT: {business_context}
PREVIOUS FAILURES: {previous_failures}

DOMAIN KNOWLEDGE (use only if relevant):
{rag_context}

UI DATA:
{ui_data}

APPLICATION CONTEXT: {domain_context}
COMPLIANCE: {compliance_requirements}

INSTRUCTIONS:
1. Choose priority (critical/high/medium/low) and depth (light/medium/deep).
2. List up to 3 focus_areas.
3. Generate:
   - positive_scenarios: up to 5 valid user flows
   - edge_cases: up to 3 boundary/edge conditions
   - negative_scenarios: up to 3 invalid/error flows
4. Write one rationale sentence.
5. Be specific – reference actual UI elements from the UI DATA above.

{format_instructions}
"""


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class MergedPlannerStrategyAgent:
    """
    Replaces two separate agents (StrategyAgent + PlannerAgent) with one LLM call.
    Injects RAG context automatically for complex modules.
    """

    def __init__(self):
        AIConfig.validate()

        self.llm = AzureChatOpenAI(
            azure_deployment=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            openai_api_version=AIConfig.AZURE_OPENAI_API_VERSION,
            azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
            api_key=AIConfig.AZURE_OPENAI_API_KEY,
            temperature=AIConfig.TEMPERATURE,
            max_tokens=AIConfig.MAX_TOKENS_PLANNER,  # generous for combined output
        )

        self.parser = PydanticOutputParser(pydantic_object=MergedPlanOutput)
        self.prompt = PromptTemplate(
            template=MERGED_PROMPT_TEMPLATE,
            input_variables=[
                "module_name", "business_context", "previous_failures",
                "rag_context", "ui_data", "domain_context", "compliance_requirements",
            ],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )

        # RAG store – loaded once at agent creation (not per call)
        self.rag = get_rag_store()

    # ------------------------------------------------------------------
    def generate(
        self,
        ui_data: dict,
        module_name: str = "general",
        business_context: str = "",
        previous_failures: Optional[List[str]] = None,
    ) -> dict:
        """
        Generate strategy + scenarios in a single LLM call.

        Args:
            ui_data: Extracted UI elements dict (from UIExtractor)
            module_name: e.g. 'segmentation', 'login', 'target_lists'
            business_context: Plain-language description of what to test
            previous_failures: List of failure descriptions from prior runs

        Returns:
            Dict with keys: priority, depth, focus_areas,
                            positive_scenarios, edge_cases, negative_scenarios, rationale
        """
        tracker = get_tracker()

        # ── 1. RAG retrieval (ONCE, only for complex modules) ──────────────
        rag_context = ""
        if self.rag.is_complex_module(module_name):
            print(f"[MergedPlanner] 🔍 RAG retrieval for '{module_name}' (k=2)...")
            rag_context = self.rag.get_context(module_name, k=2)
        else:
            print(f"[MergedPlanner] ⏭️  Skipping RAG for '{module_name}' (simple module)")

        # ── 2. Compact UI data ─────────────────────────────────────────────
        compact_ui = {
            "title": ui_data.get("title", ""),
            "url": ui_data.get("url", ""),
            "summary": ui_data.get("summary", {}),
            "key_elements": ui_data.get("sample_elements", {}),
        }

        failures_text = (
            "\n".join(f"- {f}" for f in previous_failures)
            if previous_failures else "None"
        )

        # ── 3. Format prompt ───────────────────────────────────────────────
        formatted_prompt = self.prompt.format(
            module_name=module_name,
            business_context=business_context or "Test all features thoroughly",
            previous_failures=failures_text,
            rag_context=rag_context or "No additional domain knowledge available.",
            ui_data=json.dumps(compact_ui, indent=2),
            domain_context=(
                "HCP Targeting & Segmentation: Medical specialties, "
                "segments, filters, NPI numbers, HIPAA compliance"
            ),
            compliance_requirements="HIPAA compliance, PII masking, data privacy, audit logging",
        )

        # ── 4. Cache check (50–70% cost savings on repeated calls) ─────────
        cached = get_cached_response(formatted_prompt)
        if cached:
            response_content = cached
            print("[MergedPlanner] ✅ Cache hit – skipping LLM call")
        else:
            print(f"[MergedPlanner] 🤖 Calling GPT-4o (module={module_name})...")
            response = self.llm.invoke(formatted_prompt)
            response_content = response.content
            set_cached_response(formatted_prompt, response_content)

        # ── 5. Langfuse tracking ────────────────────────────────────────────
        tracker.generation(
            name="merged_planner_strategy",
            model=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            prompt=formatted_prompt,
            completion=response_content,
            metadata={
                "module": module_name,
                "rag_used": bool(rag_context),
                "cached": bool(cached),
                "stage": "merged_plan_generation",
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
                output = json.loads(json_match.group())
            else:
                # Graceful fallback
                output = {
                    "priority": "medium", "depth": "medium",
                    "focus_areas": ["UI validation"],
                    "positive_scenarios": [f"Test {module_name} happy path"],
                    "edge_cases": [f"Test {module_name} empty state"],
                    "negative_scenarios": [f"Test {module_name} invalid input"],
                    "rationale": f"Fallback strategy (parse error: {e})",
                }

        # ── 7. Summary printout ─────────────────────────────────────────────
        print(f"[MergedPlanner] Priority={output.get('priority')} | "
              f"Depth={output.get('depth')} | "
              f"Scenarios={len(output.get('positive_scenarios', []))}+ve / "
              f"{len(output.get('edge_cases', []))}edge / "
              f"{len(output.get('negative_scenarios', []))}neg")

        return output


# ---------------------------------------------------------------------------
# Standalone convenience function
# ---------------------------------------------------------------------------
def merged_plan(
    ui_data: dict,
    module_name: str = "general",
    business_context: str = "",
    previous_failures: Optional[List[str]] = None,
) -> dict:
    """Drop-in replacement for calling strategy_agent + planner_agent separately."""
    agent = MergedPlannerStrategyAgent()
    return agent.generate(ui_data, module_name, business_context, previous_failures)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_ui = {
        "title": "Segmentation",
        "url": "https://ce-ts-dev.trinitylifesciences.com/segmentation",
        "summary": {"inputs": 5, "buttons": 3, "dropdowns": 4},
        "sample_elements": {
            "buttons": [{"text": "Add Rule"}, {"text": "Save Segment"}, {"text": "Preview"}],
            "dropdowns": [{"label": "Criterion"}, {"label": "Operator"}],
        },
    }

    result = merged_plan(sample_ui, module_name="segmentation")
    print(json.dumps(result, indent=2))
