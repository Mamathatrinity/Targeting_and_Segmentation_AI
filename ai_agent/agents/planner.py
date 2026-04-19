"""
Planner Agent  (merged: Strategy + RAG + Planner → 1 LLM call)
Generates test scenarios from UI data using Azure GPT-4o.
Includes: testing strategy (priority/depth/focus), RAG context for complex
modules, and scenario generation — all in a single LLM call.
Backup of the separate files: merged_planner_strategy.py / strategy.py
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
from ai_agent.utils.prompt_loader import load_prompt
from ai_agent.utils.prompt_formatter import format_prompt
from ai_agent.rag.rag_store import get_rag_store


class TestScenarios(BaseModel):
    """Structured output for test scenarios — now includes strategy fields"""
    # ── Strategy fields (merged from StrategyAgent) ───────────────────────
    priority: Literal["critical", "high", "medium", "low"] = Field(
        default="medium", description="Testing priority for this module"
    )
    depth: Literal["light", "medium", "deep"] = Field(
        default="medium", description="Testing depth"
    )
    focus_areas: List[str] = Field(
        default_factory=list, description="Up to 3 key areas to focus on"
    )
    rationale: str = Field(
        default="", description="One sentence: why this strategy and scenario mix"
    )
    # ── Scenario fields (original) ────────────────────────────────────────
    positive_scenarios: List[str] = Field(description="Valid user flows (max 5)")
    edge_cases: List[str] = Field(description="Edge cases to test (max 3)")
    negative_scenarios: List[str] = Field(description="Invalid/error scenarios (max 3)")


class PlannerAgent:
    """Plans test scenarios from UI data (merged: Strategy + RAG + Planner)"""
    
    def __init__(self):
        # Validate configuration
        AIConfig.validate()
        
        # Initialize Azure GPT-4o
        self.llm = AzureChatOpenAI(
            azure_deployment=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            openai_api_version=AIConfig.AZURE_OPENAI_API_VERSION,
            azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
            api_key=AIConfig.AZURE_OPENAI_API_KEY,
            temperature=AIConfig.TEMPERATURE,
            max_tokens=AIConfig.MAX_TOKENS_PLANNER  # Token limit for cost control
        )
        
        # Output parser for structured JSON
        self.parser = PydanticOutputParser(pydantic_object=TestScenarios)
        
        # Load YAML prompt template
        self.prompt_data = load_prompt("planner.yaml")
        
        # RAG store — loaded once per agent instance (not per call)
        self.rag = get_rag_store()
    
    def generate_scenarios(self, ui_data: dict) -> dict:
        """
        Generate test scenarios from UI data
        
        Args:
            ui_data: Extracted UI elements from UIExtractor
            
        Returns:
            Structured test scenarios
        """
        # Get Langfuse tracker
        tracker = get_tracker()
        
        # Prepare compact UI data for token efficiency
        compact_ui = self._compact_ui_data(ui_data)
        
        # ── RAG: retrieve domain context ONCE for complex modules (k=2) ────
        module_name = ui_data.get("module_name", ui_data.get("focus_area", "general"))
        rag_context = ""
        if self.rag.is_complex_module(module_name):
            print(f"[Planner] 🔍 RAG retrieval for '{module_name}' (k=2)...")
            rag_context = self.rag.get_context(module_name, k=2)
        
        # ── Strategy context to inject into prompt ───────────────────────
        module_strategy = (
            f"Module: {module_name} | "
            f"Previous failures: {', '.join(ui_data.get('previous_failures', [])) or 'None'}"
        )
        
        # ── Focus area instruction ────────────────────────────────────────
        focus_area = ui_data.get("focus_area", "")
        focus_instruction = ui_data.get("focus_instruction", "")  # From modules_config
        
        # Fallback built-in instructions if not from config
        if not focus_instruction:
            if focus_area == "authentication":
                focus_instruction = "Focus ONLY on: Login flows, session management, password validation, remember me, account lockout, multi-factor auth"
            elif focus_area == "security":
                focus_instruction = "Focus ONLY on: SQL injection, XSS, CSRF, brute force, rate limiting, unauthorized access, session hijacking"
            elif focus_area == "ux":
                focus_instruction = "Focus ONLY on: Browser behaviors, tab navigation, copy-paste, autofill, keyboard shortcuts, back/forward buttons, form validation UX"
        
        # Format YAML prompt with BOTH natural language + UI data (combined approach)
        formatted_prompt = format_prompt(
            self.prompt_data,
            user_description=ui_data.get("user_description", "Test all features on this page"),  # Business context
            ui_data=json.dumps(compact_ui, indent=2),  # Technical details
            domain_context="HCP Targeting & Segmentation: Medical specialties, segments, filters, NPI numbers, HIPAA compliance",
            compliance_requirements="HIPAA compliance, PII masking, data privacy, audit logging",
            focus_area=focus_instruction,  # Add focus area instruction
            rag_context=rag_context or "No additional domain knowledge.",
            module_strategy=module_strategy,
            format_instructions=self.parser.get_format_instructions()
        )
        
        # Check cache first (50-70% cost savings)
        cached_response = get_cached_response(formatted_prompt)
        if cached_response:
            response_content = cached_response
        else:
            # Call LLM with Langfuse tracking
            response = self.llm.invoke(formatted_prompt)
            response_content = response.content
            
            # Cache the response
            set_cached_response(formatted_prompt, response_content)
        
        # Track with Langfuse
        tracker.generation(
            name="planner_agent",
            model=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            prompt=formatted_prompt,
            completion=response_content,
            metadata={
                "url": ui_data.get("url", ""),
                "stage": "scenario_planning",
                "cached": cached_response is not None,
                "rag_used": bool(rag_context),
                "module": module_name,
            }
        )
        
        # Parse structured output
        try:
            scenarios = self.parser.parse(response_content)
            result = scenarios.dict()
            
            # Track agent execution
            tracker.trace_agent(
                agent_name="planner",
                input_data=compact_ui,
                output_data=result,
                metadata={"scenarios_count": len(result.get("positive_scenarios", []))}
            )
            
            return result
        except Exception as e:
            # Fallback: try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Failed to parse LLM response: {e}")
    
    def _compact_ui_data(self, ui_data: dict) -> dict:
        """Reduce UI data size for token efficiency"""
        return {
            "title": ui_data.get("title", ""),
            "url": ui_data.get("url", ""),
            "summary": ui_data.get("summary", {}),
            "key_elements": ui_data.get("sample_elements", {})
        }


# Standalone function for workflow
def planner_agent(ui_data: dict) -> dict:
    """
    Generate test scenarios from UI data
    
    Args:
        ui_data: UI elements extracted by UIExtractor
        
    Returns:
        Test scenarios (positive, edge cases, negative)
    """
    planner = PlannerAgent()
    return planner.generate_scenarios(ui_data)


if __name__ == "__main__":
    # Test planner with sample UI data
    sample_ui = {
        "title": "Login Page",
        "url": "https://example.com/login",
        "summary": {
            "inputs": 2,
            "buttons": 1,
            "dropdowns": 0,
            "checkboxes": 1
        },
        "sample_elements": {
            "inputs": [
                {"type": "email", "placeholder": "Email", "label": "Email"},
                {"type": "password", "placeholder": "Password", "label": "Password"}
            ],
            "buttons": [
                {"text": "Login", "type": "submit"}
            ]
        }
    }
    
    print("Testing Planner Agent...")
    try:
        scenarios = planner_agent(sample_ui)
        print(json.dumps(scenarios, indent=2))
    except Exception as e:
        print(f"Error: {e}")
