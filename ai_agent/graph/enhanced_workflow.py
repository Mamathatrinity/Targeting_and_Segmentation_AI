"""
Enhanced Workflow with Strategy, Decision, Coverage, and Reporting
Integrates all 4 intelligence layers without complexity
"""

from typing import Dict, Any, List
from ai_agent.agents.strategy import StrategyAgent
from ai_agent.agents.decision_engine import DecisionEngine
from ai_agent.agents.coverage_analyzer import CoverageAnalyzer
from ai_agent.agents.cross_layer_validator import CrossLayerValidator
from ai_agent.agents.report_generator import ReportGenerator
from ai_agent.graph.workflow import run_workflow as original_workflow


def run_enhanced_workflow(url: str, module_name: str = "test", business_context: str = "", previous_failures: List[str] = None) -> Dict[str, Any]:
    """
    Enhanced workflow with 4 intelligence layers:
    1. Strategy - decide what to test
    2. Decision - prioritize tests
    3. Coverage - find gaps
    4. Reporting - comprehensive output
    """
    
    print(f"\n{'='*60}")
    print(f"ENHANCED WORKFLOW - {module_name.upper()}")
    print(f"{'='*60}\n")
    
    # Initialize components
    from ai_agent.config import AIConfig
    config = {
        "azure_deployment": AIConfig.AZURE_DEPLOYMENT,
        "api_version": AIConfig.API_VERSION
    }
    
    strategy_agent = StrategyAgent(config)
    decision_engine = DecisionEngine()
    coverage_analyzer = CoverageAnalyzer()
    cross_layer_validator = CrossLayerValidator()
    report_generator = ReportGenerator()
    
    # STEP 1: Strategy - Decide testing approach
    print("🧠 Step 1: Strategy Planning...")
    strategy = strategy_agent.decide_strategy(
        module=module_name,
        business_context=business_context,
        previous_failures=previous_failures
    )
    
    print(f"   Priority: {strategy.priority.upper()}")
    print(f"   Depth: {strategy.depth}")
    print(f"   Focus: {', '.join(strategy.focus_areas[:3])}")
    print(f"   Rationale: {strategy.rationale}\n")
    
    # STEP 2: Run original workflow (test generation + execution)
    print("⚙️  Step 2: Executing Tests...")
    original_results = original_workflow(url)
    print()
    
    # Extract test cases for analysis
    test_cases = original_results.get("test_plan", {}).get("test_cases", [])
    execution_results = original_results.get("execution_results", {}).get("detailed_results", [])
    
    # STEP 3: Decision Engine - Prioritize (for next run)
    print("🎯 Step 3: Test Prioritization...")
    decisions = decision_engine.prioritize_tests(test_cases, module_name)
    execution_plan = decision_engine.get_execution_plan(decisions)
    print(f"   Tests to run: {execution_plan['to_run']}/{execution_plan['total_tests']}")
    print(f"   Estimated time: {execution_plan['estimated_time_minutes']} minutes\n")
    
    # STEP 4: Coverage Analysis - Find gaps
    print("📊 Step 4: Coverage Analysis...")
    coverage = coverage_analyzer.analyze_coverage(module_name, test_cases)
    print(f"   Coverage: {coverage['coverage_percentage']}%")
    if coverage['missing_tests']:
        print(f"   Missing: {', '.join(coverage['missing_tests'][:3])}")
    print(f"   {coverage['recommendation']}\n")
    
    # STEP 5: Cross-Layer Validation (if UI, API, DB results available)
    print("🔗 Step 5: Cross-Layer Validation...")
    cross_layer_result = None
    
    # Try to find UI, API, DB results
    ui_result = next((r for r in execution_results if r.get("agent") == "UI"), None)
    api_result = next((r for r in execution_results if r.get("agent") == "API"), None)
    db_result = next((r for r in execution_results if r.get("agent") == "DB"), None)
    
    if ui_result and api_result and db_result:
        cross_layer_result = cross_layer_validator.validate_flow(ui_result, api_result, db_result)
        print(f"   Status: {cross_layer_result['status']}")
        print(f"   {cross_layer_result['summary']}\n")
    else:
        print("   Skipped (need UI + API + DB results)\n")
    
    # STEP 6: Generate Comprehensive Report
    print("📝 Step 6: Generating Report...")
    report = report_generator.generate_report(
        module=module_name,
        strategy=strategy.dict(),
        execution_results=execution_results,
        coverage=coverage,
        cross_layer=cross_layer_result
    )
    
    # Print stakeholder-friendly summary
    print(report_generator.format_for_stakeholders(report))
    
    # Combine all results
    enhanced_results = {
        **original_results,
        "strategy": strategy.dict(),
        "execution_plan": execution_plan,
        "coverage_analysis": coverage,
        "cross_layer_validation": cross_layer_result,
        "comprehensive_report": report
    }
    
    return enhanced_results


def run_enhanced_multi_module_workflow(modules: List[Dict[str, Any]], base_url: str) -> Dict[str, Any]:
    """
    Run enhanced workflow for multiple modules
    """
    
    print(f"\n{'='*60}")
    print(f"ENHANCED MULTI-MODULE WORKFLOW")
    print(f"{'='*60}")
    print(f"Modules: {len(modules)}")
    print(f"Base URL: {base_url}\n")
    
    results = {
        "modules": [],
        "summary": {
            "total_modules": len(modules),
            "completed": 0,
            "failed": 0,
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0,
            "overall_pass_rate": "0%"
        }
    }
    
    # Track failures for next module
    previous_failures = []
    
    for module in modules:
        module_name = module.get("name", "unknown")
        module_url = f"{base_url}{module.get('path', '')}"
        
        print(f"\n{'─'*60}")
        print(f"MODULE: {module_name}")
        print(f"{'─'*60}")
        
        try:
            # Run enhanced workflow
            module_result = run_enhanced_workflow(
                url=module_url,
                module_name=module_name,
                business_context=module.get("business_context", ""),
                previous_failures=previous_failures
            )
            
            # Extract summary
            report = module_result.get("comprehensive_report", {})
            summary = report.get("summary", {})
            
            # Update tracking
            results["summary"]["completed"] += 1
            results["summary"]["total_tests"] += summary.get("total_tests", 0)
            results["summary"]["total_passed"] += summary.get("passed", 0)
            results["summary"]["total_failed"] += summary.get("failed", 0)
            
            # Track failures for learning
            if summary.get("failed", 0) > 0:
                exec_results = module_result.get("execution_results", {}).get("detailed_results", [])
                failed_tests = [r.get("scenario", "") for r in exec_results if r.get("status") == "failed"]
                previous_failures.extend(failed_tests[:3])  # Keep last 3 failures
            
            results["modules"].append({
                "name": module_name,
                "status": "complete",
                "report": report,
                "url": module_url
            })
            
        except Exception as e:
            print(f"❌ Module failed: {str(e)}\n")
            results["summary"]["failed"] += 1
            results["modules"].append({
                "name": module_name,
                "status": "failed",
                "error": str(e),
                "url": module_url
            })
    
    # Calculate overall pass rate
    total_tests = results["summary"]["total_tests"]
    total_passed = results["summary"]["total_passed"]
    
    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
        results["summary"]["overall_pass_rate"] = f"{pass_rate:.1f}%"
    
    return results
