"""
Run test generation for all focus areas and merge results
Generates 30-45 test cases total by running 3 separate focused generations
"""
import os
import subprocess
import json
from openpyxl import Workbook, load_workbook

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
