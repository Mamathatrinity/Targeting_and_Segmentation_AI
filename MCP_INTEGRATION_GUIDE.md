# Integrating Existing MCP Server with HCP AI Testing System

## Current Architecture

```
┌────────────────────────────────────────────────────────────────┐
│        Existing MCP Server (validation_mcp_server)             │
│        Location: C:\Users\mv\mcp_servers\validation_mcp_server │
│                                                                 │
│  ✅ API Validator      (api_validator.py)                      │
│  ✅ Database Validator (db_validator.py)                       │
│  ✅ UI Validator       (ui_validator.py)                       │
└────────────────────────────────────────────────────────────────┘
                               ↑
                               │ Connect to
                               │
┌────────────────────────────────────────────────────────────────┐
│     HCP AI Testing System (Targeting_and_Segmentation_AI)      │
│                                                                 │
│  ai_agent/agents/                                               │
│    ├── planner.py                                              │
│    ├── designer.py                                             │
│    ├── validator.py                                            │
│    └── ...                                                     │
└────────────────────────────────────────────────────────────────┘
```

---

## Integration Steps

### Step 1: Check Existing MCP Server Status

```bash
cd C:\Users\mv\mcp_servers\validation_mcp_server

# Check if server runs
python server.py
```

Expected output:
```
MCP Server started successfully
```

---

### Step 2: Create MCP Client for Your HCP Agents

**File: `ai_agent/integrations/mcp_client.py`**

```python
"""
MCP Client - Connect to existing validation_mcp_server
"""
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import subprocess
from typing import Dict, Any


class ValidationMCPClient:
    """Client to communicate with existing MCP validation server"""
    
    def __init__(self, server_path: str = r"C:\Users\mv\mcp_servers\validation_mcp_server"):
        self.server_path = server_path
        self.session = None
    
    async def connect(self):
        """Connect to MCP server"""
        server_params = StdioServerParameters(
            command="python",
            args=["server.py"],
            cwd=self.server_path
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()
    
    # ====================================
    # API Validation
    # ====================================
    
    async def api_set_base_url(self, url: str):
        """Set base URL for API testing"""
        result = await self.session.call_tool("api_set_base_url", {"url": url})
        return result
    
    async def api_set_auth_token(self, token: str, auth_type: str = "Bearer"):
        """Set authentication token"""
        result = await self.session.call_tool(
            "api_set_auth_token",
            {"token": token, "auth_type": auth_type}
        )
        return result
    
    async def api_make_request(self, endpoint: str, method: str = "GET", data: Dict = None):
        """Make API request"""
        params = {
            "endpoint": endpoint,
            "method": method
        }
        if data:
            params["data"] = data
        
        result = await self.session.call_tool("api_make_request", params)
        return result
    
    # ====================================
    # Database Validation
    # ====================================
    
    async def db_connect(self, host: str, database: str, user: str, password: str, port: int = 3306):
        """Connect to database"""
        result = await self.session.call_tool("db_connect", {
            "host": host,
            "database": database,
            "user": user,
            "password": password,
            "port": port
        })
        return result
    
    async def db_execute_query(self, query: str):
        """Execute database query"""
        result = await self.session.call_tool("db_execute_query", {"query": query})
        return result
    
    async def db_validate_data_exists(self, table: str, condition: str):
        """Validate data exists in table"""
        result = await self.session.call_tool("db_validate_data_exists", {
            "table": table,
            "condition": condition
        })
        return result
    
    # ====================================
    # UI Validation
    # ====================================
    
    async def ui_navigate(self, url: str):
        """Navigate to URL"""
        result = await self.session.call_tool("ui_navigate", {"url": url})
        return result
    
    async def ui_validate_element(self, selector: str):
        """Validate element exists"""
        result = await self.session.call_tool("ui_validate_element", {"selector": selector})
        return result
    
    async def ui_take_screenshot(self, filename: str):
        """Take screenshot"""
        result = await self.session.call_tool("ui_take_screenshot", {"filename": filename})
        return result
```

---

### Step 3: Update Your Agents to Use MCP

#### Option A: Update API Testing Agent

**File: `ai_agent/agents/api_testing_agent.py`** (Update existing)

```python
import asyncio
from ai_agent.integrations.mcp_client import ValidationMCPClient

class APITestingAgent:
    def __init__(self):
        self.mcp_client = ValidationMCPClient()
    
    async def test_api_endpoint(self, endpoint: str):
        """Test API endpoint using MCP server"""
        await self.mcp_client.connect()
        
        # Set base URL
        await self.mcp_client.api_set_base_url(
            "https://app-hcptargetandsegmentation-api-dev.azurewebsites.net"
        )
        
        # Make request
        result = await self.mcp_client.api_make_request(endpoint, method="GET")
        
        return result

# Usage
async def main():
    agent = APITestingAgent()
    result = await agent.test_api_endpoint("/api/v1/segments")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

#### Option B: Update UI Validation

**File: `ai_agent/agents/ui_automation_agent.py`** (Update existing)

```python
import asyncio
from ai_agent.integrations.mcp_client import ValidationMCPClient

class UIAutomationAgent:
    def __init__(self):
        self.mcp_client = ValidationMCPClient()
    
    async def validate_ui_elements(self, url: str, selectors: list):
        """Validate UI elements using MCP server"""
        await self.mcp_client.connect()
        
        # Navigate
        await self.mcp_client.ui_navigate(url)
        
        # Validate each selector
        results = []
        for selector in selectors:
            result = await self.mcp_client.ui_validate_element(selector)
            results.append(result)
        
        return results

# Usage
async def main():
    agent = UIAutomationAgent()
    results = await agent.validate_ui_elements(
        "https://ce-ts-dev.trinitylifesciences.com",
        ["#email", "#password", "#login-btn"]
    )
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

---

#### Option C: Update Database Validation

**File: `ai_agent/agents/data_validation_agent.py`** (Update existing)

```python
import asyncio
from ai_agent.integrations.mcp_client import ValidationMCPClient

class DataValidationAgent:
    def __init__(self):
        self.mcp_client = ValidationMCPClient()
    
    async def validate_database(self, query: str):
        """Validate database using MCP server"""
        await self.mcp_client.connect()
        
        # Connect to DB
        await self.mcp_client.db_connect(
            host="mysql-customerengagement-dev.mysql.database.azure.com",
            database="mysql_hcp_targetandsegmentation_dev",
            user="your-username",
            password="your-password"
        )
        
        # Execute query
        result = await self.mcp_client.db_execute_query(query)
        
        return result

# Usage
async def main():
    agent = DataValidationAgent()
    result = await agent.validate_database("SELECT * FROM segments LIMIT 5")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Benefits of Using Your Existing MCP Server

| Feature | Without MCP | With Existing MCP |
|---------|-------------|-------------------|
| **API Testing** | httpx directly | ✅ MCP standardized |
| **Database** | PyMySQL directly | ✅ MCP pooled connections |
| **UI Testing** | Playwright directly | ✅ MCP managed browser |
| **Reusability** | HCP only | ✅ HCP + CRM + ERP |
| **Code Duplication** | High | ✅ Zero (centralized) |
| **Maintenance** | Per-agent | ✅ One place (MCP) |

---

## Migration Plan

### Phase 1: Test MCP Server (Today)
```bash
cd C:\Users\mv\mcp_servers\validation_mcp_server
python server.py
```

### Phase 2: Create MCP Client (30 minutes)
- Create `ai_agent/integrations/mcp_client.py`
- Test connection to MCP server

### Phase 3: Update 1 Agent (1 hour)
- Start with API testing agent
- Use MCP for API calls
- Compare results (should be identical)

### Phase 4: Gradually Migrate Others (Optional)
- UI automation agent
- Database validation agent
- Keep direct Playwright for executor (it's fast)

---

## Recommended Approach

### ✅ **Use MCP For:**
- API validation (already implemented!)
- Database validation (already implemented!)
- Cross-application testing (CRM, ERP future)

### ⚠️ **Keep Direct Playwright For:**
- Test execution (executor.py) - No need to change
- UI extraction (ui_extractor.py) - Already optimized

---

## Quick Test

```bash
# Terminal 1: Start MCP Server
cd C:\Users\mv\mcp_servers\validation_mcp_server
python server.py

# Terminal 2: Test from HCP agent
cd C:\Users\mv\Targeting_and_Segmentation_AI
python -c "from ai_agent.integrations.mcp_client import ValidationMCPClient; print('MCP Client ready!')"
```

---

## Next Steps

1. **Test your existing MCP server** - Make sure it runs
2. **Create MCP client wrapper** - `ai_agent/integrations/mcp_client.py`
3. **Update API/DB agents** - Use MCP for validation
4. **Keep executor as-is** - Direct Playwright is perfect for test execution

**Your MCP server is already production-ready! Just need to connect it!**

Want me to create the integration files now?
