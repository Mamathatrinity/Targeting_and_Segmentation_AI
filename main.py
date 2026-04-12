"""
Main Entry Point - AI Testing Agent System
Multi-agent architecture with LangChain + LangGraph + Langfuse
"""
import argparse
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add ai_agent to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_agent'))

from ai_agent.config import AIConfig
from ai_agent.graph.workflow import run_workflow, run_multi_module_workflow
from ai_agent.graph.enhanced_workflow import run_enhanced_workflow, run_enhanced_multi_module_workflow
from ai_agent.config_loader import get_config
from ai_agent.cost_tracker import get_cost_tracker


def setup_langfuse():
    """Setup Langfuse observability (optional)"""
    try:
        from langfuse import Langfuse
        
        if AIConfig.LANGFUSE_PUBLIC_KEY and AIConfig.LANGFUSE_SECRET_KEY:
            langfuse = Langfuse(
                public_key=AIConfig.LANGFUSE_PUBLIC_KEY,
                secret_key=AIConfig.LANGFUSE_SECRET_KEY,
                host=AIConfig.LANGFUSE_HOST
            )
            print("✓ Langfuse observability enabled")
            return langfuse
    except ImportError:
        print("⚠ Langfuse not installed - observability disabled")
    except Exception as e:
        print(f"⚠ Langfuse setup failed: {e}")
    
    return None


def save_results(results: dict, output_dir: str = "reports"):
    """Save workflow results to file"""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ai_test_results_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✓ Results saved to: {filepath}")
    return filepath


def print_summary(results: dict):
    """Print execution summary"""
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    # Check if multi-module results
    if "modules" in results:
        # Multi-module summary
        summary = results.get("summary", {})
        print(f"\n📊 Multi-Module Execution:")
        print(f"  Total Modules: {summary.get('total_modules', 0)}")
        print(f"  Completed: {summary.get('completed', 0)}")
        print(f"  Failed: {summary.get('failed', 0)}")
        print(f"\n  Total Tests: {summary.get('total_tests', 0)}")
        print(f"  Passed: {summary.get('total_passed', 0)}")
        print(f"  Failed: {summary.get('total_failed', 0)}")
        print(f"  Overall Pass Rate: {summary.get('overall_pass_rate', '0%')}")
        
        # Module breakdown
        print(f"\n📦 Module Results:")
        for module in results.get("modules", []):
            status_icon = "✓" if module.get("status") == "complete" else "❌"
            print(f"  {status_icon} {module.get('name', 'Unknown')}")
            if module.get("error"):
                print(f"    Error: {module['error']}")
    
    else:
        # Single module summary
        exec_summary = results.get("execution_results", {}).get("summary", {})
        print(f"\n📊 Test Execution:")
        print(f"  Total Tests: {exec_summary.get('total_tests', 0)}")
        print(f"  Passed: {exec_summary.get('passed', 0)}")
        print(f"  Failed: {exec_summary.get('failed', 0)}")
        print(f"  Pass Rate: {exec_summary.get('pass_rate', '0%')}")
        print(f"  Duration: {exec_summary.get('total_duration_ms', 0)}ms")
        
        # AI Analysis
        analysis = results.get("validation_analysis", {})
        print(f"\n🤖 AI Analysis:")
        print(f"  Status: {analysis.get('status', 'unknown')}")
        print(f"  Confidence: {analysis.get('confidence', 'unknown')}")
        
        if analysis.get("root_causes"):
            print(f"\n  Root Causes:")
            for cause in analysis["root_causes"]:
                print(f"    - {cause}")
        
        if analysis.get("recommendations"):
            print(f"\n  Recommendations:")
            for rec in analysis["recommendations"]:
                print(f"    - {rec}")
    
    print("\n" + "="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI-powered testing agent with multi-agent architecture"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Target URL to test (overrides config file)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports",
        help="Output directory for results (default: reports)"
    )
    parser.add_argument(
        "--no-langfuse",
        action="store_true",
        help="Disable Langfuse observability"
    )
    parser.add_argument(
        "--single-module",
        action="store_true",
        help="Run single module mode (ignore config modules)"
    )
    parser.add_argument(
        "--enhanced",
        action="store_true",
        help="Use enhanced workflow with Strategy, Decision, Coverage, and Reporting"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("AI TESTING AGENT - Multi-Agent System")
    print("="*60)
    print(f"Architecture: LangChain + LangGraph + Azure GPT-4o")
    
    # Get cost tracker
    cost_tracker = get_cost_tracker()
    
    try:
        # Validate configuration
        AIConfig.validate()
        print("✓ Configuration validated")
        
        # Load YAML config
        config = get_config(args.config if os.path.exists(args.config) else None)
        
        # Determine execution mode
        if args.url:
            # Single URL mode (CLI override)
            print(f"Mode: Single URL")
            print(f"Target URL: {args.url}")
            print("="*60)
            
            # Setup Langfuse (optional)
            if not args.no_langfuse:
                langfuse = setup_langfuse()
            
            # Run workflow (enhanced or standard)
            if args.enhanced:
                print("\nStarting ENHANCED workflow...\n")
                results = run_enhanced_workflow(args.url, module_name="test")
            else:
                print("\nStarting workflow...\n")
                results = run_workflow(args.url)
            
        elif config.get_modules() and not args.single_module:
            # Multi-module mode from config
            modules = config.get_modules()
            base_url = config.get_base_url()
            
            print(f"Mode: Multi-Module")
            print(f"Modules: {len(modules)}")
            print(f"Base URL: {base_url}")
            print("="*60)
            
            # Setup Langfuse (optional)
            if not args.no_langfuse and config.is_langfuse_enabled():
                langfuse = setup_langfuse()
            
            # Run multi-module workflow (enhanced or standard)
            if args.enhanced:
                print("\nStarting ENHANCED multi-module workflow...\n")
                results = run_enhanced_multi_module_workflow(modules, base_url)
            else:
                print("\nStarting multi-module workflow...\n")
                results = run_multi_module_workflow(modules, base_url)
            
        else:
            print("\n❌ Error: No URL provided and no modules in config file")
            print("\nUsage:")
            print("  python main.py --url https://example.com")
            print("  python main.py --config config.yaml")
            return 1
        
        # Print summary
        print_summary(results)
        
        # Print cost summary
        cost_tracker.print_summary()
        
        # Save results
        output_file = save_results(results, args.output)
        
        # Exit code based on test results
        if "modules" in results:
            # Multi-module: check overall results
            failed = results.get("summary", {}).get("total_failed", 0)
        else:
            # Single module
            summary = results.get("execution_results", {}).get("summary", {})
            failed = summary.get("failed", 0)
        
        if failed > 0:
            print(f"\n⚠ {failed} test(s) failed")
            return 1
        else:
            print("\n✓ All tests passed!")
            return 0
    
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        return 130
    
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("   Check your .env file and config.yaml")
        print("   Run: python -m ai_agent.health_check")
        return 1
    
    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("   Check your network and Azure endpoint")
        return 1
    
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        print("\nFor detailed diagnosis, run:")
        print("  python -m ai_agent.health_check")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
