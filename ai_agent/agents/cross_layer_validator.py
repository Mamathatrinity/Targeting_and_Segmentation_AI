"""
Cross-Layer Validator - Validates UI → API → DB flow
Simple validation without complex tracing
"""

from typing import Dict, Any, List


class CrossLayerValidator:
    """Validates consistency across UI, API, and Database layers"""
    
    def validate_flow(self, ui_result: Dict[str, Any], api_result: Dict[str, Any], db_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a complete flow across layers"""
        
        validations = []
        issues = []
        
        # Validate UI → API consistency
        ui_api = self._validate_ui_api(ui_result, api_result)
        validations.append(ui_api)
        if not ui_api["passed"]:
            issues.append(ui_api["issue"])
        
        # Validate API → DB consistency
        api_db = self._validate_api_db(api_result, db_result)
        validations.append(api_db)
        if not api_db["passed"]:
            issues.append(api_db["issue"])
        
        # Validate UI → DB consistency (end-to-end)
        ui_db = self._validate_ui_db(ui_result, db_result)
        validations.append(ui_db)
        if not ui_db["passed"]:
            issues.append(ui_db["issue"])
        
        all_passed = all(v["passed"] for v in validations)
        
        return {
            "status": "PASS" if all_passed else "FAIL",
            "validations": validations,
            "issues": issues,
            "summary": self._generate_summary(all_passed, issues)
        }
    
    def _validate_ui_api(self, ui_result: Dict[str, Any], api_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if UI state matches API response"""
        
        # Simple validation: if UI succeeded, API should return 200-299
        ui_passed = ui_result.get("status") == "passed"
        api_status = api_result.get("status_code", 0)
        api_success = 200 <= api_status < 300
        
        if ui_passed and not api_success:
            return {
                "layer": "UI → API",
                "passed": False,
                "issue": f"UI shows success but API returned {api_status}"
            }
        
        if not ui_passed and api_success:
            return {
                "layer": "UI → API",
                "passed": False,
                "issue": "UI shows failure but API succeeded"
            }
        
        return {
            "layer": "UI → API",
            "passed": True,
            "issue": None
        }
    
    def _validate_api_db(self, api_result: Dict[str, Any], db_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if API response matches DB state"""
        
        api_success = 200 <= api_result.get("status_code", 0) < 300
        db_updated = db_result.get("status") == "passed"
        
        # If API succeeded, DB should be updated
        if api_success and not db_updated:
            return {
                "layer": "API → DB",
                "passed": False,
                "issue": "API succeeded but DB not updated"
            }
        
        return {
            "layer": "API → DB",
            "passed": True,
            "issue": None
        }
    
    def _validate_ui_db(self, ui_result: Dict[str, Any], db_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check end-to-end: UI action → DB state"""
        
        ui_passed = ui_result.get("status") == "passed"
        db_updated = db_result.get("status") == "passed"
        
        if ui_passed != db_updated:
            return {
                "layer": "UI → DB",
                "passed": False,
                "issue": "UI and DB states are inconsistent"
            }
        
        return {
            "layer": "UI → DB",
            "passed": True,
            "issue": None
        }
    
    def _generate_summary(self, all_passed: bool, issues: List[str]) -> str:
        """Generate summary message"""
        
        if all_passed:
            return "All layers are consistent ✓"
        
        return f"Cross-layer issues found: {'; '.join(issues)}"
