"""
Designer Agent
Converts test scenarios into executable YAML test steps
"""
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List, Dict
import yaml
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import AIConfig
from langfuse_tracker import get_tracker
from ai_agent.utils.cache import get_cached_response, set_cached_response
from ai_agent.utils.prompt_loader import load_prompt
from ai_agent.utils.prompt_formatter import format_prompt


class TestStep(BaseModel):
    """Single test step"""
    action: str = Field(description="Action to perform: navigate, fill, click, verify")
    target: str = Field(description="Element to interact with")
    value: str = Field(default="", description="Value to use (for fill actions)")
    expected: str = Field(default="", description="Expected result")


class TestCase(BaseModel):
    """Complete test case"""
    name: str = Field(description="Test case name")
    description: str = Field(description="What this test validates")
    steps: List[TestStep] = Field(description="Ordered test steps")


class DesignerAgent:
    """Converts scenarios to executable test steps"""
    
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
            max_tokens=AIConfig.MAX_TOKENS_DESIGNER
        )
        
        # Load YAML prompt template
        self.prompt_data = load_prompt("ai_agent/prompts/designer.yaml")
    
    def design_tests(self, scenarios: dict, ui_data: dict, max_tests: int = None) -> List[dict]:
        """
        Convert scenarios to test steps
        
        Args:
            scenarios: Test scenarios from PlannerAgent
            ui_data: UI elements for reference
            max_tests: Maximum number of tests (default from config)
            
        Returns:
            List of test cases with steps
        """
        if max_tests is None:
            max_tests = AIConfig.MAX_TESTS
        
        # Prepare compact data
        scenarios_text = self._format_scenarios(scenarios)
        ui_elements_text = self._format_ui_elements(ui_data)
        
        # Get Langfuse tracker
        tracker = get_tracker()
        
        # Format YAML prompt with variables
        formatted_prompt = format_prompt(
            self.prompt_data,
            scenarios=scenarios_text,
            ui_elements=ui_elements_text
        )
        
        # Check cache first (50-70% cost savings)
        cache_key = f"{scenarios_text}_{ui_elements_text}"
        cached_response = get_cached_response(formatted_prompt, cache_key)
        if cached_response:
            response_content = cached_response
        else:
            # Call LLM with Langfuse tracking
            response = self.llm.invoke(formatted_prompt)
            response_content = response.content
            
            # Cache the response
            set_cached_response(formatted_prompt, cache_key, response_content)
        
        # Track with Langfuse
        tracker.generation(
            name="designer_agent",
            model=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            prompt=formatted_prompt,
            completion=response_content,
            metadata={"max_tests": max_tests, "stage": "test_design", "cached": cached_response is not None}
        )
        
        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            content = response_content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            data = json.loads(content)
            test_cases = data.get("test_cases", [])
            
            # Track agent execution
            tracker.trace_agent(
                agent_name="designer",
                input_data={"scenarios": scenarios_text[:200]},
                output_data={"test_count": len(test_cases)},
                metadata={"tests_generated": len(test_cases)}
            )
            
            return test_cases
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Response: {response_content}")
            raise
    
    def _format_scenarios(self, scenarios: dict) -> str:
        """Format scenarios for prompt (token-efficient)"""
        lines = []
        
        if "positive_scenarios" in scenarios:
            lines.append("Positive:")
            for s in scenarios["positive_scenarios"][:3]:  # Limit for tokens
                lines.append(f"  - {s}")
        
        if "edge_cases" in scenarios:
            lines.append("Edge Cases:")
            for s in scenarios["edge_cases"][:2]:
                lines.append(f"  - {s}")
        
        if "negative_scenarios" in scenarios:
            lines.append("Negative:")
            for s in scenarios["negative_scenarios"][:2]:
                lines.append(f"  - {s}")
        
        return "\n".join(lines)
    
    def _format_ui_elements(self, ui_data: dict) -> str:
        """Format UI elements for prompt (token-efficient)"""
        elements = ui_data.get("sample_elements", {})
        
        lines = ["Inputs:"]
        for inp in elements.get("inputs", [])[:3]:
            lines.append(f"  - {inp.get('label') or inp.get('placeholder') or inp.get('name')}")
        
        lines.append("Buttons:")
        for btn in elements.get("buttons", [])[:3]:
            lines.append(f"  - {btn.get('text')}")
        
        return "\n".join(lines)
    
    def export_to_yaml(self, test_cases: List[dict], output_file: str = "tests.yaml"):
        """Export test cases to YAML file"""
        with open(output_file, 'w') as f:
            yaml.dump({"tests": test_cases}, f, default_flow_style=False, sort_keys=False)
        print(f"Tests exported to {output_file}")


# Standalone function for workflow
def designer_agent(scenarios: dict, ui_data: dict) -> List[dict]:
    """
    Convert scenarios to executable test steps
    
    Args:
        scenarios: Test scenarios from planner
        ui_data: UI elements
        
    Returns:
        List of test cases with steps
    """
    designer = DesignerAgent()
    return designer.design_tests(scenarios, ui_data)


if __name__ == "__main__":
    # Test designer with sample scenarios
    sample_scenarios = {
        "positive_scenarios": [
            "User logs in with valid credentials",
            "User navigates to dashboard after login"
        ],
        "edge_cases": [
            "User tries to login with empty fields"
        ],
        "negative_scenarios": [
            "User enters invalid password"
        ]
    }
    
    sample_ui = {
        "sample_elements": {
            "inputs": [
                {"label": "Email", "placeholder": "Enter email"},
                {"label": "Password", "placeholder": "Enter password"}
            ],
            "buttons": [
                {"text": "Login"}
            ]
        }
    }
    
    print("Testing Designer Agent...")
    try:
        tests = designer_agent(sample_scenarios, sample_ui)
        print(json.dumps(tests, indent=2))
    except Exception as e:
        print(f"Error: {e}")
