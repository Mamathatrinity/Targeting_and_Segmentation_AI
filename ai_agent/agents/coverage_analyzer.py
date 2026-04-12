"""
Coverage Analyzer - Detects what is NOT being tested
Simple gap detection without complex analysis
"""

from typing import List, Dict, Set, Any


class CoverageAnalyzer:
    """Analyzes test coverage and finds gaps"""
    
    def __init__(self):
        # Common features that should be tested
        self.expected_features = {
            "login": ["valid login", "invalid login", "password reset", "session timeout"],
            "segmentation": ["rule validation", "filter logic", "edge cases", "data accuracy"],
            "targeting": ["audience selection", "criteria validation", "exclusion rules"],
            "dashboard": ["data display", "navigation", "responsive design"],
            "api": ["success responses", "error handling", "authentication", "rate limiting"],
            "database": ["data persistence", "data integrity", "transactions", "rollback"]
        }
    
    def analyze_coverage(self, module: str, generated_tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find coverage gaps"""
        
        # Get test scenarios
        tested_scenarios = set()
        for test in generated_tests:
            scenario = test.get("scenario", "").lower()
            tested_scenarios.add(scenario)
        
        # Find gaps
        gaps = self._find_gaps(module.lower(), tested_scenarios)
        
        # Calculate coverage
        coverage_pct = self._calculate_coverage(module.lower(), tested_scenarios)
        
        return {
            "module": module,
            "total_tests": len(generated_tests),
            "coverage_percentage": coverage_pct,
            "missing_tests": gaps,
            "recommendation": self._get_recommendation(coverage_pct, gaps)
        }
    
    def _find_gaps(self, module: str, tested_scenarios: Set[str]) -> List[str]:
        """Find what's not tested"""
        
        gaps = []
        
        # Get expected features for this module
        expected = self.expected_features.get(module, [])
        
        for feature in expected:
            # Check if any test covers this feature
            if not any(feature.lower() in scenario for scenario in tested_scenarios):
                gaps.append(feature)
        
        return gaps
    
    def _calculate_coverage(self, module: str, tested_scenarios: Set[str]) -> int:
        """Simple coverage percentage"""
        
        expected = self.expected_features.get(module, [])
        
        if not expected:
            return 100  # Unknown module, assume complete
        
        covered = 0
        for feature in expected:
            if any(feature.lower() in scenario for scenario in tested_scenarios):
                covered += 1
        
        return int((covered / len(expected)) * 100)
    
    def _get_recommendation(self, coverage_pct: int, gaps: List[str]) -> str:
        """Get recommendation"""
        
        if coverage_pct >= 90:
            return "Excellent coverage"
        elif coverage_pct >= 70:
            return f"Good coverage, consider adding: {', '.join(gaps[:2])}"
        elif coverage_pct >= 50:
            return f"Moderate coverage, missing: {', '.join(gaps[:3])}"
        else:
            return f"Low coverage, critical gaps: {', '.join(gaps)}"
