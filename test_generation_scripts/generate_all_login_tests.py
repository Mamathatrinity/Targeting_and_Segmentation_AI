"""
Generate test cases for a specific module + focus area
Called by run_all_focus_areas.py with module_id and focus_area arguments

Usage:
  python generate_all_login_tests.py <focus_area> <module_id>
  e.g. python generate_all_login_tests.py authentication login
  e.g. python generate_all_login_tests.py filters hcp_search
"""
import os
import sys
import json
from ai_agent.agents.planner import PlannerAgent
from ai_agent.agents.designer import DesignerAgent

CONFIG_FILE = "test_generation_scripts/modules_config.json"

def load_module_config(module_id):
    """Load UI data for a specific module from config"""
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    for module in config['modules']:
        if module['module_id'] == module_id:
            return module, config.get('focus_area_instructions', {})
    return None, {}

def main(focus_area=None, module_id="login"):
    # Load UI data from config
    module_config, focus_instructions = load_module_config(module_id)
    
    if module_config:
        ui_data = module_config['ui_data'].copy()
        module_name = module_config['name']
    else:
        # Fallback: default login UI data
        module_name = "Login"
        ui_data = {
            "url": "https://ce-ts-dev.trinitylifesciences.com/login",
            "module": "Login",
            "inputs": [
                {"label": "Email", "type": "email", "placeholder": "Enter email"},
                {"label": "Password", "type": "password", "placeholder": "Enter password"}
            ],
            "buttons": [{"text": "Login", "type": "submit"}],
            "links": [{"text": "Forgot Password?", "href": "/forgot-password"}]
        }

    # Inject focus area into UI data for planner
    ui_data['focus_area'] = focus_area
    if focus_area and focus_area in focus_instructions:
        ui_data['focus_instruction'] = focus_instructions[focus_area]
    
    print("="*80)
    print(f"GENERATING: {module_name} | Focus: {focus_area or 'general'}")
    print("="*80)
    
    # Step 1: Generate scenarios
    print("\n[1/3] Generating test scenarios...")
    planner = PlannerAgent()
    scenarios = planner.generate_scenarios(ui_data)
    
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
        single_scenario = {scenario_type + "_scenarios": [scenario]}
        try:
            test_cases = designer.design_tests(single_scenario, ui_data, max_tests=1)
            if test_cases:
                test_case = test_cases[0]
                test_case['scenario_type'] = scenario_type
                test_case['scenario_text'] = scenario
                all_test_cases.append(test_case)
                print(f"      [OK] Created: {test_case.get('name', 'Unknown')}")
            else:
                print(f"      [WARN] No test case generated")
        except Exception as e:
            print(f"      [ERROR] {str(e)[:100]}")
    
    print(f"\n   [OK] Generated {len(all_test_cases)} test cases")
    
    # Step 3: Save JSON (Excel merged later by run_all_focus_areas.py)
    print("\n[3/3] Saving results...")
    os.makedirs("outputs", exist_ok=True)
    
    json_file = f"outputs/{module_id}_{focus_area}.json" if focus_area else f"outputs/{module_id}_general.json"
    with open(json_file, 'w') as f:
        json.dump({
            "module": module_name,
            "focus_area": focus_area or "general",
            "scenarios": scenarios,
            "test_cases": all_test_cases,
            "summary": {
                "total_scenarios": len(all_scenarios),
                "total_test_cases": len(all_test_cases),
                "positive": len([tc for tc in all_test_cases if tc.get('scenario_type') == 'positive']),
                "edge_cases": len([tc for tc in all_test_cases if tc.get('scenario_type') == 'edge_case']),
                "negative": len([tc for tc in all_test_cases if tc.get('scenario_type') == 'negative'])
            }
        }, f, indent=2)
    
    print(f"   [OK] Saved {len(all_test_cases)} test cases to {json_file}")

if __name__ == "__main__":
    focus_area = sys.argv[1] if len(sys.argv) > 1 else None
    module_id  = sys.argv[2] if len(sys.argv) > 2 else "login"
    main(focus_area, module_id)

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
