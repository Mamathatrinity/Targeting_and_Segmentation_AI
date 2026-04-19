"""
Strategy Agent - Decides what to test, depth, and focus areas
Simple implementation without over-engineering
"""

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Literal
import yaml
import os


class TestingStrategy(BaseModel):
    """Testing strategy decision output"""
    module: str = Field(description="Module being tested")
    focus_areas: List[str] = Field(description="Key areas to focus on")
    depth: Literal["light", "medium", "deep"] = Field(description="Testing depth")
    priority: Literal["critical", "high", "medium", "low"] = Field(description="Priority level")
    rationale: str = Field(description="Why this strategy")


class StrategyAgent:
    """Decides testing strategy before generating tests"""
    
    def __init__(self, config):
        self.llm = AzureChatOpenAI(
            azure_deployment=config.get("azure_deployment", "gpt-4o"),
            api_version=config.get("api_version", "2024-02-15-preview"),
            temperature=0.3,
            max_tokens=400
        )
        
        # Load strategy prompt
        prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/strategy.yaml")
        with open(prompt_path, 'r') as f:
            prompt_data = yaml.safe_load(f)
        
        self.parser = PydanticOutputParser(pydantic_object=TestingStrategy)
        self.prompt = PromptTemplate(
            template=prompt_data['template'],
            input_variables=["module", "business_context", "previous_failures"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    def decide_strategy(self, module: str, business_context: str = "", previous_failures: List[str] = None) -> TestingStrategy:
        """Decide testing strategy for a module"""
        
        failures_text = "\n".join(previous_failures) if previous_failures else "None"
        
        chain = self.prompt | self.llm | self.parser
        
        try:
            strategy = chain.invoke({
                "module": module,
                "business_context": business_context or "Standard web application",
                "previous_failures": failures_text
            })
            return strategy
        except Exception as e:
            # Fallback strategy
            return TestingStrategy(
                module=module,
                focus_areas=["UI validation", "API response", "Database state"],
                depth="medium",
                priority="medium",
                rationale=f"Default strategy (error: {str(e)})"
            )
