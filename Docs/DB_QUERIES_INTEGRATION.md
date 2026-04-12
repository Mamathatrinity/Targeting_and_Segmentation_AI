# DB Queries Integration - Manual SQL Query Management

## Overview

Added support for writing and managing SQL queries manually in a centralized YAML configuration file. These queries are automatically included in Excel test case exports.

## Files Created/Updated

### 1. `ai_agent/config/db_queries.yaml` (NEW)

**Purpose:** Central repository for all database validation queries

**Structure:**
```yaml
test_case_name:
  - name: "query_identifier"
    sql: "SELECT statement"
    expected: "Expected result description"
    description: "What this query validates"
```

**Example:**
```yaml
test_login_valid:
  - name: "verify_last_login_updated"
    sql: "SELECT last_login FROM users WHERE email = 'test@test.com' AND last_login IS NOT NULL"
    expected: "Returns 1 row with timestamp within last 10 seconds"
    description: "Verify user's last_login timestamp updated after successful login"
```

### 2. `designer.py` (UPDATED)

**Added:**
- `load_db_queries()` function - Loads queries from YAML config
- SQL Queries column in Excel export (Column D)
- Automatic mapping: test_case_name → SQL queries from config

**Excel Format:**

| Test Case Name | Description | Test Steps | SQL Queries | Expected Result | Actual Result | Layers |
|----------------|-------------|------------|-------------|-----------------|---------------|--------|
| test_login_valid | User logs in | 1. [UI] Fill Email<br>2. [UI] Click Login | 1. [verify_last_login_updated]<br>SQL: SELECT last_login FROM users...<br>Expected: Returns timestamp | Login successful | _(empty)_ | UI API DB |

## How to Use

### Step 1: Write SQL Queries in YAML

Edit `ai_agent/config/db_queries.yaml`:

```yaml
test_your_feature:
  - name: "verify_data_saved"
    sql: "SELECT * FROM your_table WHERE id = 123"
    expected: "Returns 1 row with data"
    description: "Verify feature data persisted to database"
```

### Step 2: Run Test Generation

```powershell
python main.py --url https://your-app.com
```

### Step 3: View Excel Output

Open `test_cases_module_timestamp.xlsx` and see SQL queries in Column D.

## Benefits

✅ **Centralized:** All queries in one file, easy to find and update
✅ **Version Control:** Track query changes in Git
✅ **Documentation:** Queries visible in Excel for manual testers
✅ **Execution Ready:** Executor can load and run queries directly from YAML
✅ **Maintainable:** Update queries without editing Excel or Python code
✅ **Scalable:** Handle hundreds of test cases easily

## Query Examples Provided

The config file includes examples for:
- Login validation (last_login, login_count)
- Search validation (HCP search, filters)
- Segment creation (segment records, HCP counts)
- User registration (user creation, profiles)
- Data export (export logs, record counts)
- Generic templates (copy and customize)

## Query Rules

**Allowed:**
- ✅ SELECT statements only (read-only)
- ✅ WHERE conditions to filter results
- ✅ JOINs across multiple tables
- ✅ COUNT, SUM, AVG aggregations
- ✅ ORDER BY, LIMIT for result control

**Not Allowed:**
- ❌ INSERT, UPDATE, DELETE (modifications)
- ❌ DROP, TRUNCATE, ALTER (DDL)
- ❌ Queries without WHERE conditions (full table scans)
- ❌ Hard-coded sensitive data

## Next Steps

### For Immediate Use:
1. Edit `db_queries.yaml` to add your queries
2. Run system to generate test cases
3. Review SQL queries in Excel output

### For Future Automation:
1. Update executor.py to read from db_queries.yaml
2. Add database connection configuration
3. Execute queries during test execution
4. Validate results against expected values

## Example Workflow

**1. Add Query:**
```yaml
test_create_user:
  - name: "verify_user_exists"
    sql: "SELECT email, status FROM users WHERE email = 'newuser@test.com'"
    expected: "Returns 1 row with status = 'active'"
    description: "Verify new user created successfully"
```

**2. Generate Tests:**
```powershell
python main.py --url https://app.com/register
```

**3. Excel Output:**

| Test Case Name | SQL Queries |
|----------------|-------------|
| test_create_user | 1. [verify_user_exists]<br>SQL: SELECT email, status FROM users...<br>Expected: Returns 1 row with status = 'active' |

**4. Execute (Future):**
```python
# executor.py will read and run these queries
queries = load_db_queries()
for query in queries["test_create_user"]:
    result = execute_sql(query["sql"])
    assert result, query["expected"]
```

## File Locations

```
ai_agent/
├── config/
│   └── db_queries.yaml          ← Write SQL queries here
├── agents/
│   └── designer.py              ← Loads queries and exports to Excel
└── prompts/
    └── designer.yaml            ← AI generates DB validation steps
```

## Notes

- Queries are matched by test case name
- If no queries defined for a test, Excel shows "No DB queries defined"
- Queries are documentation until executor is updated to execute them
- Use templates at bottom of YAML file as starting points
