"""
Validator Agent
Analyzes test results and identifies failure root causes using AI
"""
from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from typing import Dict, List
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import AIConfig
from langfuse_tracker import get_tracker


class ValidatorAgent:
    """Analyzes test execution results"""
    
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
            max_tokens=AIConfig.MAX_TOKENS_VALIDATOR  # Small limit - just analysis
        )
        
        # Load prompt template from cache (reuse for cost reduction)
        from ai_agent.tools.prompt_cache import load_prompt
        template = load_prompt("validator_prompt.txt")
        
        # Token-efficient prompt
        self.prompt = PromptTemplate(
            input_variables=["results_summary"],
            template=template
        )
    
    def validate_results(self, execution_results: Dict) -> Dict:
        """
        Analyze test execution results
        
        Args:
            execution_results: Results from Executor
            
        Returns:
            Analysis with root causes and recommendations
        """
        # Get Langfuse tracker
        tracker = get_tracker()
        
        # Prepare compact summary for analysis
        summary = self._prepare_summary(execution_results)
        
        # Format prompt
        formatted_prompt = self.prompt.format(results_summary=json.dumps(summary, indent=2))
        
        # Call LLM with Langfuse tracking
        response = self.llm.invoke(formatted_prompt)
        
        # Track with Langfuse
        tracker.generation(
            name="validator_agent",
            model=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            prompt=formatted_prompt,
            completion=response.content,
            metadata={
                "total_tests": summary.get("total_tests", 0),
                "failed": summary.get("failed", 0),
                "stage": "result_validation"
            }
        )
        
        # Parse response
        try:
            # Remove markdown if present
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            analysis = json.loads(content)
            
            # Track agent execution
            tracker.trace_agent(
                agent_name="validator",
                input_data={"summary": summary},
                output_data=analysis,
                metadata={"status": analysis.get("status", "unknown")}
            )
            
            return analysis
        
        except json.JSONDecodeError:
            # Fallback: extract key info from text
            return {
                "status": "analysis_failed",
                "failure_count": execution_results.get("summary", {}).get("failed", 0),
                "root_causes": ["Unable to parse AI analysis"],
                "recommendations": ["Review logs manually"],
                "raw_response": response.content,
                "confidence": "low"
            }
    
    def _prepare_summary(self, execution_results: Dict) -> Dict:
        """Prepare compact summary for LLM (token-efficient)"""
        summary = execution_results.get("summary", {})
        results = execution_results.get("results", [])
        
        failed_tests = [
            {
                "name": r["test_name"],
                "error": r.get("error", ""),
                "failed_steps": r.get("steps_failed", [])
            }
            for r in results if r["status"] == "failed"
        ]
        
        return {
            "total_tests": summary.get("total_tests", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "pass_rate": summary.get("pass_rate", "0%"),
            "failed_tests": failed_tests[:5]  # Limit to 5 for tokens
        }


# Standalone function for workflow
def validator_agent(execution_results: Dict) -> Dict:
    """
    Analyze test execution results
    
    Args:
        execution_results: Results from executor
        
    Returns:
        AI analysis with root causes
    """
    validator = ValidatorAgent()
    return validator.validate_results(execution_results)


if __name__ == "__main__":
    # Test validator with sample results
    sample_results = {
        "summary": {
            "total_tests": 3,
            "passed": 2,
            "failed": 1,
            "pass_rate": "66.7%"
        },
        "results": [
            {
                "test_name": "test_login_valid",
                "status": "passed",
                "error": None
            },
            {
                "test_name": "test_login_invalid",
                "status": "failed",
                "error": "Could not find input field: Email",
                "steps_failed": [{"step_number": 2, "error": "Selector not found"}]
            },
            {
                "test_name": "test_navigation",
                "status": "passed",
                "error": None
            }
        ]
    }
    
    print("Testing Validator Agent...")
    try:
        analysis = validator_agent(sample_results)
        print(json.dumps(analysis, indent=2))
    except Exception as e:
        print(f"Error: {e}")
