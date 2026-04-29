"""
Designer Agent
Converts test scenarios into executable YAML test steps
"""
from pydantic import BaseModel, Field
from typing import List, Dict
import yaml
import json
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import AIConfig
from langfuse_tracker import get_tracker
from ai_agent.utils.cache import get_cached_response, set_cached_response
from ai_agent.utils.prompt_loader import load_prompt, load_yaml_config, match_module
from ai_agent.utils.prompt_formatter import format_prompt



class TestStep(BaseModel):
    """Single test step"""
    action: str = Field(description="Action to perform: navigate, fill, click, verify")
    target: str = Field(description="Element to interact with")
    value: str = Field(default="", description="Value to use (for fill actions)")
    expected: str = Field(default="", description="Expected result")


class TestCase(BaseModel):
    """Complete test case"""
    name: str = Field(description="Test case name")
    description: str = Field(description="What this test validates")
    steps: List[TestStep] = Field(description="Ordered test steps")


class DesignerAgent:
    """Converts scenarios to executable test steps"""
    
    def __init__(self):
        self.llm         = AIConfig.build_llm(AIConfig.MAX_TOKENS_DESIGNER)
        self.prompt_data = load_prompt("designer.yaml")
    
    def design_tests(self, scenarios: dict, ui_data: dict, max_tests: int = None) -> List[dict]:
        """
        Convert scenarios to test steps — batched by DESIGNER_BATCH_SIZE to
        avoid token overflow when scenario count is high (deep modules = 30+).
        """
        if max_tests is None:
            max_tests = AIConfig.MAX_TESTS

        depth = scenarios.get("depth", "medium")
        ui_elements_text = self._format_ui_elements(ui_data)
        tracker = get_tracker()

        # Split all scenarios into batches of DESIGNER_BATCH_SIZE
        all_scenarios = (
            [*scenarios.get("positive_scenarios", []),
             *scenarios.get("edge_cases", []),
             *scenarios.get("negative_scenarios", [])]
        )
        batch_size = AIConfig.DESIGNER_BATCH_SIZE
        batches = [all_scenarios[i:i + batch_size] for i in range(0, len(all_scenarios), batch_size)]

        print(f"[Designer] 📦 {len(all_scenarios)} scenarios → {len(batches)} batch(es) of {batch_size}")

        all_test_cases: List[dict] = []

        for batch_num, batch in enumerate(batches, 1):
            print(f"[Designer] ⚙️  Batch {batch_num}/{len(batches)} ({len(batch)} scenarios)...")

            batch_scenarios_text = "\n".join(f"  - {s}" for s in batch)

            formatted_prompt = format_prompt(
                self.prompt_data,
                scenarios=batch_scenarios_text,
                ui_elements=ui_elements_text,
                depth=depth,
                few_shot_examples=AIConfig.DESIGNER_FEW_SHOT_EXAMPLES,
                format_instructions=""
            )

            cached_response = get_cached_response(formatted_prompt)
            if cached_response:
                response_content = cached_response
            else:
                response = self.llm.invoke(formatted_prompt)
                response_content = response.content
                set_cached_response(formatted_prompt, response_content)

            tracker.generation(
                name="designer_agent",
                model=AIConfig.AZURE_OPENAI_DEPLOYMENT,
                prompt=formatted_prompt,
                completion=response_content,
                metadata={"batch": batch_num, "total_batches": len(batches),
                           "depth": depth, "stage": "test_design",
                           "cached": cached_response is not None}
            )

            batch_cases = self._parse_response(response_content)
            all_test_cases.extend(batch_cases)

            # Stop if we hit MAX_TESTS
            if len(all_test_cases) >= max_tests:
                all_test_cases = all_test_cases[:max_tests]
                print(f"[Designer] ⚠️  Reached MAX_TESTS ({max_tests}), stopping.")
                break

        tracker.trace_agent(
            agent_name="designer",
            input_data={"scenario_count": len(all_scenarios), "batches": len(batches)},
            output_data={"test_count": len(all_test_cases)},
            metadata={"tests_generated": len(all_test_cases)}
        )

        print(f"[Designer] ✅ {len(all_test_cases)} test cases generated")
        return all_test_cases

    def _parse_response(self, response_content: str) -> List[dict]:
        """Parse LLM JSON response, stripping markdown if present."""
        content = response_content.strip()
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif content.startswith("```"):
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1].strip()
                if content.startswith("json"):
                    content = content[4:].strip()
        try:
            data = json.loads(content)
            return data.get("test_cases", [])
        except json.JSONDecodeError as e:
            print(f"[Designer] ⚠️  Failed to parse batch response: {e}")
            return []
    
    def _format_scenarios(self, scenarios: dict) -> str:
        """Format scenarios for prompt — count driven by depth (same DEPTH_CONFIG as planner)"""
        from ai_agent.agents.planner import DEPTH_CONFIG
        depth = scenarios.get("depth", "medium")
        counts = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["medium"])

        lines = []
        if "positive_scenarios" in scenarios:
            lines.append("Positive:")
            for s in scenarios["positive_scenarios"][:counts["positive"]]:
                lines.append(f"  - {s}")

        if "edge_cases" in scenarios:
            lines.append("Edge Cases:")
            for s in scenarios["edge_cases"][:counts["edge"]]:
                lines.append(f"  - {s}")

        if "negative_scenarios" in scenarios:
            lines.append("Negative:")
            for s in scenarios["negative_scenarios"][:counts["negative"]]:
                lines.append(f"  - {s}")

        return "\n".join(lines)
    
    def _format_ui_elements(self, ui_data: dict) -> str:
        """Format UI elements for prompt (token-efficient)"""
        elements = ui_data.get("sample_elements", {})
        
        lines = ["Inputs:"]
        for inp in elements.get("inputs", [])[:3]:
            lines.append(f"  - {inp.get('label') or inp.get('placeholder') or inp.get('name')}")
        
        lines.append("Buttons:")
        for btn in elements.get("buttons", [])[:3]:
            lines.append(f"  - {btn.get('text')}")
        
        return "\n".join(lines)
    
    def export_to_excel(self, test_cases: List[dict], output_file: str = "test_cases.xlsx"):
        """
        Export test cases to Excel with proper formatting
        
        Columns: Test Case Name | Description | Test Steps | SQL Queries | Expected Result | Actual Result | Layers
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Test Cases"
        
        # Load DB queries config
        db_queries_cfg = load_yaml_config("ai_agent/config/db_queries.yaml")
        
        # Header row
        headers = ["Test Case Name", "Description", "Test Steps", "SQL Queries", "Expected Result", "Actual Result", "Layers"]
        ws.append(headers)
        
        # Style headers
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Add test cases
        for test_case in test_cases:
            test_name = test_case.get("name", "")
            description = test_case.get("description", "")
            
            # Format steps as numbered list with layer information
            steps = test_case.get("steps", [])
            steps_text = ""
            expected_result = ""
            layer_info = ""
            
            for idx, step in enumerate(steps, 1):
                action = step.get("action", "")
                target = step.get("target", "")
                value = step.get("value", "")
                expected = step.get("expected", "")
                layer = step.get("layer", "UI")  # Default to UI if not specified
                
                # Build step text with layer indicator
                layer_prefix = f"[{layer}] "
                
                if action == "navigate":
                    steps_text += f"{idx}. {layer_prefix}Navigate to: {value}\n"
                elif action == "fill":
                    steps_text += f"{idx}. {layer_prefix}Fill '{target}' with: {value}\n"
                elif action == "click":
                    steps_text += f"{idx}. {layer_prefix}Click on: {target}\n"
                elif action == "select":
                    steps_text += f"{idx}. {layer_prefix}Select '{value}' from: {target}\n"
                elif action == "verify_text" or action == "verify":
                    steps_text += f"{idx}. {layer_prefix}Verify text appears: {expected}\n"
                    expected_result = expected  # Capture final expected result
                elif action == "verify_element":
                    steps_text += f"{idx}. {layer_prefix}Verify element exists: {target}\n"
                elif action == "verify_api":
                    endpoint = step.get("endpoint", "")
                    status = step.get("expected_status", "")
                    steps_text += f"{idx}. {layer_prefix}Call API {endpoint} - Expect status {status}\n"
                    if not expected_result:
                        expected_result = expected or f"API returns {status}"
                elif action == "verify_api_field":
                    endpoint = step.get("endpoint", "")
                    field = step.get("field", "")
                    expected_value = step.get("expected_value", "")
                    steps_text += f"{idx}. {layer_prefix}Verify API {endpoint} field '{field}' = '{expected_value}'\n"
                elif action == "verify_db":
                    table = step.get("table", "")
                    column = step.get("column", "")
                    condition = step.get("condition", "")
                    steps_text += f"{idx}. {layer_prefix}Verify DB: {table}.{column} {condition}\n"
                    if not expected_result:
                        expected_result = expected or f"Database validation passes"
                elif action == "verify_db_count":
                    table = step.get("table", "")
                    condition = step.get("condition", "")
                    steps_text += f"{idx}. {layer_prefix}Verify DB count: SELECT COUNT(*) FROM {table} {condition}\n"
                elif action == "verify_db_value":
                    table = step.get("table", "")
                    column = step.get("column", "")
                    condition = step.get("condition", "")
                    steps_text += f"{idx}. {layer_prefix}Verify DB value: {table}.{column} {condition}\n"
                else:
                    steps_text += f"{idx}. {layer_prefix}{action.title()} {target}\n"
                
                # Track layers used
                if layer not in layer_info:
                    layer_info += f"{layer} "
            
            # Build SQL queries text from config (module-based matching)
            sql_queries_text = ""
            matched_module = match_module(test_name, db_queries_cfg)
            matched_queries = matched_module.get("queries", []) if matched_module else []
            
            if matched_queries:
                for idx, query in enumerate(matched_queries, 1):
                    sql = query.get("sql", "")
                    query_name = query.get("name", "")
                    query_expected = query.get("expected", "")
                    query_vars = query.get("variables", [])
                    
                    # Show variables if any
                    vars_text = f" (Variables: {', '.join(query_vars)})" if query_vars else ""
                    sql_queries_text += f"{idx}. [{query_name}]{vars_text}\n   SQL: {sql}\n   Expected: {query_expected}\n\n"
            
            # Add row with layer information and SQL queries
            ws.append([
                test_name,
                description,
                steps_text.strip(),
                sql_queries_text.strip() or "No DB queries defined",
                expected_result or "Test completes successfully",
                "",  # Actual result - empty for execution
                layer_info.strip()  # Layers used (UI, API, DB)
            ])
        
        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 30  # Test Case Name
        ws.column_dimensions['B'].width = 40  # Description
        ws.column_dimensions['C'].width = 60  # Test Steps (wider for UI+API+DB)
        ws.column_dimensions['D'].width = 70  # SQL Queries (wide for queries)
        ws.column_dimensions['E'].width = 30  # Expected Result
        ws.column_dimensions['F'].width = 30  # Actual Result
        ws.column_dimensions['G'].width = 15  # Layers
        
        # Align cells
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        
        # Save file
        wb.save(output_file)
        print(f"\n[OK] Test cases exported to: {output_file}")
        print(f"   Total test cases: {len(test_cases)}")
        return output_file


# Standalone function for workflow
def designer_agent(scenarios: dict, ui_data: dict, export_excel: bool = True) -> List[dict]:
    """
    Convert scenarios to executable test steps
    
    Args:
        scenarios: Test scenarios from planner
        ui_data: UI elements
        export_excel: Whether to export test cases to Excel (default: True)
        
    Returns:
        List of test cases with steps
    """
    designer = DesignerAgent()
    test_cases = designer.design_tests(scenarios, ui_data)
    
    # Auto-export to Excel for review
    if export_excel and test_cases:
        module_name = ui_data.get("title", "module").replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_cases_{module_name}_{timestamp}.xlsx"
        designer.export_to_excel(test_cases, output_file)
    
    return test_cases


if __name__ == "__main__":
    # Test designer with sample scenarios
    sample_scenarios = {
        "positive_scenarios": [
            "User logs in with valid credentials",
            "User navigates to dashboard after login"
        ],
        "edge_cases": [
            "User tries to login with empty fields"
        ],
        "negative_scenarios": [
            "User enters invalid password"
        ]
    }
    
    sample_ui = {
        "sample_elements": {
            "inputs": [
                {"label": "Email", "placeholder": "Enter email"},
                {"label": "Password", "placeholder": "Enter password"}
            ],
            "buttons": [
                {"text": "Login"}
            ]
        }
    }
    
    print("Testing Designer Agent...")
    try:
        tests = designer_agent(sample_scenarios, sample_ui)
        print(json.dumps(tests, indent=2))
    except Exception as e:
        print(f"Error: {e}")
