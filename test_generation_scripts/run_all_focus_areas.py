"""
Run test generation for all modules and focus areas
Generates 100+ test cases per module using module config
Usage:
  python run_all_focus_areas.py                  → Generate for ALL modules
  python run_all_focus_areas.py login            → Generate for Login only
  python run_all_focus_areas.py hcp_search       → Generate for HCP Search only
"""
import os
import sys
import subprocess
import json
from ai_agent.agents.designer import DesignerAgent

BASE_PATH = "C:\\Users\\mv\\Targeting_and_Segmentation_AI"
CONFIG_FILE = "test_generation_scripts/modules_config.json"

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def run_generation(module_id, module_name, focus_area, ui_data):
    """Run test generation for a specific module + focus area"""
    cmd = (
        f'$env:PYTHONPATH = "{BASE_PATH}"; '
        f'python test_generation_scripts\\generate_all_login_tests.py '
        f'{focus_area} "{module_id}" '
    )
    result = subprocess.run(
        ["powershell", "-Command", cmd],
        capture_output=True,
        text=True,
        cwd=BASE_PATH
    )
    if result.returncode == 0:
        print(f"   [OK] {focus_area}")
        return True
    else:
        print(f"   [ERROR] {focus_area}: {result.stderr[:200]}")
        return False

def merge_and_export(module_id, module_name, focus_areas):
    """Merge all focus area JSONs for a module into one Excel"""
    merged_test_cases = []
    
    for focus in focus_areas:
        json_file = f"outputs/{module_id}_{focus}.json"
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                data = json.load(f)
                test_cases = data.get("test_cases", [])
                for tc in test_cases:
                    tc['focus_area'] = focus
                merged_test_cases.extend(test_cases)

    if not merged_test_cases:
        print(f"   [WARN] No test cases found to merge for {module_name}")
        return 0

    # Save merged JSON
    os.makedirs("outputs", exist_ok=True)
    merged_json = f"outputs/{module_id}_COMPLETE.json"
    with open(merged_json, 'w') as f:
        json.dump({"module": module_name, "test_cases": merged_test_cases,
                   "summary": {"total": len(merged_test_cases),
                               "by_focus": {fa: len([tc for tc in merged_test_cases if tc.get('focus_area') == fa]) for fa in focus_areas}}
                   }, f, indent=2)

    # Export to Excel
    os.makedirs("Testcases", exist_ok=True)
    excel_file = f"Testcases/{module_id}_test_cases.xlsx"
    designer = DesignerAgent()
    designer.export_to_excel(merged_test_cases, excel_file)

    # Cleanup intermediate JSON files
    for focus in focus_areas:
        json_file = f"outputs/{module_id}_{focus}.json"
        if os.path.exists(json_file):
            os.remove(json_file)

    print(f"   [OK] Merged {len(merged_test_cases)} test cases")
    print(f"   [OK] Excel: {excel_file}")
    return len(merged_test_cases)

def generate_for_module(module_config, config):
    """Generate all test cases for a single module"""
    module_id = module_config['module_id']
    module_name = module_config['name']
    focus_areas = module_config['focus_areas']
    ui_data = module_config['ui_data']

    print(f"\n{'='*80}")
    print(f"MODULE: {module_name}")
    print(f"Focus Areas: {len(focus_areas)} | Expected: ~{len(focus_areas) * 15}+ test cases")
    print('='*80)

    # Inject focus instructions into ui_data
    focus_instructions = config.get("focus_area_instructions", {})
    ui_data['focus_instructions'] = {fa: focus_instructions.get(fa, fa) for fa in focus_areas}

    # Save ui_data temp file for subprocess to read
    temp_file = f"outputs/temp_{module_id}_ui.json"
    os.makedirs("outputs", exist_ok=True)
    with open(temp_file, 'w') as f:
        json.dump(ui_data, f)

    # Run generation for each focus area
    success = 0
    for focus in focus_areas:
        run_generation(module_id, module_name, focus, ui_data)
        # Check if output file was created
        if os.path.exists(f"outputs/{module_id}_{focus}.json"):
            success += 1

    # Remove temp file
    if os.path.exists(temp_file):
        os.remove(temp_file)

    # Merge all focus areas into one Excel
    total = merge_and_export(module_id, module_name, focus_areas)
    return total

def main():
    config = load_config()
    modules = config['modules']

    # Filter by module_id if provided as argument
    target_module = sys.argv[1] if len(sys.argv) > 1 else None
    if target_module:
        modules = [m for m in modules if m['module_id'] == target_module]
        if not modules:
            print(f"[ERROR] Module '{target_module}' not found in config")
            print(f"Available modules: {[m['module_id'] for m in config['modules']]}")
            return

    print("="*80)
    print("COMPREHENSIVE TEST CASE GENERATION - MODULE BASED")
    print("="*80)
    print(f"\nModules to process: {[m['name'] for m in modules]}")

    # Clear cache
    subprocess.run(["powershell", "-Command",
                    "Remove-Item -Path '.cache' -Recurse -Force -ErrorAction SilentlyContinue"],
                   capture_output=True)

    summary = {}
    for module_config in modules:
        total = generate_for_module(module_config, config)
        summary[module_config['name']] = total

    print(f"\n{'='*80}")
    print("ALL MODULES COMPLETE!")
    print('='*80)
    for module_name, total in summary.items():
        print(f"  {module_name}: {total} test cases | Testcases/{module_name.lower().replace(' ', '_')}_test_cases.xlsx")
    print(f"\nTotal: {sum(summary.values())} test cases across {len(summary)} modules")

if __name__ == "__main__":
    main()


def run_generation(focus_area):
    """Run test generation for a specific focus area"""
    print(f"\n{'='*80}")
    print(f"Generating Test Cases - Focus: {focus_area.upper()}")
    print('='*80)
    
    cmd = f'$env:PYTHONPATH = "C:\\Users\\mv\\Targeting_and_Segmentation_AI"; python test_generation_scripts\\generate_all_login_tests.py {focus_area}'
    
    result = subprocess.run(
        ["powershell", "-Command", cmd],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"[OK] {focus_area.capitalize()} test cases generated")
        return True
    else:
        print(f"[ERROR] Failed to generate {focus_area} test cases")
        print(result.stderr)
        return False

def merge_excel_files():
    """Merge all 3 Excel files into one comprehensive file"""
    print(f"\n{'='*80}")
    print("Merging All Test Cases into One Excel File")
    print('='*80)
    
    focus_areas = ["authentication", "security", "ux"]
    merged_test_cases = []
    
    # Load all JSON files and merge
    for focus in focus_areas:
        json_file = f"outputs/all_login_test_cases_{focus}.json"
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                data = json.load(f)
                test_cases = data.get("test_cases", [])
                # Add focus area tag to each test case
                for tc in test_cases:
                    tc['focus_area'] = focus
                merged_test_cases.extend(test_cases)
                print(f"   [OK] Loaded {len(test_cases)} test cases from {focus}")
    
    # Save merged JSON
    merged_json = "outputs/all_login_test_cases_COMPLETE.json"
    with open(merged_json, 'w') as f:
        json.dump({
            "test_cases": merged_test_cases,
            "summary": {
                "total_test_cases": len(merged_test_cases),
                "authentication": len([tc for tc in merged_test_cases if tc.get('focus_area') == 'authentication']),
                "security": len([tc for tc in merged_test_cases if tc.get('focus_area') == 'security']),
                "ux": len([tc for tc in merged_test_cases if tc.get('focus_area') == 'ux'])
            }
        }, f, indent=2)
    
    # Export to Excel
    from ai_agent.agents.designer import DesignerAgent
    designer = DesignerAgent()
    excel_file = "Testcases/all_login_test_cases_COMPLETE.xlsx"
    designer.export_to_excel(merged_test_cases, excel_file)
    
    print(f"\n   [OK] Merged {len(merged_test_cases)} total test cases")
    print(f"   [OK] JSON saved to: {merged_json}")
    print(f"   [OK] Excel saved to: {excel_file}")
    
    return len(merged_test_cases)

def main():
    print("="*80)
    print("COMPREHENSIVE TEST CASE GENERATION - 3 FOCUS AREAS")
    print("="*80)
    print("\nThis will generate 30-45 test cases by running 3 focused generations:")
    print("  1. Authentication (login, sessions, passwords)")
    print("  2. Security (SQL injection, XSS, CSRF)")
    print("  3. UX (browser behaviors, navigation, validation)")
    print()
    
    # Clear cache to get fresh results
    subprocess.run(["powershell", "-Command", "Remove-Item -Path '.cache' -Recurse -Force -ErrorAction SilentlyContinue"], capture_output=True)
    
    # Run 3 focused generations
    focus_areas = ["authentication", "security", "ux"]
    success_count = 0
    
    for focus in focus_areas:
        if run_generation(focus):
            success_count += 1
    
    # Merge results
    if success_count == 3:
        total_tests = merge_excel_files()
        
        print(f"\n{'='*80}")
        print("GENERATION COMPLETE!")
        print('='*80)
        print(f"\nTotal Test Cases Generated: {total_tests}")
        print(f"  - Authentication Focus: ~{total_tests//3}")
        print(f"  - Security Focus: ~{total_tests//3}")
        print(f"  - UX Focus: ~{total_tests//3}")
        print(f"\nFinal Output: Testcases/all_login_test_cases_COMPLETE.xlsx")
    else:
        print(f"\n[WARNING] Only {success_count}/3 focus areas completed successfully")

if __name__ == "__main__":
    main()
