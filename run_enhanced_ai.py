"""
run_enhanced_ai.py
==================
Main entry point that wires together all 4 AI features:

  1. RAG Store         – domain knowledge for CE-TS modules (loaded once)
  2. Merged Agents     – Planner+Strategy (1 call) & Validator+Decision (1 call)
  3. LangGraph Retry   – generate → execute → check → fix → retry (max 1)
  4. Selector Healing  – auto-fix broken CSS selectors using GPT-4o + DOM

Usage:
    python run_enhanced_ai.py                          # interactive menu
    python run_enhanced_ai.py --module segmentation    # run specific module
    python run_enhanced_ai.py --module login           # run login module
    python run_enhanced_ai.py --all                    # run all CE-TS modules
"""

import argparse
import json
import sys
import os
from datetime import datetime

# Ensure project root is in path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# ── App constants ────────────────────────────────────────────────────────────
BASE_URL = "https://ce-ts-dev.trinitylifesciences.com"

CE_TS_MODULES = [
    {
        "name": "login",
        "url": f"{BASE_URL}/",
        "description": "Microsoft SSO login, MFA, session management",
        "complex": False,
    },
    {
        "name": "segmentation",
        "url": f"{BASE_URL}/segmentation",
        "description": "Segment creation, rule builder, AND/OR logic, save/preview",
        "complex": True,
    },
    {
        "name": "universe_summary",
        "url": f"{BASE_URL}/universe-summary",
        "description": "HCP universe dashboard, filters, KPI cards, export",
        "complex": True,
    },
    {
        "name": "target_lists",
        "url": f"{BASE_URL}/target-lists",
        "description": "Target list management, CSV upload, archive, assign territory",
        "complex": True,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          CE-TS AI Testing Suite – Enhanced Mode              ║
║  Features: RAG + Merged Agents + LangGraph + Selector Heal   ║
╚══════════════════════════════════════════════════════════════╝
""")


def print_section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ─────────────────────────────────────────────────────────────────────────────
def warm_up_rag():
    """Pre-load FAISS index so it's ready before tests run."""
    print_section("Step 1/4 — RAG Store Warm-up")
    from ai_agent.rag.rag_store import get_rag_store
    rag = get_rag_store()

    for module in ["segmentation", "target_lists", "universe_summary"]:
        ctx = rag.get_context(module, k=2)
        status = "✅" if ctx else "⚠️ "
        print(f"  {status} {module}: {len(ctx)} chars of domain context loaded")

    print("  ✅ RAG store ready")
    return rag


# ─────────────────────────────────────────────────────────────────────────────
def run_module(module: dict, previous_failures: list = None) -> dict:
    """Run the full retry workflow for one module."""
    from ai_agent.graph.retry_workflow import run_retry_workflow

    print_section(f"Running Module: {module['name'].upper()}")
    print(f"  URL: {module['url']}")
    print(f"  RAG enabled: {module['complex']}")

    result = run_retry_workflow(
        url=module["url"],
        module_name=module["name"],
        business_context=module["description"],
        previous_failures=previous_failures or [],
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
def save_report(results: list, output_dir: str = "outputs"):
    """Save final JSON report to disk."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"enhanced_ai_report_{timestamp}.json")

    full_report = {
        "generated_at": datetime.now().isoformat(),
        "features_used": [
            "RAG (FAISS CE-TS knowledge base)",
            "Merged Planner+Strategy (1 LLM call)",
            "Merged Validator+Decision (1 LLM call)",
            "LangGraph Retry Workflow (max 1 retry)",
            "AI Selector Healing (GPT-4o + DOM snapshot)",
        ],
        "modules": results,
        "aggregate": {
            "total_modules": len(results),
            "total_tests": sum(r.get("test_summary", {}).get("total", 0) for r in results),
            "total_passed": sum(r.get("test_summary", {}).get("passed", 0) for r in results),
            "total_failed": sum(r.get("test_summary", {}).get("failed", 0) for r in results),
            "retries_performed": sum(1 for r in results if r.get("retry", {}).get("performed")),
            "selectors_healed": sum(
                len(r.get("retry", {}).get("healed_selectors", {})) for r in results
            ),
        },
    }

    total = full_report["aggregate"]["total_tests"]
    passed = full_report["aggregate"]["total_passed"]
    full_report["aggregate"]["overall_pass_rate"] = (
        f"{(passed/total*100):.1f}%" if total > 0 else "0%"
    )

    with open(report_path, "w") as f:
        json.dump(full_report, f, indent=2, default=str)

    print(f"\n  📄 Report saved: {report_path}")
    return report_path, full_report


# ─────────────────────────────────────────────────────────────────────────────
def print_summary(full_report: dict):
    agg = full_report.get("aggregate", {})
    print(f"""
╔══════════════════════════════════════════════════╗
║                 FINAL SUMMARY                    ║
╠══════════════════════════════════════════════════╣
║  Modules tested:    {agg.get('total_modules', 0):<28}║
║  Total tests:       {agg.get('total_tests', 0):<28}║
║  Passed:            {agg.get('total_passed', 0):<28}║
║  Failed:            {agg.get('total_failed', 0):<28}║
║  Pass rate:         {agg.get('overall_pass_rate', '0%'):<28}║
║  Retries triggered: {agg.get('retries_performed', 0):<28}║
║  Selectors healed:  {agg.get('selectors_healed', 0):<28}║
╚══════════════════════════════════════════════════╝""")


# ─────────────────────────────────────────────────────────────────────────────
def interactive_menu():
    print_banner()
    print("Select option:")
    print("  1) Run single module")
    print("  2) Run all CE-TS modules")
    print("  3) RAG smoke test only")
    print("  4) Selector healer demo")
    print("  q) Quit")
    choice = input("\n> ").strip()

    if choice == "1":
        print("\nAvailable modules:")
        for i, m in enumerate(CE_TS_MODULES, 1):
            print(f"  {i}) {m['name']}")
        idx = int(input("Select module number: ").strip()) - 1
        if 0 <= idx < len(CE_TS_MODULES):
            warm_up_rag()
            result = run_module(CE_TS_MODULES[idx])
            _, report = save_report([result])
            print_summary(report)

    elif choice == "2":
        warm_up_rag()
        results = []
        failures_so_far = []
        for module in CE_TS_MODULES:
            r = run_module(module, previous_failures=failures_so_far)
            results.append(r)
            # Feed failures into next module's strategy context
            new_fails = [
                t["test_name"] for t in r.get("test_results", [])
                if t.get("status") == "failed"
            ]
            failures_so_far.extend(new_fails)
        _, report = save_report(results)
        print_summary(report)

    elif choice == "3":
        warm_up_rag()
        print("\n✅ RAG smoke test complete")

    elif choice == "4":
        _selector_healer_demo()

    elif choice.lower() == "q":
        print("Bye!")
        sys.exit(0)
    else:
        print("Invalid choice")


# ─────────────────────────────────────────────────────────────────────────────
def _selector_healer_demo():
    from ai_agent.tools.selector_healer import SelectorHealer
    healer = SelectorHealer()

    sample_html = """
    <html><body>
      <nav>
        <button data-testid="nav-segments" aria-label="Go to Segments">Segments</button>
        <button data-testid="add-rule" class="btn-primary">Add Rule</button>
        <input id="segment-name" placeholder="Segment Name" />
      </nav>
    </body></html>
    """

    tests = [
        ("#old-segments-btn",  "Segments navigation button"),
        ("#add-rule-button",   "Button to add a new rule in segment builder"),
        ("#segment-name-input","Segment name text input field"),
    ]

    print_section("Selector Healer Demo")
    for broken, context in tests:
        result = healer.heal(
            failed_selector=broken,
            page_html=sample_html,
            element_context=context,
        )
        print(f"\n  Broken:   {broken}")
        print(f"  Healed:   {result.get('new_selector', 'N/A')}")
        print(f"  Confidence: {result.get('confidence', 0)}")
        print(f"  Reasoning:  {result.get('reasoning', '')}")


# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="CE-TS Enhanced AI Test Runner")
    parser.add_argument("--module", help="Module name to test (login/segmentation/etc.)")
    parser.add_argument("--all", action="store_true", help="Run all CE-TS modules")
    parser.add_argument("--rag-only", action="store_true", help="Just warm up and test RAG")
    args = parser.parse_args()

    print_banner()

    if args.rag_only:
        warm_up_rag()
        return

    if args.module:
        module = next((m for m in CE_TS_MODULES if m["name"] == args.module), None)
        if not module:
            print(f"❌ Unknown module: {args.module}")
            print(f"   Available: {', '.join(m['name'] for m in CE_TS_MODULES)}")
            sys.exit(1)
        warm_up_rag()
        result = run_module(module)
        _, report = save_report([result])
        print_summary(report)
        return

    if args.all:
        warm_up_rag()
        results = []
        failures_so_far = []
        for module in CE_TS_MODULES:
            r = run_module(module, previous_failures=failures_so_far)
            results.append(r)
            failures_so_far.extend(
                t["test_name"] for t in r.get("test_results", []) if t.get("status") == "failed"
            )
        _, report = save_report(results)
        print_summary(report)
        return

    # No args → interactive menu
    interactive_menu()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
