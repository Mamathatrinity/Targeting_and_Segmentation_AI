"""
Failure Root Cause Analyzer - AI-Powered Failure Analysis

This agent analyzes test failures and provides intelligent root cause analysis
using GPT-4o to identify patterns and recommend fixes.

Key Features:
- Analyzes failure patterns across multiple tests
- Classifies errors into categories
- Provides actionable recommendations
- Calculates confidence levels
"""

import os
import json
from typing import Dict, List, Any
from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from ai_agent.config import AIConfig
from ai_agent.langfuse_tracker import tracker


class FailureRootCauseAnalyzer:
    """
    Intelligent failure analyzer using AI to find root causes
    """
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
            api_key=AIConfig.AZURE_OPENAI_API_KEY,
            api_version=AIConfig.AZURE_OPENAI_API_VERSION,
            deployment_name=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            temperature=0,
            max_tokens=400
        )
        
        # Load prompt
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "../prompts/failure_analyzer_prompt.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()
    
    def analyze(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze test failures and provide root cause analysis.
        
        Args:
            test_results: Test execution results with failures
            
        Returns:
            Root cause analysis with recommendations
        """
        failures = [
            t for t in test_results.get("test_results", [])
            if t.get("status") == "failed"
        ]
        
        if not failures:
            return {
                "has_failures": False,
                "message": "All tests passed - no analysis needed"
            }
        
        # Prepare failure summary for AI
        failure_summary = self._prepare_failure_summary(failures)
        
        # Ask AI for root cause analysis
        prompt = PromptTemplate(
            input_variables=["failures"],
            template=self.prompt_template
        )
        
        formatted_prompt = prompt.format(failures=json.dumps(failure_summary, indent=2))
        
        with tracker.trace_agent("failure_analyzer"):
            with tracker.generation(
                name="analyze_failures",
                model="gpt-4o",
                input=formatted_prompt
            ) as gen:
                response = self.llm.invoke(formatted_prompt)
                analysis_json = response.content
                gen.end(output=analysis_json)
        
        try:
            analysis = json.loads(analysis_json)
            analysis["has_failures"] = True
            analysis["total_failures"] = len(failures)
            return analysis
        except json.JSONDecodeError:
            return {
                "has_failures": True,
                "total_failures": len(failures),
                "error": "Failed to parse AI response",
                "raw_response": analysis_json
            }
    
    def _prepare_failure_summary(self, failures: List[Dict]) -> List[Dict]:
        """Prepare concise failure summary for AI analysis"""
        return [
            {
                "test": f["name"],
                "step": f.get("failed_step", "unknown"),
                "error": f.get("failure_reason", "unknown"),
                "type": f.get("error_type", "unknown")
            }
            for f in failures
        ]


def analyze_failures(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze test failures using AI.
    
    Args:
        test_results: Test execution results
        
    Returns:
        Root cause analysis
    """
    analyzer = FailureRootCauseAnalyzer()
    return analyzer.analyze(test_results)


if __name__ == "__main__":
    # Example usage
    example_results = {
        "test_results": [
            {
                "name": "Login test",
                "status": "failed",
                "failed_step": 3,
                "failure_reason": "Selector 'button#submit' not found",
                "error_type": "element_not_found"
            },
            {
                "name": "Signup test",
                "status": "failed",
                "failed_step": 5,
                "failure_reason": "Selector 'button#register' not found",
                "error_type": "element_not_found"
            }
        ]
    }
    
    analysis = analyze_failures(example_results)
    print(json.dumps(analysis, indent=2))
