"""
Planner Agent
Generates test scenarios from UI data using Azure GPT-4o
"""
from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import AIConfig
from langfuse_tracker import get_tracker


class TestScenarios(BaseModel):
    """Structured output for test scenarios"""
    positive_scenarios: List[str] = Field(description="Valid user flows (max 5)")
    edge_cases: List[str] = Field(description="Edge cases to test (max 3)")
    negative_scenarios: List[str] = Field(description="Invalid/error scenarios (max 3)")


class PlannerAgent:
    """Plans test scenarios from UI data"""
    
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
        
        # Load prompt template from cache (reuse for cost reduction)
        from ai_agent.tools.prompt_cache import load_prompt
        template = load_prompt("planner_prompt.txt")
        
        # Token-efficient prompt template
        self.prompt = PromptTemplate(
            input_variables=["ui_data"],
            template=template,
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
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
        
        # Format prompt
        formatted_prompt = self.prompt.format(ui_data=json.dumps(compact_ui, indent=2))
        
        # Call LLM with Langfuse tracking
        response = self.llm.invoke(formatted_prompt)
        
        # Track with Langfuse
        tracker.generation(
            name="planner_agent",
            model=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            prompt=formatted_prompt,
            completion=response.content,
            metadata={"url": ui_data.get("url", ""), "stage": "scenario_planning"}
        )
        
        # Parse structured output
        try:
            scenarios = self.parser.parse(response.content)
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
