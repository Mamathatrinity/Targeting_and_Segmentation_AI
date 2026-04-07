"""
Advanced AI Testing Orchestrator
Combines all 6 AI techniques into one powerful testing system
"""
from ai_agent.agents.self_healing import SelfHealingAgent
from ai_agent.agents.visual_regression import VisualRegressionAgent
from ai_agent.agents.predictive_selector import PredictiveTestSelector
from ai_agent.agents.test_data_generator import TestDataGenerator
from ai_agent.agents.performance_security_ai import PerformanceAI, SecurityAI
import json
from typing import Dict, List


class AdvancedAITestOrchestrator:
    """Master orchestrator using all 6 AI techniques"""
    
    def __init__(self):
        # Initialize all AI agents
        self.self_healer = SelfHealingAgent()
        self.visual_tester = VisualRegressionAgent()
        self.test_selector = PredictiveTestSelector()
        self.data_generator = TestDataGenerator()
        self.performance_ai = PerformanceAI()
        self.security_ai = SecurityAI()
        
        print("🤖 Advanced AI Testing System Initialized")
        print("   ✓ Self-Healing Tests")
        print("   ✓ Visual Regression")
        print("   ✓ Predictive Test Selection")
        print("   ✓ AI Test Data Generator")
        print("   ✓ Performance AI")
        print("   ✓ Security AI")
    
    def run_smart_test_suite(self, config: Dict) -> Dict:
        """
        Run complete AI-powered test suite
        
        Workflow:
        1. Predictive Selection: Choose which tests to run (83% faster)
        2. Data Generation: Generate realistic test data
        3. Self-Healing: Auto-fix broken selectors
        4. Visual Regression: Check UI changes
        5. Performance AI: Track and analyze performance
        6. Security AI: Run advanced security tests
        """
        
        results = {
            "stages": {},
            "overall_status": "in_progress"
        }
        
        # STAGE 1: Predictive Test Selection
        print("\n📊 Stage 1: Predictive Test Selection...")
        changed_files = config.get("changed_files", [])
        if changed_files:
            prediction = self.test_selector.predict_affected_tests(changed_files)
            results["stages"]["predictive_selection"] = prediction
            print(f"   ✓ Selected {len(prediction['recommended_tests'])} tests")
            print(f"   ✓ Skipping {len(prediction['skip_tests'])} irrelevant tests")
            print(f"   ✓ Estimated savings: {prediction.get('estimated_time_savings')}")
        
        # STAGE 2: AI Test Data Generation
        print("\n🎲 Stage 2: Generating Test Data...")
        test_data = self.data_generator.generate_hcp_data(
            count=config.get("test_data_count", 50),
            specialties=config.get("specialties", ["Cardiology", "Oncology"]),
            states=config.get("states", ["California", "New York"])
        )
        results["stages"]["data_generation"] = {
            "records_generated": len(test_data),
            "sample": test_data[:2]
        }
        print(f"   ✓ Generated {len(test_data)} realistic HCP records")
        
        # STAGE 3: Execute Tests with Self-Healing
        print("\n🔧 Stage 3: Executing Tests (with Self-Healing)...")
        test_failures = config.get("test_failures", [])
        if test_failures:
            healed_tests = []
            for failure in test_failures:
                healing_result = self.self_healer.auto_heal_test(
                    failure,
                    config.get("page_source", "")
                )
                healed_tests.append(healing_result)
            
            healed_count = sum(1 for t in healed_tests if t.get("healed"))
            results["stages"]["self_healing"] = {
                "total_failures": len(test_failures),
                "successfully_healed": healed_count,
                "heal_rate": f"{(healed_count/len(test_failures)*100):.1f}%",
                "details": healed_tests
            }
            print(f"   ✓ Auto-healed {healed_count}/{len(test_failures)} broken tests")
        
        # STAGE 4: Visual Regression Testing
        print("\n👁️ Stage 4: Visual Regression Testing...")
        screenshots = config.get("screenshots", {})
        if screenshots:
            visual_results = self.visual_tester.batch_visual_regression(screenshots)
            results["stages"]["visual_regression"] = visual_results
            print(f"   ✓ Tested {visual_results['summary']['total_pages_tested']} pages")
            print(f"   ✓ {visual_results['summary']['pages_with_changes']} pages with changes")
        
        # STAGE 5: Performance Analysis
        print("\n⚡ Stage 5: Performance Analysis...")
        performance_metrics = config.get("performance_metrics", [])
        if performance_metrics:
            for metric in performance_metrics:
                self.performance_ai.track_performance(
                    metric["test_name"],
                    metric["metrics"]
                )
            
            perf_analysis = self.performance_ai.analyze_performance()
            results["stages"]["performance"] = perf_analysis
            print(f"   ✓ Performance score: {perf_analysis.get('performance_score', 'N/A')}")
            if perf_analysis.get("bottlenecks"):
                print(f"   ⚠ Found {len(perf_analysis['bottlenecks'])} bottlenecks")
        
        # STAGE 6: Security Testing
        print("\n🔒 Stage 6: Advanced Security Testing...")
        endpoints = config.get("api_endpoints", [])
        all_security_tests = []
        for endpoint in endpoints:
            security_tests = self.security_ai.generate_security_tests(
                endpoint["path"],
                endpoint["method"]
            )
            all_security_tests.extend(security_tests)
        
        if all_security_tests:
            results["stages"]["security"] = {
                "total_tests_generated": len(all_security_tests),
                "critical_tests": sum(1 for t in all_security_tests if t.get("severity") == "critical"),
                "tests": all_security_tests
            }
            print(f"   ✓ Generated {len(all_security_tests)} advanced security tests")
        
        # Final Summary
        results["overall_status"] = "completed"
        results["summary"] = self._generate_summary(results)
        
        return results
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate executive summary"""
        stages = results.get("stages", {})
        
        summary = {
            "ai_techniques_used": len(stages),
            "highlights": []
        }
        
        # Predictive selection savings
        if "predictive_selection" in stages:
            savings = stages["predictive_selection"].get("estimated_time_savings", "0%")
            summary["highlights"].append(f"Predictive selection saved {savings} testing time")
        
        # Self-healing success rate
        if "self_healing" in stages:
            heal_rate = stages["self_healing"].get("heal_rate", "0%")
            summary["highlights"].append(f"Self-healing fixed {heal_rate} of broken tests")
        
        # Visual regression findings
        if "visual_regression" in stages:
            changes = stages["visual_regression"]["summary"]["pages_with_changes"]
            if changes > 0:
                summary["highlights"].append(f"Visual regression detected {changes} UI changes")
        
        # Performance issues
        if "performance" in stages:
            bottlenecks = stages["performance"].get("bottlenecks", [])
            if bottlenecks:
                summary["highlights"].append(f"Performance AI found {len(bottlenecks)} bottlenecks")
        
        # Security tests
        if "security" in stages:
            critical = stages["security"].get("critical_tests", 0)
            summary["highlights"].append(f"Security AI generated {critical} critical security tests")
        
        return summary


# Example Usage
if __name__ == "__main__":
    orchestrator = AdvancedAITestOrchestrator()
    
    # Configure test run
    config = {
        "changed_files": [
            "backend/controllers/segment_controller.py",
            "frontend/components/SegmentList.tsx"
        ],
        "test_data_count": 100,
        "specialties": ["Cardiology", "Oncology", "Primary Care"],
        "states": ["California", "New York", "Texas"],
        "test_failures": [
            {
                "test_name": "Create segment test",
                "failed_step": {"action": "click", "selector": "#create-btn"},
                "error": "Element not found",
                "url": "https://app.example.com/segments"
            }
        ],
        "screenshots": {
            "segments_page": ("baseline/segments.png", "current/segments.png")
        },
        "performance_metrics": [
            {
                "test_name": "Segment list load",
                "metrics": {"page_load_ms": 3500, "api_time_ms": 2100}
            }
        ],
        "api_endpoints": [
            {"path": "/api/v1/segments", "method": "POST"},
            {"path": "/api/v1/hcps/export", "method": "GET"}
        ]
    }
    
    # Run complete AI-powered test suite
    print("\n" + "="*80)
    print("ADVANCED AI TESTING SYSTEM - FULL RUN")
    print("="*80)
    
    results = orchestrator.run_smart_test_suite(config)
    
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(json.dumps(results["summary"], indent=2))
    
    print("\n✅ AI-Powered Testing Complete!")
    print(f"   Stages completed: {len(results['stages'])}/6")
    for highlight in results["summary"]["highlights"]:
        print(f"   • {highlight}")
