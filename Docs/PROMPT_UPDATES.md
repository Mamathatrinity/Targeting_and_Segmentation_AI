# Prompt Updates - Structured Format with E2E Testing

## Summary

Updated both Planner and Designer prompts to use structured YAML format (like SQL prompt reference) with FEW_SHOT_EXAMPLES and added support for end-to-end testing across UI, API, and Database layers.

## Changes Made

### 1. planner.yaml (Completely Rewritten)

**New Structure:**
- ✅ **GOAL**: Clear objective - generate specific, Excel-ready test scenarios
- ✅ **CONTEXT**: Input/output format, domain, compliance requirements
- ✅ **ALLOWED / NOT_ALLOWED**: Explicit boundaries for scenarios
- ✅ **QUALITY_CHECK**: Validation rules for scenario quality
- ✅ **TEST_CASE_RULES**: Specificity, realistic data, expected results, Excel formatting
- ✅ **THINK_STEPWISE**: 7-step process for generating scenarios
- ✅ **OUTPUT_JSON**: Exact JSON structure expected
- ✅ **FEW_SHOT_EXAMPLES**: 2 complete examples (Login page, Search/Filter page)

**Key Improvements:**
- More specific scenario requirements ("test@example.com" not "valid email")
- Every scenario must include expected result
- Domain-appropriate test data (Dr. Smith, Cardiology, NPI numbers)
- Examples show real UI data → scenario mapping

### 2. designer.yaml (Completely Rewritten)

**New Structure:**
- ✅ **GOAL**: Convert scenarios to UI + API + DB test steps
- ✅ **CONTEXT**: Input scenarios, output test cases, layer support
- ✅ **ALLOWED_ACTIONS**: Comprehensive list of UI/API/DB actions
  - UI: navigate, fill, click, select, verify_text, verify_element, wait
  - API: verify_api, verify_status, verify_response, verify_api_field
  - DB: verify_db, verify_db_count, verify_db_value, verify_db_exists
- ✅ **NOT_ALLOWED**: Vague steps, missing layers, DB modifications
- ✅ **STEP_RULES**: Layer-specific rules for UI, API, and DB steps
- ✅ **THINK_STEPWISE**: 7-step process for converting scenarios to steps
- ✅ **LAYER_STRATEGY**: When to add API/DB validation
- ✅ **OUTPUT_JSON**: Test case structure with layer field
- ✅ **FEW_SHOT_EXAMPLES**: 3 complete examples showing UI+API+DB integration

**Key Improvements:**
- Each step now has `layer` field: "UI", "API", or "DB"
- API validation: endpoint, expected_status, response field checks
- DB validation: table, column, condition (SELECT queries only)
- Examples show complete E2E test flows

### 3. designer.py (Updated)

**Excel Export Enhancements:**
- ✅ Added **6th column**: "Layers" showing which layers tested (UI, API, DB)
- ✅ Updated step formatting to show layer prefix: `[UI]`, `[API]`, `[DB]`
- ✅ Added support for new action types:
  - `verify_api` - API endpoint validation
  - `verify_api_field` - Specific JSON field validation
  - `verify_db` - Database query validation
  - `verify_db_count` - Record count validation
  - `verify_element` - Element existence check
- ✅ Wider "Test Steps" column (60 chars) to accommodate multi-layer steps
- ✅ Layer tracking in each test case

**Excel Output Example:**

| Test Case Name | Description | Test Steps | Expected Result | Actual Result | Layers |
|----------------|-------------|------------|-----------------|---------------|--------|
| test_login_valid_e2e | User logs in and validates UI + API + DB | 1. [UI] Navigate to: /login<br>2. [UI] Fill Email: test@test.com<br>3. [UI] Click Login<br>4. [UI] Verify Dashboard<br>5. [API] Call /api/auth/session - Expect 200<br>6. [DB] Verify users.last_login updated | Dashboard appears, API returns 200, DB updated | _(empty)_ | UI API DB |

## Benefits

### Structured Prompt Format
- ✅ Clear GOAL/CONTEXT sections
- ✅ Explicit ALLOWED/NOT_ALLOWED boundaries
- ✅ Step-by-step THINK_STEPWISE logic
- ✅ Real examples with FEW_SHOT_EXAMPLES
- ✅ Consistent with best practices (SQL prompt reference)

### End-to-End Testing
- ✅ One test case validates UI + API + DB
- ✅ More comprehensive testing
- ✅ Catches integration issues
- ✅ Better coverage (UI works but API fails scenarios)

### No New Agents Needed
- ✅ Still 3 agents (Planner, Designer, Validator)
- ✅ Same cost ($0.002 per module)
- ✅ Less complexity
- ✅ Easier maintenance

### Excel Documentation
- ✅ Clear layer indicators in steps
- ✅ "Layers" column shows test scope
- ✅ Manual testers see complete flow
- ✅ Professional, readable format

## Migration Notes

**Old prompt files backed up:**
- `planner_old.yaml` - Original planner prompt
- `designer_old.yaml` - Original designer prompt

**No code changes needed in:**
- planner.py - Still loads and formats YAML same way
- validator.py - Already validates all 3 layers
- Executor - Will need updates to handle API/DB actions (future work)

## Next Steps (Future)

1. **Update Executor** to handle new action types:
   - `verify_api` → Use `requests` library
   - `verify_db` → Use `pymysql` library
   - Keep UI actions with Playwright

2. **Test the new prompts**:
   ```powershell
   python main.py --url https://ce-ts-dev.trinitylifesciences.com
   ```

3. **Review Excel output** to verify:
   - Steps show layer prefixes [UI], [API], [DB]
   - "Layers" column populated correctly
   - Test cases are more comprehensive

## Example Output Comparison

### Before (UI Only)
```json
{
  "name": "test_login",
  "steps": [
    {"action": "fill", "target": "Email", "value": "test@test.com"},
    {"action": "click", "target": "Login"},
    {"action": "verify_text", "expected": "Dashboard"}
  ]
}
```

### After (UI + API + DB)
```json
{
  "name": "test_login_e2e",
  "steps": [
    {"action": "fill", "target": "Email", "value": "test@test.com", "layer": "UI"},
    {"action": "click", "target": "Login", "layer": "UI"},
    {"action": "verify_text", "expected": "Dashboard", "layer": "UI"},
    {"action": "verify_api", "endpoint": "/api/auth/session", "expected_status": 200, "layer": "API"},
    {"action": "verify_db", "table": "users", "column": "last_login", "condition": "IS NOT NULL", "layer": "DB"}
  ]
}
```

## Cost Impact

**No change** - Still $0.002 per module:
- Planner: ~$0.0006 (slightly more tokens due to better prompts)
- Designer: ~$0.0010 (slightly more tokens for API/DB steps)
- Validator: ~$0.0004 (same)

Total: ~$0.002 per module (same as before)
