"""
Generate test cases for ALL login scenarios
Processes scenarios one by one to ensure all are converted to test cases
"""
import os
import sys
import json
from ai_agent.agents.planner import PlannerAgent
from ai_agent.agents.designer import DesignerAgent

def main(focus_area=None):
    # Login UI data
    login_ui_data = {
        "url": "https://ce-ts-dev.trinitylifesciences.com/login",
        "module": "Login",
        "focus_area": focus_area,  # Pass focus area to planner
        "inputs": [
            {"label": "Email", "type": "email", "placeholder": "Enter email"},
            {"label": "Password", "type": "password", "placeholder": "Enter password"}
        ],
        "buttons": [
            {"text": "Login", "type": "submit"}
        ],
        "links": [
            {"text": "Forgot Password?", "href": "/forgot-password"}
        ]
    }
    
    print("="*80)
    print("GENERATING ALL LOGIN TEST CASES")
    print("="*80)
    
    # Step 1: Generate scenarios
    print("\n[1/3] Generating test scenarios...")
    planner = PlannerAgent()
    scenarios = planner.generate_scenarios(login_ui_data)
    
    # Flatten all scenarios into a list
    all_scenarios = []
    all_scenarios.extend([(s, "positive") for s in scenarios.get("positive_scenarios", [])])
    all_scenarios.extend([(s, "edge_case") for s in scenarios.get("edge_cases", [])])
    all_scenarios.extend([(s, "negative") for s in scenarios.get("negative_scenarios", [])])
    
    print(f"   [OK] Generated {len(all_scenarios)} scenarios")
    
    # Step 2: Convert each scenario to test case
    print("\n[2/3] Converting scenarios to test cases...")
    designer = DesignerAgent()
    all_test_cases = []
    
    for idx, (scenario, scenario_type) in enumerate(all_scenarios, 1):
        print(f"   Processing {idx}/{len(all_scenarios)}: {scenario_type}")
        
        # Convert single scenario
        single_scenario = {
            scenario_type + "_scenarios": [scenario]
        }
        
        try:
            test_cases = designer.design_tests(single_scenario, login_ui_data, max_tests=1)
            if test_cases:
                test_case = test_cases[0]
                # Add metadata
                test_case['scenario_type'] = scenario_type
                test_case['scenario_text'] = scenario
                all_test_cases.append(test_case)
                print(f"      [OK] Created: {test_case.get('name', 'Unknown')}")
            else:
                print(f"      [WARN] No test case generated")
        except Exception as e:
            print(f"      [ERROR] {str(e)}")
    
    print(f"\n   [OK] Generated {len(all_test_cases)} test cases")
    
    # Step 3: Export to Excel and JSON
    print("\n[3/3] Exporting results...")
    
    # Create directories
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("Testcases", exist_ok=True)
    
    # Save JSON
    focus_suffix = f"_{focus_area}" if focus_area else ""
    json_file = f"outputs/all_login_test_cases{focus_suffix}.json"
    with open(json_file, 'w') as f:
        json.dump({
            "scenarios": scenarios,
            "test_cases": all_test_cases,
            "summary": {
                "focus_area": focus_area or "general",
                "total_scenarios": len(all_scenarios),
                "total_test_cases": len(all_test_cases),
                "positive": len([tc for tc in all_test_cases if tc.get('scenario_type') == 'positive']),
                "edge_cases": len([tc for tc in all_test_cases if tc.get('scenario_type') == 'edge_case']),
                "negative": len([tc for tc in all_test_cases if tc.get('scenario_type') == 'negative'])
            }
        }, f, indent=2)
    
    # Export to Excel
    excel_file = f"Testcases/all_login_test_cases{focus_suffix}.xlsx"
    designer.export_to_excel(all_test_cases, excel_file)
    
    print(f"\n   [OK] JSON saved to: {json_file}")
    print(f"   [OK] Excel saved to: {excel_file}")
    
    # Final summary
    print("\n" + "="*80)
    print("GENERATION COMPLETE!")
    print("="*80)
    print(f"\nResults:")
    print(f"   - Total Scenarios: {len(all_scenarios)}")
    print(f"   - Test Cases Generated: {len(all_test_cases)}")
    print(f"   - Positive: {len([tc for tc in all_test_cases if tc.get('scenario_type') == 'positive'])}")
    print(f"   - Edge Cases: {len([tc for tc in all_test_cases if tc.get('scenario_type') == 'edge_case'])}")
    print(f"   - Negative: {len([tc for tc in all_test_cases if tc.get('scenario_type') == 'negative'])}")
    print(f"   - Total Steps: {sum(len(tc.get('steps', [])) for tc in all_test_cases)}")

if __name__ == "__main__":
    # Check if focus area is provided as command line argument
    focus_area = sys.argv[1] if len(sys.argv) > 1 else None
    main(focus_area)
