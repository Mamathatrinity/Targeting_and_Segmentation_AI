"""
Performance AI Agent
Tracks performance metrics and uses AI to identify bottlenecks
"""
from langchain_openai import AzureChatOpenAI
import time
import json
from typing import Dict, List
from ai_agent.config import AIConfig


class PerformanceAI:
    """AI-powered performance testing and bottleneck detection"""
    
    def __init__(self):
        AIConfig.validate()
        self.llm = AzureChatOpenAI(
            azure_deployment=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            openai_api_version=AIConfig.AZURE_OPENAI_API_VERSION,
            azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
            api_key=AIConfig.AZURE_OPENAI_API_KEY,
            temperature=0.2,
            max_tokens=2000
        )
        self.metrics = []
    
    def track_performance(self, test_name: str, metrics: Dict):
        """Track performance metrics for a test"""
        self.metrics.append({
            "test": test_name,
            "timestamp": time.time(),
            **metrics
        })
    
    def analyze_performance(self, baseline_metrics: List[Dict] = None) -> Dict:
        """
        AI analyzes performance data and identifies bottlenecks
        
        Returns recommendations for optimization
        """
        
        prompt = f"""Analyze performance test results and identify bottlenecks.

PERFORMANCE METRICS:
{json.dumps(self.metrics[-20:], indent=2)}

{f"BASELINE (Previous Run):\\n{json.dumps(baseline_metrics, indent=2)}" if baseline_metrics else ""}

IDENTIFY:
1. Slowest operations (page load, API calls, DB queries)
2. Performance regressions (slower than baseline)
3. Bottlenecks (what's causing slowness)
4. Optimization recommendations

RETURN JSON:
{{
  "bottlenecks": [
    {{
      "operation": "Segment list page load",
      "current_time_ms": 3500,
      "baseline_time_ms": 1200,
      "degradation": "191% slower",
      "likely_cause": "N+1 query problem in HCP data fetch",
      "recommendation": "Add database query optimization"
    }}
  ],
  "performance_score": 0-100,
  "critical_issues": ["List critical performance problems"],
  "quick_wins": ["Easy optimizations with high impact"]
}}
"""
        
        response = self.llm.invoke(prompt)
        
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except:
            return {"error": "Failed to analyze performance"}


class SecurityAI:
    """AI-powered security testing beyond basic SQL/XSS"""
    
    def __init__(self):
        AIConfig.validate()
        self.llm = AzureChatOpenAI(
            azure_deployment=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            openai_api_version=AIConfig.AZURE_OPENAI_API_VERSION,
            azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
            api_key=AIConfig.AZURE_OPENAI_API_KEY,
            temperature=0.4,
            max_tokens=2500
        )
    
    def generate_security_tests(self, endpoint: str, method: str) -> List[Dict]:
        """
        AI generates advanced security test cases
        
        Beyond basic SQL injection/XSS - includes:
        - CSRF attacks
        - JWT manipulation
        - IDOR (Insecure Direct Object Reference)
        - Rate limiting bypass
        - Session hijacking
        """
        
        prompt = f"""Generate advanced security test cases for this API endpoint.

ENDPOINT: {method} {endpoint}

GENERATE TESTS FOR:
1. CSRF (Cross-Site Request Forgery)
2. JWT Token Manipulation
3. IDOR (Access another user's data)
4. Rate Limiting Bypass
5. Session Hijacking
6. Authorization Bypass
7. Data Exposure (PII/HIPAA)

For HIPAA compliance (HCP data):
- Test unauthorized PII access
- Test data export without authorization
- Test audit logging

RETURN JSON ARRAY:
[
  {{
    "attack_type": "IDOR",
    "test_name": "Access another user's segment",
    "payload": "GET /segments/123 with user_id=999",
    "expected_result": "403 Forbidden",
    "severity": "critical"
  }}
]
"""
        
        response = self.llm.invoke(prompt)
        
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except:
            return []
