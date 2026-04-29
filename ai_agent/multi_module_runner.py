"""
Multi-Module Test Execution Runner
Runs AI testing across all HCP modules in one automated flow
Based on PDF recommendations (Page 282-283)
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Import agents
from ai_agent.agents.planner import generate_scenarios
from ai_agent.agents.designer import design_tests
from ai_agent.agents.validator import validate_results
from ai_agent.agents.failure_analyzer import analyze_failures

# Import tools
from ai_agent.tools.ui_extractor import extract_ui_data
from ai_agent.tools.executor import execute_tests

# Import utils
from ai_agent.utils.prompt_loader import load_module_contexts, load_yaml_config
from ai_agent.utils.cache import get_cache_stats, clear_cache
from ai_agent.langfuse_tracker import tracker


class MultiModuleRunner:
    """Execute AI testing across all application modules"""
    
    def __init__(self, base_url: str, modules_config: str = "config/modules.yaml"):
        """
        Initialize multi-module runner
        
        Args:
            base_url: Base URL of the application
            modules_config: Path to modules configuration file
        """
        self.base_url = base_url
        self.modules = self._load_modules(modules_config)
        self.results = []
    
    def _load_modules(self, config_path: str) -> List[Dict[str, str]]:
        """
        Load module configuration
        
        Args:
            config_path: Path to modules YAML config
            
        Returns:
            List of module dictionaries with name, context, and url
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            # Return default HCP modules
            return [
                {
                    "name": "Authentication",
                    "context": "Login, SSO, session validation, security",
                    "url": "/login"
                },
                {
                    "name": "Universe Summary",
                    "context": "HCP dashboard, KPIs, charts, filters",
                    "url": "/universe-summary"
                },
                {
                    "name": "Segments List",
                    "context": "HCP segmentation, create/edit segments, filters",
                    "url": "/segments"
                },
                {
                    "name": "Segment Detail",
                    "context": "View segment HCPs, apply filters, export data",
                    "url": "/segments/{id}"
                },
                {
                    "name": "Target List",
                    "context": "Campaign targets, HCP list management",
                    "url": "/targets"
                },
                {
                    "name": "Target List Detail",
                    "context": "Target HCP assignments, bulk import/export",
                    "url": "/targets/{id}"
                }
            ]
        
        config = load_yaml_config(str(config_file))

        if 'modules' in config and isinstance(config['modules'], list):
            return config['modules']
        
        return []
    
    def run_module(self, module: Dict[str, str]) -> Dict[str, Any]:
        """
        Run AI testing for a single module
        
        Args:
            module: Module configuration dictionary
            
        Returns:
            Test results for the module
        """
        module_name = module['name']
        module_context = module['context']
        module_url = self.base_url + module['url']
        
        print(f"\n{'='*80}")
        print(f"MODULE: {module_name}")
        print(f"Context: {module_context}")
        print(f"URL: {module_url}")
        print(f"{'='*80}\n")
        
        result = {
            "module": module_name,
            "context": module_context,
            "url": module_url,
            "timestamp": datetime.now().isoformat(),
            "steps": {},
            "status": "success",
            "error": None
        }
        
        try:
            # Step 1: Extract UI
            print("Step 1: Extracting UI elements...")
            ui_data = extract_ui_data(module_url)
            result['steps']['ui_extraction'] = {
                "status": "completed",
                "elements_found": len(ui_data.get('inputs', [])) + len(ui_data.get('buttons', []))
            }
            print(f"  ✓ Found {result['steps']['ui_extraction']['elements_found']} UI elements")
            
            # Step 2: Generate scenarios
            print("\nStep 2: Generating test scenarios (AI)...")
            scenarios = generate_scenarios(ui_data)
            result['steps']['scenario_generation'] = {
                "status": "completed",
                "scenarios_count": len(scenarios.get('positive', [])) + len(scenarios.get('edge_cases', [])) + len(scenarios.get('negative', []))
            }
            print(f"  ✓ Generated {result['steps']['scenario_generation']['scenarios_count']} scenarios")
            
            # Step 3: Design test steps
            print("\nStep 3: Designing test steps (AI)...")
            test_cases = design_tests(scenarios, ui_data)
            result['steps']['test_design'] = {
                "status": "completed",
                "test_cases": len(test_cases) if isinstance(test_cases, list) else 1
            }
            print(f"  ✓ Designed {result['steps']['test_design']['test_cases']} test cases")
            
            # Step 4: Execute tests
            print("\nStep 4: Executing tests (Playwright + API + DB)...")
            execution_results = execute_tests(test_cases, self.base_url)
            passed = sum(1 for r in execution_results if r.get('status') == 'passed')
            failed = len(execution_results) - passed
            result['steps']['execution'] = {
                "status": "completed",
                "total": len(execution_results),
                "passed": passed,
                "failed": failed
            }
            print(f"  ✓ Executed {len(execution_results)} tests: {passed} passed, {failed} failed")
            
            # Step 5: Validate results (if failures)
            if failed > 0:
                print("\nStep 5: Analyzing failures (AI)...")
                analysis = analyze_failures(module_name, execution_results)
                result['steps']['failure_analysis'] = {
                    "status": "completed",
                    "analysis": analysis
                }
                print(f"  ✓ Failure analysis complete")
                result['status'] = "completed_with_failures"
            else:
                result['status'] = "all_tests_passed"
            
            result['execution_results'] = execution_results
            
        except Exception as e:
            result['status'] = "error"
            result['error'] = str(e)
            print(f"\n  ✗ Error: {e}")
        
        return result
    
    def run_all_modules(self) -> List[Dict[str, Any]]:
        """
        Run AI testing across all modules
        
        Returns:
            List of results for each module
        """
        print(f"\n{'#'*80}")
        print(f"# MULTI-MODULE AI TESTING")
        print(f"# Application: HCP Targeting & Segmentation")
        print(f"# Base URL: {self.base_url}")
        print(f"# Modules: {len(self.modules)}")
        print(f"{'#'*80}\n")
        
        for module in self.modules:
            result = self.run_module(module)
            self.results.append(result)
        
        # Print summary
        self._print_summary()
        
        # Save report
        self._save_report()
        
        return self.results
    
    def _print_summary(self):
        """Print execution summary"""
        print(f"\n{'='*80}")
        print(f"EXECUTION SUMMARY")
        print(f"{'='*80}\n")
        
        total_modules = len(self.results)
        successful = sum(1 for r in self.results if r['status'] in ['success', 'all_tests_passed', 'completed_with_failures'])
        errors = sum(1 for r in self.results if r['status'] == 'error')
        
        total_tests = sum(r['steps'].get('execution', {}).get('total', 0) for r in self.results)
        total_passed = sum(r['steps'].get('execution', {}).get('passed', 0) for r in self.results)
        total_failed = sum(r['steps'].get('execution', {}).get('failed', 0) for r in self.results)
        
        print(f"Modules Executed: {total_modules}")
        print(f"  ✓ Successful: {successful}")
        print(f"  ✗ Errors: {errors}")
        print(f"\nTotal Tests: {total_tests}")
        print(f"  ✓ Passed: {total_passed}")
        print(f"  ✗ Failed: {total_failed}")
        print(f"  Pass Rate: {(total_passed/total_tests*100 if total_tests > 0 else 0):.1f}%")
        
        # Cache statistics
        cache_stats = get_cache_stats()
        print(f"\nCache Statistics:")
        print(f"  Total Entries: {cache_stats['total_entries']}")
        print(f"  Cache Hits: {cache_stats['total_hits']}")
        if cache_stats['total_hits'] > 0:
            savings = cache_stats['total_hits'] / (cache_stats['total_hits'] + total_modules) * 100
            print(f"  Cost Savings: ~{savings:.1f}% (from caching)")
        
        print(f"\n{'='*80}\n")
    
    def _save_report(self):
        """Save execution report to file"""
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"multi_module_report_{timestamp}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "modules_tested": len(self.modules),
            "results": self.results,
            "cache_stats": get_cache_stats()
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved: {report_file}")


def run_multi_module_tests(base_url: str, modules_config: str = "config/modules.yaml"):
    """
    Convenience function to run multi-module testing
    
    Args:
        base_url: Base URL of the application
        modules_config: Path to modules configuration
        
    Returns:
        List of test results
    """
    runner = MultiModuleRunner(base_url, modules_config)
    return runner.run_all_modules()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://ce-ts-dev.trinitylifesciences.com"
    
    print("Starting multi-module AI testing...")
    results = run_multi_module_tests(base_url)
    
    print("\n✅ Multi-module testing complete!")
