# MCP Server Setup & Usage Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP SERVER (Port 8080)                    │
│                  Centralized Test Infrastructure             │
│                                                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │   Browser     │  │   API Client  │  │   Database    │   │
│  │  (Playwright) │  │    (httpx)    │  │   (PyMySQL)   │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP API
            ┌──────────────┼──────────────┐
            │              │               │
┌───────────▼─────────┐ ┌─▼──────────────┐ ┌─▼─────────────┐
│  HCP Testing Agent  │ │ CRM Testing    │ │ ERP Testing   │
│  (Application #1)   │ │ Agent (#2)     │ │ Agent (#3)    │
└─────────────────────┘ └────────────────┘ └───────────────┘
```

## Setup Instructions

### 1. Install MCP Server Dependencies

```bash
cd mcp_server
pip install -r requirements.txt
playwright install chromium
```

### 2. Start MCP Server

```bash
# Development mode (with auto-reload)
python server.py

# Production mode
uvicorn server:app --host 0.0.0.0 --port 8080
```

Expected output:
```
✓ MCP Server: Browser initialized
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### 3. Test MCP Server

Open browser: http://localhost:8080

You should see:
```json
{
  "service": "MCP Test Server",
  "version": "1.0.0",
  "endpoints": {
    "browser": "/browser/*",
    "api": "/api/*",
    "database": "/database/*",
    "health": "/health"
  }
}
```

---

## Using MCP Client in Your Agents

### Update Your Existing Agents

**Before (Direct Playwright):**
```python
from playwright.sync_api import sync_playwright

# Direct browser control
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://app.com")
    page.fill("#email", "test@example.com")
    page.click("#login-btn")
```

**After (MCP Client):**
```python
from mcp_server.client import MCPClient

# Use centralized MCP Server
mcp = MCPClient("http://localhost:8080")
mcp.navigate("https://app.com")
mcp.fill_field("#email", "test@example.com")
mcp.click("#login-btn")
```

---

## Example: Update UI Extractor

**File: `ai_agent/tools/ui_extractor_mcp.py`**

```python
"""
UI Extractor using MCP Server
"""
from mcp_server.client import MCPClient

class UIExtractorMCP:
    def __init__(self, mcp_url: str = "http://localhost:8080"):
        self.mcp = MCPClient(mcp_url)
    
    def extract_ui_elements(self, url: str):
        """Extract UI elements via MCP Server"""
        result = self.mcp.extract_ui(url)
        return {
            "url": result["url"],
            "title": result["title"],
            "inputs": result["ui_data"]["inputs"],
            "buttons": result["ui_data"]["buttons"],
            "links": result["ui_data"]["links"]
        }

# Usage
extractor = UIExtractorMCP()
ui_data = extractor.extract_ui_elements("https://hcp-app.com")
```

---

## Example: Multiple Applications

### Application #1: HCP Testing

```python
from mcp_server.client import MCPClient

mcp = MCPClient("http://localhost:8080")

# Test HCP app
mcp.navigate("https://ce-ts-dev.trinitylifesciences.com")
mcp.fill_field("#username", "mv@trinitypartners.com")
mcp.click("#login-btn")

# Validate HCP API
api_result = mcp.api_call(
    "GET",
    "https://app-hcptargetandsegmentation-api-dev.azurewebsites.net/api/v1/segments"
)
print(f"HCP API: {api_result['status_code']}")
```

### Application #2: CRM Testing (Future)

```python
from mcp_server.client import MCPClient

# Same MCP server, different app!
mcp = MCPClient("http://localhost:8080")

# Test CRM app
mcp.navigate("https://crm-app.com")
mcp.fill_field("#email", "admin@company.com")
mcp.click("#submit")

# Validate CRM API
api_result = mcp.api_call("GET", "https://crm-api.com/customers")
print(f"CRM API: {api_result['status_code']}")
```

---

## MCP Server API Reference

### Browser Automation

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/browser/navigate` | POST | Navigate to URL |
| `/browser/fill` | POST | Fill input field |
| `/browser/click` | POST | Click element |
| `/browser/extract-ui` | POST | Extract UI elements |
| `/browser/screenshot` | GET | Take screenshot |

### API Testing

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/call` | POST | Make HTTP request (GET/POST/PUT/DELETE) |

### Database Validation

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/database/query` | POST | Execute SQL query |

### Health Check

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check server status |

---

## Deployment

### Option 1: Local Development
```bash
python mcp_server/server.py
```

### Option 2: Docker
```bash
# Build image
docker build -t mcp-server ./mcp_server

# Run container
docker run -p 8080:8080 mcp-server
```

### Option 3: Azure/AWS
```bash
# Deploy to Azure App Service
az webapp up --name mcp-test-server --runtime python:3.12

# Deploy to AWS Lambda
serverless deploy
```

---

## Migration Checklist

- [ ] Install MCP Server dependencies
- [ ] Start MCP Server locally
- [ ] Test MCP Server health endpoint
- [ ] Update HCP agents to use MCP Client
- [ ] Test HCP application with MCP
- [ ] Deploy MCP Server to production
- [ ] Add second application (CRM/ERP)
- [ ] Monitor MCP Server performance

---

## Benefits You Get

✅ **Reusability** - One MCP server for HCP, CRM, ERP, etc.  
✅ **Scalability** - Add new apps without duplicating infrastructure  
✅ **Centralized** - One place to fix bugs, update drivers  
✅ **Connection Pooling** - Share browser sessions, DB connections  
✅ **Cost Savings** - Reduce resource usage  

---

## Cost Comparison

### Before (Direct Architecture):
- HCP App: 1 browser instance
- CRM App: 1 browser instance  
- ERP App: 1 browser instance
- **Total: 3 browser instances**

### After (MCP Server):
- MCP Server: 1 browser instance
- HCP App: Uses MCP  
- CRM App: Uses MCP  
- ERP App: Uses MCP  
- **Total: 1 browser instance**

**Savings: 66% resource reduction!**

---

## Next Steps

1. Start MCP Server: `python mcp_server/server.py`
2. Keep HCP agent as-is (still works!)
3. When you add app #2, use MCP Client
4. Gradually migrate HCP to MCP if needed

**Your HCP system works NOW. MCP is ready for FUTURE apps!**
