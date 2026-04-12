# Pytest Framework with AI Agents

This folder contains the pytest testing framework integrated with AI agents for dynamic test generation and execution.

## Structure

```
├── conftest.py          # Pytest fixtures (browser, AI agents, MCP client)
├── pages/               # Page objects (UI locators ONLY, no methods)
│   ├── __init__.py
│   ├── login_page.py    # Login page locators
│   └── segments_page.py # Segments page locators
├── tests/               # AI-powered test files
│   ├── __init__.py
│   ├── test_login.py    # Login tests using AI agents
│   └── test_segments.py # Segments tests using AI agents
└── screenshots/         # Auto-captured on test failures
```

## Key Principles

### 1. **Page Objects = Locators Only**
```python
# pages/login_page.py
class LoginPageLocators:
    def __init__(self, page):
        self.username_input = page.locator("input[type='email']")
        self.password_input = page.locator("input[type='password']")
        # NO methods - just locators
```

### 2. **Tests Use AI Agents**
```python
# tests/test_login.py
def test_valid_login_with_ai(ai_test_framework):
    planner = ai_test_framework["planner"]
    designer = ai_test_framework["designer"]
    executor = ai_test_framework["executor"]
    validator = ai_test_framework["validator"]
    
    # AI generates scenarios
    scenarios = planner.generate_test_scenarios(...)
    
    # AI converts to steps
    steps = designer.convert_to_test_steps(...)
    
    # AI executes steps
    results = executor.execute_test_steps(...)
    
    # AI validates results
    validation = validator.validate_results(...)
```

### 3. **No Static Test Data**
- AI generates test data dynamically
- Use `test_context` fixture to store generated data
- No JSON files with hardcoded credentials/values

## Fixtures Available

### Browser Fixtures
- `playwright_instance` - Playwright instance (session-scoped)
- `browser` - Browser instance (session-scoped)
- `browser_context` - Browser context with auth state (session-scoped)
- `page` - New page per test (function-scoped)
- `fresh_page` - Page with cleared storage (function-scoped)

### AI Agent Fixtures
- `planner_agent` - Generates test scenarios
- `designer_agent` - Converts scenarios to executable steps
- `validator_agent` - Analyzes results with root cause analysis
- `ui_extractor` - Extracts UI elements via MCP
- `test_executor` - Executes test steps via MCP
- `ai_test_framework` - All agents together (dict)

### Other Fixtures
- `mcp_client` - MCP HTTP client for browser automation
- `test_context` - Dict for storing dynamic test data
- `screenshot_on_failure` - Auto-screenshots on failure

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific module
```bash
pytest tests/test_login.py
pytest tests/test_segments.py
```

### Run specific test class
```bash
pytest tests/test_login.py::TestLogin
pytest tests/test_segments.py::TestSegments
```

### Run specific test
```bash
pytest tests/test_login.py::TestLogin::test_valid_login_with_ai
```

### Run with verbose output
```bash
pytest -v
pytest -vv  # Extra verbose
```

### Run with live logging
```bash
pytest -s  # Show print statements
pytest -v -s
```

### Run performance tests
```bash
pytest -m performance
```

## Environment Variables

Required in `.env`:
```
BASE_URL=https://your-app-url.com
AZURE_OPENAI_API_KEY=your-actual-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_DEPLOYMENT_NAME=gpt-4o
```

## Test Flow

### 1. Test Scenario Generation
```python
# Planner Agent generates scenarios
scenarios = planner.generate_test_scenarios(
    module_name="Login",
    module_description="User authentication with email/password",
    context={"ui_elements": extracted_elements}
)
```

### 2. Convert to Steps
```python
# Designer Agent converts to executable YAML steps
test_steps = designer.convert_to_test_steps(
    scenario=scenario,
    context=test_context
)
```

### 3. Execute Tests
```python
# Executor runs steps via MCP
results = executor.execute_test_steps(
    test_steps=test_steps,
    page_url=page.url
)
```

### 4. Validate Results
```python
# Validator analyzes with AI
validation = validator.validate_results(
    test_steps=test_steps,
    results=results,
    expected_outcome="User logged in successfully"
)
# Returns: status, analysis, root_cause, self_healing_suggestions
```

## Example Test

```python
def test_create_segment_ai(ai_test_framework, page):
    """AI-powered segment creation test."""
    
    # 1. Generate scenario
    scenarios = ai_test_framework["planner"].generate_test_scenarios(
        module_name="Segment Creation",
        module_description="Create audience segment with age and location rules",
        context={}
    )
    
    # 2. Convert to steps
    test_steps = ai_test_framework["designer"].convert_to_test_steps(
        scenario=scenarios[0],
        context={}
    )
    
    # 3. Execute
    results = ai_test_framework["executor"].execute_test_steps(
        test_steps=test_steps,
        page_url=page.url
    )
    
    # 4. Validate
    validation = ai_test_framework["validator"].validate_results(
        test_steps=test_steps,
        results=results,
        expected_outcome="Segment created successfully"
    )
    
    # 5. Assert
    assert validation["status"] == "PASSED", validation["analysis"]
```

## Features

✅ **AI-Generated Test Scenarios** - Planner creates comprehensive test cases  
✅ **Dynamic Test Steps** - Designer converts scenarios to executable YAML  
✅ **MCP Browser Automation** - Executor runs tests via parallel-safe MCP server  
✅ **Intelligent Validation** - Validator provides root cause analysis + self-healing  
✅ **Auto-Screenshots** - Failures captured automatically  
✅ **Session Management** - Browser context with saved auth state  
✅ **Token Measurement** - Track GPT-4o usage for cost analysis  

## Integration with MMX_Studio_Automation

This framework follows the structure from `C:\Users\mv\MMX_Studio_Automation\pytest_framework`:

- ✅ `conftest.py` - Browser context + fixtures
- ✅ `pages/` - Page objects (locators only)
- ✅ `tests/` - Test files
- ✅ Session management with storage_state.json
- ✅ Auto-screenshots on failure

**Key Difference:** AI agents generate and execute tests instead of static test data files.

## Next Steps

1. **Add Azure Credentials** - Update `.env` with real API keys
2. **Start MCP Server** - Run `python mcp_server/server.py`
3. **Run Tests** - Execute `pytest tests/test_login.py`
4. **Measure Costs** - Check token usage in logs
5. **Tune Agents** - Adjust prompts based on results
