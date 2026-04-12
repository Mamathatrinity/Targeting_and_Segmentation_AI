# MCP Server - Quick Start Guide

## What is This?

MCP (Model Context Protocol) Server provides centralized browser automation for your AI testing agents.

**Key Benefit for Parallel Testing:**
- One browser process handles all tests
- Each test gets its own context (isolated session)
- 3x less memory than spawning multiple browsers

---

## Starting the Server

**Option 1: PowerShell**
```powershell
cd mcp_server
python server.py
```

**Option 2: From root directory**
```powershell
python -m mcp_server.server
```

**Expected Output:**
```
✓ MCP Server: Browser initialized
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     Application startup complete.
```

---

## Using the Server

### **Check Health**
```powershell
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "browser": "running",
  "active_contexts": 0,
  "version": "1.0.0"
}
```

### **View API Documentation**
Open browser: http://localhost:8080/docs

---

## Parallel Testing with Contexts

### **1. Create Contexts for Each Test**
```python
import requests

# Create context for Login test
response = requests.post("http://localhost:8080/browser/context/create")
login_context = response.json()["context_id"]

# Create context for Search test
response = requests.post("http://localhost:8080/browser/context/create")
search_context = response.json()["context_id"]

# Now both tests run in parallel with isolated sessions!
```

### **2. Run Tests in Parallel**
```python
from concurrent.futures import ThreadPoolExecutor

def test_login(context_id):
    # Navigate, fill, click using this context_id
    pass

def test_search(context_id):
    # Navigate, fill, click using this context_id
    pass

with ThreadPoolExecutor(max_workers=5) as executor:
    executor.submit(test_login, login_context)
    executor.submit(test_search, search_context)
```

### **3. Cleanup**
```python
# Close contexts when done
requests.post(f"http://localhost:8080/browser/context/close?context_id={login_context}")
requests.post(f"http://localhost:8080/browser/context/close?context_id={search_context}")
```

---

## Your AI Agents Integration

Your agents (Planner/Designer/Executor) will:
1. Connect to MCP server (HTTP)
2. Use Azure GPT-4o for AI thinking
3. Use MCP for browser automation

**No changes to AI model** - Just better browser management!

---

## Stopping the Server

**Press Ctrl+C** in the server terminal

---

## Troubleshooting

**Error: Port 8080 already in use**
→ Change port in server.py line 427 to 8081

**Error: Browser not initialized**
→ Restart server (Ctrl+C, then `python server.py`)

**Error: Connection refused**
→ Server not running. Start it first.

---

## Architecture

```
Your AI Agents (Azure GPT-4o)
        ↓
    MCP Server (Port 8080)
        ↓
  Playwright Browser
    ├─ Context 1 (Login test)
    ├─ Context 2 (Search test)
    └─ Context 3 (Segments test)
```

**Memory Usage:**
- Without MCP: 3 tests = 1.2GB RAM (3 browsers)
- With MCP: 3 tests = 600MB RAM (1 browser, 3 contexts)

**Speed:**
- Without MCP: 3 tests = 15 seconds (3 × 5s startup)
- With MCP: 3 tests = 6 seconds (0s startup after first)
