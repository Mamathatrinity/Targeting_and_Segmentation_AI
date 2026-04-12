"""
Report Generator - Creates comprehensive test reports
Simple, stakeholder-friendly reports
"""

from typing import Dict, Any, List
from datetime import datetime
import json


class ReportGenerator:
    """Generates comprehensive test execution reports"""
    
    def generate_report(
        self,
        module: str,
        strategy: Dict[str, Any],
        execution_results: List[Dict[str, Any]],
        coverage: Dict[str, Any],
        cross_layer: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate full test report"""
        
        # Calculate metrics
        total_tests = len(execution_results)
        passed = sum(1 for r in execution_results if r.get("status") == "passed")
        failed = total_tests - passed
        
        # Risk assessment
        risk = self._assess_risk(failed, total_tests, coverage.get("coverage_percentage", 0))
        
        # Confidence score
        confidence = self._calculate_confidence(passed, total_tests, coverage.get("coverage_percentage", 0))
        
        # Test explanations
        explanations = self._generate_explanations(execution_results)
        
        return {
            "module": module,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{(passed/total_tests*100):.1f}%" if total_tests > 0 else "0%",
                "coverage": f"{coverage.get('coverage_percentage', 0)}%",
                "risk_level": risk,
                "confidence_score": f"{confidence}%"
            },
            "strategy": {
                "focus_areas": strategy.get("focus_areas", []),
                "depth": strategy.get("depth", "medium"),
                "priority": strategy.get("priority", "medium"),
                "rationale": strategy.get("rationale", "")
            },
            "coverage_analysis": {
                "tested": total_tests,
                "missing": coverage.get("missing_tests", []),
                "recommendation": coverage.get("recommendation", "")
            },
            "test_results": execution_results,
            "explanations": explanations,
            "cross_layer_validation": cross_layer if cross_layer else {"status": "Not performed"},
            "recommendations": self._generate_recommendations(failed, coverage.get("missing_tests", []))
        }
    
    def _assess_risk(self, failed: int, total: int, coverage: int) -> str:
        """Assess risk level"""
        
        if failed == 0 and coverage >= 80:
            return "LOW"
        elif failed <= 1 and coverage >= 60:
            return "MEDIUM"
        elif failed <= 2:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _calculate_confidence(self, passed: int, total: int, coverage: int) -> int:
        """Calculate confidence score 0-100"""
        
        if total == 0:
            return 0
        
        # Weight: 70% pass rate, 30% coverage
        pass_rate = (passed / total) * 100
        weighted_score = (pass_rate * 0.7) + (coverage * 0.3)
        
        return int(weighted_score)
    
    def _generate_explanations(self, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate test explanations"""
        
        explanations = []
        
        for result in results:
            scenario = result.get("scenario", "")
            status = result.get("status", "")
            
            explanation = {
                "test": scenario,
                "purpose": self._explain_purpose(scenario),
                "result": status,
                "why_important": self._explain_importance(scenario)
            }
            
            explanations.append(explanation)
        
        return explanations
    
    def _explain_purpose(self, scenario: str) -> str:
        """Explain test purpose"""
        
        scenario_lower = scenario.lower()
        
        if "login" in scenario_lower:
            return "Validates authentication security"
        elif "invalid" in scenario_lower or "error" in scenario_lower:
            return "Tests error handling and system resilience"
        elif "filter" in scenario_lower or "segmentation" in scenario_lower:
            return "Ensures business logic accuracy"
        elif "api" in scenario_lower:
            return "Validates backend integration"
        elif "database" in scenario_lower or "db" in scenario_lower:
            return "Confirms data persistence"
        else:
            return "Validates system functionality"
    
    def _explain_importance(self, scenario: str) -> str:
        """Explain why test is important"""
        
        scenario_lower = scenario.lower()
        
        if "login" in scenario_lower or "auth" in scenario_lower:
            return "Prevents unauthorized access"
        elif "segmentation" in scenario_lower or "targeting" in scenario_lower:
            return "Ensures correct audience targeting for campaigns"
        elif "filter" in scenario_lower or "rule" in scenario_lower:
            return "Prevents incorrect data filtering"
        elif "api" in scenario_lower:
            return "Ensures reliable system integration"
        else:
            return "Maintains system quality"
    
    def _generate_recommendations(self, failed: int, missing: List[str]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        if failed > 0:
            recommendations.append(f"Fix {failed} failing test(s) before deployment")
        
        if missing:
            recommendations.append(f"Add missing tests: {', '.join(missing[:3])}")
        
        if not recommendations:
            recommendations.append("System is ready for deployment")
        
        return recommendations
    
    def format_for_stakeholders(self, report: Dict[str, Any]) -> str:
        """Format report for non-technical stakeholders"""
        
        summary = report["summary"]
        
        output = f"""
╔══════════════════════════════════════════════════════════════╗
║           TEST EXECUTION REPORT - {report['module'].upper()}           
╚══════════════════════════════════════════════════════════════╝

📊 SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Tests Executed:      {summary['total_tests']}
  ✅ Passed:            {summary['passed']}
  ❌ Failed:            {summary['failed']}
  Success Rate:        {summary['success_rate']}
  Coverage:            {summary['coverage']}
  
🎯 QUALITY METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Risk Level:          {summary['risk_level']}
  Confidence Score:    {summary['confidence_score']}

💡 RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for i, rec in enumerate(report['recommendations'], 1):
            output += f"  {i}. {rec}\n"
        
        output += "\n"
        
        return output
