# AI Testing Agent - All Prompts Explained

**Total Prompts: 8**  
**Location:** `ai_agent/prompts/`  
**Purpose:** Control how each AI agent thinks and generates output

---

## Overview of All Prompts

| # | Prompt File | Agent | Purpose | Cost Impact |
|---|-------------|-------|---------|-------------|
| 1 | `planner_prompt.txt` | Planner | Generate test scenarios from UI | 25% of total |
| 2 | `designer_prompt.txt` | Designer | Convert scenarios to test code | 25% of total |
| 3 | `validator_prompt.txt` | Validator | Analyze test quality & failures | 50% of total |
| 4 | `failure_analyzer_prompt.txt` | Failure Analyzer | Deep failure analysis | On-demand |
| 5 | `ui_automation_prompt.txt` | UI Test Analyzer | Analyze UI test results | On-demand |
| 6 | `api_testing_prompt.txt` | API Test Analyzer | Analyze API test results | On-demand |
| 7 | `data_validation_prompt.txt` | DB Test Analyzer | Analyze DB validation results | On-demand |
| 8 | `_template.txt` | Template | Create new prompts | Development only |

---

## Prompt 1: Planner Prompt (planner_prompt.txt)

### Purpose
Convert UI elements into test scenarios - the "what to test"

### Complete Code with Line-by-Line Explanation

```plaintext
QA expert - generate test scenarios from UI elements.
```
**Explanation:** Sets the AI's role as a QA expert. This instruction tells the AI to think like a quality assurance professional.

---

```plaintext
UI: {ui_data}
```
**Explanation:** Placeholder for UI element data. This gets replaced with actual UI structure like buttons, forms, text fields extracted from the webpage.

**Example Value:**
```json
{
  "buttons": ["Login", "Register", "Forgot Password"],
  "inputs": [{"name": "username", "type": "text"}, {"name": "password", "type": "password"}],
  "links": ["Terms", "Privacy"]
}
```

---

```plaintext
Generate:
- 5 positive (happy path)
```
**Explanation:** Instructs AI to create 5 normal/successful test scenarios. These are tests where everything works correctly.

**Example:** "User logs in with valid credentials", "User successfully submits registration form"

---

```plaintext
- 3 edge cases
```
**Explanation:** Create 3 boundary/unusual scenarios. Tests that check limits or uncommon situations.

**Example:** "Login with very long username (100 characters)", "Submit form with all optional fields empty"

---

```plaintext
- 3 negative (errors/security)
```
**Explanation:** Create 3 failure scenarios. Tests that verify error handling and security.

**Example:** "Login with SQL injection attempt", "Submit form with invalid email format", "Access protected page without authentication"

---

```plaintext
{format_instructions}
```
**Explanation:** Placeholder for JSON output format rules. Tells AI exactly how to structure the response.

---

```plaintext
Return JSON only: {{"scenarios": [{{"name": "...", "type": "positive|edge_case|negative", "user_goal": "...", "expected_outcome": "..."}}]}}
```
**Explanation:** 
- **"Return JSON only":** Don't add explanations, just pure JSON
- **"scenarios":** Array of test scenarios
- **"name":** Test scenario title
- **"type":** Category (positive/edge_case/negative)
- **"user_goal":** What the user is trying to achieve
- **"expected_outcome":** What should happen

**Example Output:**
```json
{
  "scenarios": [
    {
      "name": "Successful login with valid credentials",
      "type": "positive",
      "user_goal": "User wants to access their account",
      "expected_outcome": "User is redirected to dashboard, sees welcome message"
    },
    {
      "name": "Login with username exceeding 255 characters",
      "type": "edge_case",
      "user_goal": "Test system handling of extremely long input",
      "expected_outcome": "System shows error: 'Username too long' or truncates gracefully"
    },
    {
      "name": "SQL injection attempt in login form",
      "type": "negative",
      "user_goal": "Attacker tries to bypass authentication",
      "expected_outcome": "System sanitizes input, login fails, no database error exposed"
    }
  ]
}
```

### Token Optimization Applied
- **Original prompt:** ~200 tokens (with examples)
- **Optimized prompt:** ~50 tokens (85% reduction)
- **Removed:** Examples, detailed explanations, redundant instructions
- **Kept:** Essential instructions, format requirements, JSON schema

---

## Prompt 2: Designer Prompt (designer_prompt.txt)

### Purpose
Convert test scenarios into executable test code - the "how to test"

### Complete Code with Line-by-Line Explanation

```plaintext
Convert scenarios to test steps.
```
**Explanation:** Sets the task - transform high-level scenarios into detailed step-by-step actions.

---

```plaintext
UI: {ui_elements}
```
**Explanation:** Provides UI element information (selectors, IDs, names) needed to interact with the page.

**Example Value:**
```json
{
  "username_input": {"selector": "#username", "type": "text"},
  "password_input": {"selector": "#password", "type": "password"},
  "login_button": {"selector": "#login-btn", "type": "button"}
}
```

---

```plaintext
Scenarios: {scenarios}
```
**Explanation:** The test scenarios from Planner (previous step). Designer converts these into executable steps.

---

```plaintext
Actions: navigate(url), fill(selector,value), click(selector), verify_text(text), select(selector,value)
```
**Explanation:** Available actions the AI can use in test steps. This is the "vocabulary" for writing tests.

- **navigate(url):** Go to a webpage
- **fill(selector, value):** Type text into an input field
- **click(selector):** Click a button/link
- **verify_text(text):** Check if text appears on page
- **select(selector, value):** Choose option from dropdown

---

```plaintext
Rules:
- Max {max_tests} tests
```
**Explanation:** Limit total number of tests generated. Prevents AI from creating too many tests.

**Example:** If max_tests = 5, AI will generate at most 5 test cases.

---

```plaintext
- Use stable selectors (id > name)
```
**Explanation:** Prefer stable element identifiers. Priority order:
1. **ID** (best) - rarely changes: `#login-btn`
2. **name** (good) - somewhat stable: `[name="username"]`
3. **CSS class** (avoid) - changes frequently: `.btn-primary`

**Why:** ID selectors are less likely to break when developers change CSS styling.

---

```plaintext
- Add verify_text after actions
```
**Explanation:** After every action, verify something happened. This catches failures immediately.

**Example:**
```json
[
  {"action": "click", "selector": "#login-btn"},
  {"action": "verify_text", "text": "Welcome back"}  // ← Verification after action
]
```

---

```plaintext
Return JSON: {{"test_cases": [{{"name": "...", "description": "...", "steps": [{{"action": "navigate|fill|click|verify_text|select", "selector": "...", "value": "..."}}]}}]}}
```
**Explanation:** Output format structure:
- **test_cases:** Array of test cases
- **name:** Test name
- **description:** What the test does
- **steps:** Array of actions to perform
  - **action:** Type of action (navigate, fill, click, etc.)
  - **selector:** Element to interact with
  - **value:** Data to use (for fill/select actions)

**Example Output:**
```json
{
  "test_cases": [
    {
      "name": "Login with valid credentials",
      "description": "User successfully logs in with correct username and password",
      "steps": [
        {"action": "navigate", "value": "https://app.com/login"},
        {"action": "fill", "selector": "#username", "value": "testuser@example.com"},
        {"action": "fill", "selector": "#password", "value": "SecurePass123"},
        {"action": "click", "selector": "#login-btn"},
        {"action": "verify_text", "text": "Welcome back, testuser"}
      ]
    }
  ]
}
```

---

```plaintext
Max {max_tests} tests. Use ID selectors. Add verify_text after actions.
```
**Explanation:** Reinforces the three critical rules in a concise reminder.

### Token Optimization Applied
- **Original prompt:** ~180 tokens (with examples and detailed explanations)
- **Optimized prompt:** ~60 tokens (67% reduction)
- **Removed:** Step-by-step examples, best practice explanations
- **Kept:** Action list, rules, JSON format

---

## Prompt 3: Validator Prompt (validator_prompt.txt)

### Purpose
Analyze test execution results and identify why tests failed

### Complete Code with Line-by-Line Explanation

```plaintext
Analyze test failures.
```
**Explanation:** Sets the core task - figure out what went wrong with failed tests.

---

```plaintext
Results: {results_summary}
```
**Explanation:** Provides test execution results with pass/fail status and error messages.

**Example Value:**
```json
{
  "total": 10,
  "passed": 7,
  "failed": 3,
  "failures": [
    {"test": "Login test", "error": "Element #login-btn not found"},
    {"test": "Register test", "error": "Element #submit-btn not found"},
    {"test": "Profile update", "error": "Timeout waiting for #save-btn"}
  ]
}
```

---

```plaintext
Find: root causes, patterns, fixes
```
**Explanation:** What to look for in the failures:
- **root causes:** Why did it fail? (selector changed, server down, timing issue)
- **patterns:** Are multiple tests failing the same way? (all button selectors failing)
- **fixes:** What should be done to resolve? (update selectors, add waits)

---

```plaintext
Categories: selector/timing/data/environment/bug/test-design
```
**Explanation:** Classify failures into these types:
- **selector:** Element not found, wrong CSS selector
- **timing:** Timeout, element not ready, slow page load
- **data:** Wrong test data, database issue
- **environment:** Server down, network issue
- **bug:** Actual application bug
- **test-design:** Test is incorrectly written

---

```plaintext
Return JSON: {{"status": "all_passed|failures_detected", "failure_count": 0, "root_causes": [...], "recommendations": [...], "confidence": "high|medium|low"}}
```
**Explanation:** Output structure:
- **status:** Overall result (all_passed or failures_detected)
- **failure_count:** Number of failed tests
- **root_causes:** Array of identified problems
- **recommendations:** Array of suggested fixes
- **confidence:** How sure is the AI about its analysis

**Example Output:**
```json
{
  "status": "failures_detected",
  "failure_count": 3,
  "root_causes": [
    "Button selectors changed - #login-btn and #submit-btn not found",
    "Timing issue - #save-btn appears after 3 seconds but test waits only 2 seconds"
  ],
  "recommendations": [
    "Update button selectors to use data-testid attributes instead of IDs",
    "Increase wait timeout from 2s to 5s for dynamic elements",
    "Add retry logic for element not found errors"
  ],
  "confidence": "high"
}
```

---

```plaintext
## Confidence Levels
- **high**: Clear evidence, single obvious cause
```
**Explanation:** Use "high" confidence when:
- Error message clearly indicates the problem
- Multiple tests fail with identical error
- Pattern is obvious (e.g., all tests fail at same step)

**Example:** "3 tests fail with 'Element #login-btn not found'" → high confidence it's a selector issue

---

```plaintext
- **medium**: Multiple possible causes, needs investigation
```
**Explanation:** Use "medium" confidence when:
- Could be multiple reasons
- Error is ambiguous
- Need more data to be sure

**Example:** "Timeout error" → could be slow server, network issue, or selector problem

---

```plaintext
- **low**: Insufficient data, unclear failure pattern
```
**Explanation:** Use "low" confidence when:
- Only one test failed
- Error message is generic
- No clear pattern

**Example:** "Unknown error occurred" → low confidence, need more investigation

---

```plaintext
## Constraints
- Keep total response under 150 words
```
**Explanation:** Limit response size to reduce token costs and keep analysis concise.

---

```plaintext
- Return ONLY JSON structure
```
**Explanation:** No additional text, explanations, or markdown - pure JSON only.

---

```plaintext
- No additional commentary
```
**Explanation:** Don't add comments like "Here's the analysis:" or "Based on the results:" - just JSON.

---

```plaintext
- Maximum 5 root causes
```
**Explanation:** Don't list every single issue - focus on top 5 most important.

---

```plaintext
- Maximum 5 recommendations
```
**Explanation:** Provide 5 or fewer actionable fixes. Prevents information overload.

---

```plaintext
- Be specific (mention selector names, step numbers, exact errors)
```
**Explanation:** Don't say "selector issue" - say "Element #login-btn not found in step 3"

**Good:** "Update selector #old-button to #new-button in LoginTest.py line 15"  
**Bad:** "Fix selector issues"

### Token Optimization Applied
- **Original prompt:** ~150 tokens
- **Optimized prompt:** ~90 tokens (40% reduction)
- **Removed:** Verbose examples, detailed confidence explanations
- **Kept:** Categories, constraints, JSON format

---

## Prompt 4: Failure Analyzer Prompt (failure_analyzer_prompt.txt)

### Purpose
Deep dive analysis when multiple tests fail - finds common patterns

### Complete Code with Line-by-Line Explanation

```plaintext
Analyze test failures and find root causes.
```
**Explanation:** This is a specialized analyzer for deeper investigation when Validator detects failures.

---

```plaintext
Failures:
{failures}
```
**Explanation:** Detailed failure information from multiple tests.

**Example Value:**
```json
[
  {"test": "Login", "step": 3, "error": "Element #btn-login not found", "screenshot": "login_fail.png"},
  {"test": "Register", "step": 5, "error": "Element #btn-submit not found", "screenshot": "reg_fail.png"},
  {"test": "Checkout", "step": 2, "error": "Element #btn-pay not found", "screenshot": "checkout_fail.png"}
]
```

---

```plaintext
Identify:
1. Common patterns (same error in multiple tests)
```
**Explanation:** Look for failures that repeat across tests.

**Example Pattern:** "3 tests failed with 'Element not found' - all button selectors"

---

```plaintext
2. Root cause category (selector/timing/data/environment/bug)
```
**Explanation:** Categorize the underlying problem (same categories as Validator).

**Example:** All button selectors failing → Category: "selector_issues"

---

```plaintext
3. Severity (critical/high/medium/low)
```
**Explanation:** How bad is this failure?
- **critical:** Blocks all testing, system completely broken
- **high:** Multiple core features affected
- **medium:** Some features affected, workarounds exist
- **low:** Minor issue, doesn't block testing

**Example:** If 20 out of 100 tests fail due to button selectors → Severity: "high"

---

```plaintext
4. Fix recommendations
```
**Explanation:** Specific actions to resolve the issue.

**Example:** "Update all button selectors from #btn-{action} to [data-testid='{action}-button']"

---

```plaintext
Return JSON only:
{{
  "patterns": ["3 tests failed: selector not found"],
```
**Explanation:** 
- **patterns:** Array of identified failure patterns
- Shows how many tests share the same failure

---

```plaintext
  "root_cause": "Selectors changed in recent UI update",
```
**Explanation:** The underlying reason for failures in plain English.

---

```plaintext
  "category": "selector_issues",
```
**Explanation:** Classification of the problem (from: selector_issues, timing_issues, data_issues, environment_issues, application_bug, test_design_flaw)

---

```plaintext
  "severity": "high",
```
**Explanation:** Impact level (critical/high/medium/low)

---

```plaintext
  "affected_tests": ["test1", "test2"],
```
**Explanation:** List of test names that failed due to this root cause.

---

```plaintext
  "recommendations": [
    "Update selectors to use data-testid attributes",
    "Add selector validation before execution"
  ],
```
**Explanation:** Step-by-step fixes to resolve the issue.

---

```plaintext
  "confidence": "high"
}}
```
**Explanation:** How confident is the analysis (high/medium/low)

**Complete Example Output:**
```json
{
  "patterns": [
    "15 tests failed with 'Element not found' error",
    "All failures involve button elements",
    "Pattern started after deployment on 2026-04-05"
  ],
  "root_cause": "Frontend team changed button ID naming convention from #btn-{action} to #button-{action}",
  "category": "selector_issues",
  "severity": "high",
  "affected_tests": [
    "Login_Test",
    "Register_Test", 
    "Checkout_Test",
    "Profile_Update_Test",
    "Password_Reset_Test"
  ],
  "recommendations": [
    "Update all button selectors: #btn-login → #button-login, #btn-submit → #button-submit, etc.",
    "Switch to data-testid attributes for better stability: [data-testid='login-button']",
    "Add automated selector validation step before test execution",
    "Coordinate with frontend team to notify QA before UI changes"
  ],
  "confidence": "high"
}
```

### When This Prompt Is Used
- **Trigger:** When Validator detects multiple failures (>3 tests failing)
- **Purpose:** Find if there's a common cause instead of treating each failure separately
- **Cost:** Only runs when needed (not every test run)

---

## Prompt 5: UI Automation Prompt (ui_automation_prompt.txt)

### Purpose
Specialized analyzer for UI test execution results - focuses on browser automation issues

### Complete Code with Line-by-Line Explanation

```plaintext
# UI Automation Agent Prompt

## Role
You are an expert UI Test Automation Engineer analyzing test execution results.
```
**Explanation:** Sets AI persona as a Playwright/Selenium expert who understands browser automation.

---

```plaintext
## Task
Analyze the results of UI test execution and identify patterns in failures.
```
**Explanation:** Core job - find patterns in UI test failures (different from API or DB failures).

---

```plaintext
## Input Data
Test Execution Results:
{execution_results}
```
**Explanation:** Playwright test run results with screenshots, console logs, error messages.

**Example Value:**
```json
{
  "tests": [
    {
      "name": "Login flow",
      "status": "failed",
      "error": "TimeoutError: Timeout 5000ms exceeded waiting for element #dashboard",
      "screenshot": "login_timeout.png",
      "console_logs": ["Navigation to /dashboard", "Error: Cannot read property 'user' of undefined"]
    }
  ]
}
```

---

```plaintext
## Analysis Requirements
1. Identify common failure patterns across multiple tests
```
**Explanation:** Don't analyze each test in isolation - look for trends.

**Example:** "5 tests failed with timeout" vs "5 different random errors"

---

```plaintext
2. Group failures by error type (timeout, selector issues, navigation errors, etc.)
```
**Explanation:** Categorize failures into buckets for easier fixing.

---

```plaintext
3. Provide specific, actionable recommendations for each failure group
```
**Explanation:** Don't say "fix timeouts" - say "Increase timeout from 5s to 10s for dashboard page load"

---

```plaintext
4. Assess confidence level based on error patterns
```
**Explanation:** More tests with same error = higher confidence in root cause

---

```plaintext
## Error Classification
Classify errors into these categories:
- **timeout**: Page load or element wait timeouts
```
**Explanation:** Element didn't appear within expected time.

**Example:** "Waited 5 seconds for #submit-btn but it never appeared"

---

```plaintext
- **element_not_found**: Selectors not finding elements
```
**Explanation:** Selector exists but doesn't match anything on the page.

**Example:** "#old-button" selector used but page has "#new-button"

---

```plaintext
- **invalid_selector**: Malformed or incorrect CSS selectors
```
**Explanation:** Syntax error in the selector itself.

**Example:** "##double-hash" or "[missing-bracket"

---

```plaintext
- **navigation_error**: URL navigation failures
```
**Explanation:** Can't reach the page.

**Example:** "404 Not Found", "Connection refused", "ERR_NAME_NOT_RESOLVED"

---

```plaintext
- **assertion_failed**: Text verification or validation failures
```
**Explanation:** Element found but contains wrong text/value.

**Example:** Expected "Welcome, John" but found "Welcome, Guest"

---

```plaintext
- **unknown_error**: Uncategorized errors
```
**Explanation:** Errors that don't fit other categories.

---

```plaintext
## Output Format
Return ONLY valid JSON (no markdown, no explanations):

{{
  "total_tests": 10,
  "passed": 7,
  "failed": 3,
```
**Explanation:** Summary counts of test execution.

---

```plaintext
  "failure_groups": [
    {{
      "error_type": "element_not_found",
      "count": 2,
```
**Explanation:** How many tests failed with this error type.

---

```plaintext
      "recommendation": "Update selectors to use more stable attributes like data-testid or id",
```
**Explanation:** How to fix this category of failures.

---

```plaintext
      "failed_tests": ["Login test", "Signup test"]
    }}
  ],
```
**Explanation:** Which specific tests failed in this group.

---

```plaintext
  "overall_recommendation": "Most failures due to selector issues - consider using data-testid attributes"
}}
```
**Explanation:** High-level summary recommendation across all failures.

**Complete Example Output:**
```json
{
  "total_tests": 25,
  "passed": 18,
  "failed": 7,
  "failure_groups": [
    {
      "error_type": "timeout",
      "count": 4,
      "recommendation": "Increase timeout to 10s for dashboard page - it loads dynamic content. Add explicit wait for #user-profile element.",
      "failed_tests": ["Dashboard_Load_Test", "Profile_Navigation_Test", "Settings_Page_Test", "Reports_Page_Test"]
    },
    {
      "error_type": "element_not_found",
      "count": 3,
      "recommendation": "Update button selectors: #btn-submit → [data-testid='submit-button'], #btn-cancel → [data-testid='cancel-button']",
      "failed_tests": ["Form_Submit_Test", "Registration_Test", "Edit_Profile_Test"]
    }
  ],
  "overall_recommendation": "Primary issue is timing (4/7 failures) - increase timeouts for pages with dynamic content loading. Secondary issue is selector stability - migrate to data-testid attributes."
}
```

---

```plaintext
## Constraints
- Return ONLY JSON structure
- No explanations outside JSON
- Group similar failures together
- Maximum 5 failure groups
- Be specific in recommendations
```
**Explanation:** Output rules to keep response focused and cost-effective.

### When This Prompt Is Used
- After UI test execution via Playwright
- When analyzing browser automation failures
- Focuses on DOM, selectors, page interactions

---

## Prompt 6: API Testing Prompt (api_testing_prompt.txt)

### Purpose
Specialized analyzer for REST API test results - focuses on HTTP/endpoint issues

### Complete Code with Line-by-Line Explanation

```plaintext
# API Testing Agent Prompt

## Role
You are an expert API Testing Engineer analyzing API test execution results.
```
**Explanation:** AI persona as REST API / HTTP testing expert.

---

```plaintext
## Task
Analyze the results of API test execution and identify patterns in failures.
```
**Explanation:** Find patterns in API call failures (different from UI failures).

---

```plaintext
## Input Data
API Test Execution Results:
{execution_results}
```
**Explanation:** HTTP request/response data, status codes, response times.

**Example Value:**
```json
{
  "tests": [
    {
      "endpoint": "POST /api/users",
      "expected_status": 201,
      "actual_status": 500,
      "response_time_ms": 1234,
      "error": "Internal Server Error",
      "response_body": {"error": "Database connection failed"}
    }
  ]
}
```

---

```plaintext
## Analysis Requirements
1. Identify common API failure patterns (status code mismatches, response format issues, timeouts)
```
**Explanation:** Look for trends in API failures.

**Example:** "10 endpoints returning 500 instead of 200" → server issue

---

```plaintext
2. Group failures by error type
```
**Explanation:** Categorize by API-specific error types.

---

```plaintext
3. Provide specific recommendations for fixing API issues
```
**Explanation:** Actionable fixes for API problems.

**Example:** "Check database connection pool - multiple 500 errors indicate DB timeout"

---

```plaintext
4. Assess impact and severity of failures
```
**Explanation:** How critical are the API failures?

**Example:** Auth endpoint failing = critical, analytics endpoint = medium

---

```plaintext
## Error Classification
Classify API errors into these categories:
- **status_mismatch**: Unexpected HTTP status codes (4xx, 5xx)
```
**Explanation:** API returns wrong status code.

**Example:** Expected 200 OK, got 404 Not Found or 500 Internal Server Error

---

```plaintext
- **body_mismatch**: Response body doesn't match expected structure
```
**Explanation:** Status code correct but JSON structure wrong.

**Example:** Expected `{"user": {...}}` but got `{"data": {"user": {...}}}`

---

```plaintext
- **timeout**: API response time exceeds threshold
```
**Explanation:** Request takes too long.

**Example:** Expected response in <2s, took 15s

---

```plaintext
- **connection_error**: Cannot connect to API server
```
**Explanation:** Network/server unreachable.

**Example:** "ECONNREFUSED", "DNS resolution failed", "ERR_CONNECTION_TIMED_OUT"

---

```plaintext
- **invalid_json**: Response is not valid JSON
```
**Explanation:** API returned malformed JSON or HTML error page.

**Example:** `{"user": "John"` (missing closing brace) or HTML 500 error page

---

```plaintext
- **authentication_error**: Auth token or credentials issues
```
**Explanation:** 401 Unauthorized, token expired, invalid API key.

**Example:** "Bearer token expired" or "Invalid API key"

---

```plaintext
## Output Format
Return ONLY valid JSON (no markdown, no explanations):

{{
  "total_tests": 15,
  "passed": 12,
  "failed": 3,
  "failure_groups": [
    {{
      "error_type": "status_mismatch",
      "count": 2,
      "recommendation": "Check API implementation - endpoints returning 500 instead of expected 200",
      "failed_tests": ["POST /users", "GET /profile"],
      "affected_endpoints": ["/users", "/profile"]
    }}
  ],
```
**Explanation:** Groups failures by error type and affected endpoints.

---

```plaintext
  "performance_summary": {{
    "avg_response_time_ms": 250,
    "slowest_endpoint": "/report/generate",
    "slowest_time_ms": 3500
  }},
```
**Explanation:** API performance metrics - helps identify slow endpoints even if they didn't fail.

---

```plaintext
  "overall_recommendation": "API stability issue - multiple 500 errors indicate server-side problems"
}}
```
**Explanation:** High-level summary of API health.

**Complete Example Output:**
```json
{
  "total_tests": 45,
  "passed": 38,
  "failed": 7,
  "failure_groups": [
    {
      "error_type": "status_mismatch",
      "count": 5,
      "recommendation": "5 endpoints returning 500 Internal Server Error - check database connection pool and server logs. Likely database timeout or connection limit reached.",
      "failed_tests": [
        "Create User Test",
        "Get User Profile Test",
        "Update User Test",
        "Create Segment Test",
        "Get Segments List Test"
      ],
      "affected_endpoints": [
        "POST /api/v1/users",
        "GET /api/v1/users/{id}",
        "PUT /api/v1/users/{id}",
        "POST /api/v1/segments",
        "GET /api/v1/segments"
      ]
    },
    {
      "error_type": "timeout",
      "count": 2,
      "recommendation": "Report generation endpoint exceeds 5s timeout - increase timeout to 15s or optimize report query. Consider moving to async job queue.",
      "failed_tests": [
        "Generate Large Report Test",
        "Export All Data Test"
      ],
      "affected_endpoints": [
        "GET /api/v1/reports/generate",
        "POST /api/v1/export/all"
      ]
    }
  ],
  "performance_summary": {
    "avg_response_time_ms": 312,
    "slowest_endpoint": "/api/v1/reports/generate",
    "slowest_time_ms": 8500
  },
  "overall_recommendation": "Critical: Database connection issues causing 5 endpoints to fail with 500 errors. Secondary: Report generation performance needs optimization or async processing. Check DB connection pool size and query performance."
}
```

---

```plaintext
## Constraints
- Return ONLY JSON structure
- No explanations outside JSON
- Include performance metrics
- Group by error type and affected endpoints
- Provide actionable fixes
```
**Explanation:** Keep output structured and actionable.

### When This Prompt Is Used
- After API test execution (HTTP requests)
- When analyzing REST endpoint failures
- Focuses on status codes, response times, JSON validation

---

## Prompt 7: Data Validation Prompt (data_validation_prompt.txt)

### Purpose
Specialized analyzer for database validation results - focuses on data quality

### Complete Code with Line-by-Line Explanation

```plaintext
# Data Validation Agent Prompt

## Role
You are an expert Data Quality Engineer analyzing data validation test results.
```
**Explanation:** AI persona as database/data quality expert.

---

```plaintext
## Task
Analyze the results of data validation tests and identify data quality issues.
```
**Explanation:** Find problems in database records (not the queries, but the data itself).

---

```plaintext
## Input Data
Data Validation Test Results:
{execution_results}
```
**Explanation:** Database query results with validation checks.

**Example Value:**
```json
{
  "validations": [
    {
      "check": "user.email NOT NULL",
      "passed": false,
      "failed_records": 5,
      "sample_failures": [{"id": 123, "email": null}, {"id": 456, "email": null}]
    },
    {
      "check": "user.email format validation",
      "passed": false,
      "failed_records": 150,
      "sample_failures": [{"id": 789, "email": "invalid-email"}, {"id": 101, "email": "test@"}]
    }
  ]
}
```

---

```plaintext
## Analysis Requirements
1. Identify data quality issues (nulls, type mismatches, constraint violations, format errors)
```
**Explanation:** Find data problems in database records.

---

```plaintext
2. Group failures by validation type
```
**Explanation:** Categorize by type of data issue.

---

```plaintext
3. Assess data quality score
```
**Explanation:** Calculate overall data health percentage.

**Formula:** (Passed validations / Total validations) * 100

---

```plaintext
4. Provide remediation recommendations
```
**Explanation:** How to fix or prevent data quality issues.

---

```plaintext
## Validation Types
Classify validation failures into:
- **not_null**: Null values found in non-nullable fields
```
**Explanation:** Required field has NULL/empty value.

**Example:** `user.email` is NULL but should be required

---

```plaintext
- **data_type**: Type mismatches (string vs integer, etc.)
```
**Explanation:** Wrong data type stored in field.

**Example:** `age` field contains "twenty-five" instead of 25

---

```plaintext
- **range**: Values outside expected range
```
**Explanation:** Value violates min/max constraints.

**Example:** `age = -5` or `age = 250`

---

```plaintext
- **unique**: Duplicate values in unique constraint fields
```
**Explanation:** Multiple records with same value in unique field.

**Example:** Two users with same email address when email should be unique

---

```plaintext
- **format**: Format violations (email, phone, date formats)
```
**Explanation:** Value doesn't match expected pattern.

**Example:** 
- Email: "notanemail" instead of "user@domain.com"
- Phone: "123" instead of "+1-555-123-4567"
- Date: "2026/04/05" instead of "2026-04-05"

---

```plaintext
- **count**: Unexpected record counts
```
**Explanation:** Too many or too few records.

**Example:** Expected 1000 users but found 500 (data loss?) or 2000 (duplicates?)

---

```plaintext
- **referential_integrity**: Foreign key violations
```
**Explanation:** Reference to non-existent record.

**Example:** `order.user_id = 999` but no user with ID 999 exists

---

```plaintext
## Output Format
Return ONLY valid JSON (no markdown, no explanations):

{{
  "total_validations": 20,
  "passed": 17,
  "failed": 3,
  "data_quality_score": 85,
```
**Explanation:** 
- **total_validations:** How many checks were run
- **passed/failed:** Results count
- **data_quality_score:** Percentage (85% = 17/20 passed)

---

```plaintext
  "failure_groups": [
    {{
      "validation_type": "format",
      "count": 2,
      "recommendation": "Add email format validation at data entry point - 150 invalid email records found",
      "affected_fields": ["email", "alternate_email"],
      "severity": "medium"
    }}
  ],
```
**Explanation:** Groups data issues by type with fix recommendations.

---

```plaintext
  "critical_issues": [
    "user_id field has 5 null values - violates NOT NULL constraint"
  ],
```
**Explanation:** Most severe data problems that need immediate attention.

---

```plaintext
  "overall_recommendation": "Data quality is good (85%) - focus on email validation and null handling"
}}
```
**Explanation:** Summary assessment of data health.

**Complete Example Output:**
```json
{
  "total_validations": 32,
  "passed": 26,
  "failed": 6,
  "data_quality_score": 81,
  "failure_groups": [
    {
      "validation_type": "format",
      "count": 3,
      "recommendation": "Implement email format validation at form entry and data import - 387 records have invalid email formats. Add regex validation: /^[\\w-\\.]+@([\\w-]+\\.)+[\\w-]{2,4}$/",
      "affected_fields": ["user.email", "user.secondary_email", "contact.email"],
      "severity": "medium"
    },
    {
      "validation_type": "not_null",
      "count": 2,
      "recommendation": "Critical: user.created_at has 12 NULL values. Add database trigger to set default timestamp on insert. Backfill existing NULL values with earliest known activity timestamp.",
      "affected_fields": ["user.created_at", "segment.created_by"],
      "severity": "high"
    },
    {
      "validation_type": "referential_integrity",
      "count": 1,
      "recommendation": "28 target_list records reference non-existent segment IDs. Add foreign key constraint and cleanup orphaned records with: DELETE FROM target_list WHERE segment_id NOT IN (SELECT id FROM segments)",
      "affected_fields": ["target_list.segment_id"],
      "severity": "high"
    }
  ],
  "critical_issues": [
    "user.created_at has 12 NULL values in production database - violates NOT NULL constraint",
    "28 orphaned target_list records with invalid segment_id references"
  ],
  "overall_recommendation": "Data quality score: 81% (Good). Focus on: 1) Add email validation at entry point (387 invalid emails), 2) Fix critical NULL values in created_at field (12 records), 3) Clean up referential integrity violations (28 orphaned records). Implement database constraints to prevent future violations."
}
```

---

```plaintext
## Data Quality Score Calculation
- 90-100: Excellent data quality
- 75-89: Good data quality with minor issues
- 60-74: Fair data quality - needs attention
- Below 60: Poor data quality - immediate action required
```
**Explanation:** How to interpret the data quality score percentage.

---

```plaintext
## Constraints
- Return ONLY JSON structure
- No explanations outside JSON
- Include severity levels (critical, high, medium, low)
- Calculate data quality score
- Prioritize critical issues first
```
**Explanation:** Output formatting rules.

### When This Prompt Is Used
- After database validation queries execute
- When checking data integrity
- Focuses on data quality, not query performance

---

## Prompt 8: Template Prompt (_template.txt)

### Purpose
Blueprint for creating new agent prompts - not used in production

### Structure Overview

This is a documentation template showing the standard format for all prompts. It's not executed by AI but serves as a guide for developers creating new agents.

**Sections:**
1. **Role:** Define the AI's expertise
2. **Task:** What the agent should accomplish
3. **Input Data:** Variables that will be injected
4. **Requirements:** Specific instructions
5. **Supported Actions:** Available operations
6. **Output Format:** Exact JSON structure
7. **Best Practices:** Optional guidelines
8. **Constraints:** Hard limits
9. **Example Scenarios:** Sample inputs/outputs

**When to Use:**
- Creating a new specialized agent
- Standardizing prompt format across team
- Documentation reference

---

## Summary: Prompt Usage & Cost Impact

### Core Production Prompts (Always Used)

| Prompt | Cost % | Tokens | When Used |
|--------|--------|--------|-----------|
| Planner | 25% | ~50 | Every test generation |
| Designer | 25% | ~60 | Every test generation |
| Validator | 50% | ~90 | Every test generation |

**Total for one test generation:** ~200 tokens (~$0.003 per test)

### Specialized Analysis Prompts (On-Demand)

| Prompt | Cost | When Used |
|--------|------|-----------|
| Failure Analyzer | ~$0.002 | When >3 tests fail |
| UI Automation | ~$0.002 | After UI test run |
| API Testing | ~$0.002 | After API test run |
| Data Validation | ~$0.002 | After DB validation run |

**These only run when needed**, not on every test generation.

---

## Token Optimization Summary

**Before Optimization:**
- Planner: 200 tokens (with examples)
- Designer: 180 tokens (with examples)
- Validator: 150 tokens (with examples)
- **Total:** ~530 tokens per test

**After Optimization:**
- Planner: 50 tokens (85% reduction)
- Designer: 60 tokens (67% reduction)
- Validator: 90 tokens (40% reduction)
- **Total:** ~200 tokens per test

**Cost Savings:** 62% reduction in prompt token costs

---

## Key Design Principles

All prompts follow these principles:

1. **JSON-Only Output:** No explanations, pure JSON
2. **Token Limits:** Hard constraints to prevent overspending
3. **Specific Examples:** Show exact format expected
4. **Clear Constraints:** "Maximum 5 items", "Under 150 words"
5. **Confidence Levels:** AI indicates certainty (high/medium/low)
6. **Actionable Recommendations:** Not just "fix it" but "Update selector #old to #new"
7. **Categories:** Standardized error types for pattern detection

---

## How Prompts Work Together

```
1. Planner Prompt
   ↓ (generates test scenarios)
   
2. Designer Prompt  
   ↓ (converts to executable steps)
   
3. Test Execution (FREE - no AI used)
   ↓ (runs tests in Playwright/API/DB)
   
4. Validator Prompt
   ↓ (analyzes results)
   
5. If failures detected:
   ├─→ Failure Analyzer (finds patterns)
   ├─→ UI Automation (if UI failures)
   ├─→ API Testing (if API failures)
   └─→ Data Validation (if DB failures)
```

**Cost occurs only in steps 1, 2, 4, and 5 (AI-powered steps)**  
**Execution (step 3) is FREE**

---

## Customizing Prompts

### To Change Test Count:
Edit `designer_prompt.txt`:
```
- Max {max_tests} tests
```
Change `max_tests` parameter in config.

### To Add New Validation Type:
Edit `validator_prompt.txt`:
```
Categories: selector/timing/data/environment/bug/test-design/YOUR_NEW_TYPE
```

### To Reduce Costs Further:
1. Decrease max test count
2. Remove optional validations
3. Use more template-based approaches (Hybrid mode)
4. Increase prompt caching effectiveness

---

**End of Prompts Explanation**

Total Prompts: 8  
Production Prompts: 3 (Planner, Designer, Validator)  
Specialized Prompts: 4 (Failure Analyzer, UI, API, DB)  
Template Prompt: 1 (Development only)

All prompts optimized for token efficiency while maintaining quality! 🎯
