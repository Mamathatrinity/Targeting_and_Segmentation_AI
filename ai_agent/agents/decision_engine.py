"""
Decision Engine - Decides what to run, skip, and prioritize
Simple rule-based + AI hybrid approach
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TestDecision:
    """Decision for a test"""
    test_name: str
    should_run: bool
    priority: int  # 1=highest, 5=lowest
    reason: str


class DecisionEngine:
    """Decides test execution priority and what to skip"""
    
    def __init__(self):
        # Simple rules for prioritization
        self.critical_keywords = ["login", "auth", "security", "payment"]
        self.high_keywords = ["segmentation", "targeting", "filter", "rule"]
        self.low_keywords = ["ui", "color", "style", "layout"]
    
    def prioritize_tests(self, tests: List[Dict[str, Any]], module: str, changed_files: List[str] = None) -> List[TestDecision]:
        """Prioritize tests based on simple rules"""
        
        decisions = []
        
        for test in tests:
            test_name = test.get("scenario", "").lower()
            
            # Determine priority
            priority = self._calculate_priority(test_name, module)
            
            # Decide if should run
            should_run = self._should_run(test_name, module, changed_files)
            
            # Reason
            reason = self._get_reason(test_name, priority, should_run, changed_files)
            
            decisions.append(TestDecision(
                test_name=test.get("scenario", ""),
                should_run=should_run,
                priority=priority,
                reason=reason
            ))
        
        # Sort by priority (lower number = higher priority)
        decisions.sort(key=lambda x: (not x.should_run, x.priority))
        
        return decisions
    
    def _calculate_priority(self, test_name: str, module: str) -> int:
        """Calculate priority 1-5"""
        
        # Critical (1)
        if any(keyword in test_name for keyword in self.critical_keywords):
            return 1
        
        # High (2)
        if any(keyword in test_name for keyword in self.high_keywords):
            return 2
        
        # Low (4)
        if any(keyword in test_name for keyword in self.low_keywords):
            return 4
        
        # Medium (3) - default
        return 3
    
    def _should_run(self, test_name: str, module: str, changed_files: List[str] = None) -> bool:
        """Decide if test should run"""
        
        # Always run critical tests
        if any(keyword in test_name for keyword in self.critical_keywords):
            return True
        
        # If we have change info, only run relevant tests
        if changed_files:
            module_lower = module.lower()
            return any(module_lower in f.lower() for f in changed_files)
        
        # Default: run all
        return True
    
    def _get_reason(self, test_name: str, priority: int, should_run: bool, changed_files: List[str] = None) -> str:
        """Get reason for decision"""
        
        if not should_run:
            return "Skipped - module unchanged"
        
        priority_map = {
            1: "Critical - security/auth related",
            2: "High - business logic",
            3: "Medium - standard validation",
            4: "Low - UI/cosmetic",
            5: "Low - optional"
        }
        
        return priority_map.get(priority, "Medium priority")
    
    def get_execution_plan(self, decisions: List[TestDecision]) -> Dict[str, Any]:
        """Get simplified execution plan"""
        
        to_run = [d for d in decisions if d.should_run]
        to_skip = [d for d in decisions if not d.should_run]
        
        return {
            "total_tests": len(decisions),
            "to_run": len(to_run),
            "to_skip": len(to_skip),
            "execution_order": [d.test_name for d in to_run],
            "skipped": [d.test_name for d in to_skip],
            "estimated_time_minutes": len(to_run) * 2  # Assume 2 min per test
        }
