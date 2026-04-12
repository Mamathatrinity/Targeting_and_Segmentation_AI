"""
MCP Server - Centralized Test Infrastructure
Provides browser automation, API testing, and database validation as a service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
import httpx
import pymysql
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Global resources
browser: Optional[Browser] = None
page: Optional[Page] = None
playwright: Optional[Playwright] = None
executor = ThreadPoolExecutor(max_workers=1)

# Browser context pool for parallel testing
contexts: Dict[str, Any] = {}
import uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global browser, page, playwright
    
    # Startup: Initialize browser in thread
    def init_browser():
        global playwright, browser, page
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        return True
    
    await asyncio.get_event_loop().run_in_executor(executor, init_browser)
    print("✓ MCP Server: Browser initialized")
    
    yield
    
    # Shutdown: Cleanup (graceful, ignore errors)
    def cleanup():
        global browser, page, playwright
        try:
            if page:
                page.close()
        except:
            pass
        try:
            if browser:
                browser.close()
        except:
            pass
        try:
            if playwright:
                playwright.stop()
        except:
            pass
    
    try:
        await asyncio.get_event_loop().run_in_executor(executor, cleanup)
    except:
        pass
    print("✓ MCP Server: Resources cleaned up")


app = FastAPI(
    title="MCP Test Server",
    description="Centralized testing infrastructure for multi-application testing",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for multi-app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class NavigateRequest(BaseModel):
    url: str
    wait_until: str = "networkidle"
    timeout: int = 30000


class FillFieldRequest(BaseModel):
    selector: str
    value: str
    clear_first: bool = True


class ClickRequest(BaseModel):
    selector: str
    timeout: int = 5000


class APICallRequest(BaseModel):
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    timeout: int = 30


class DatabaseQueryRequest(BaseModel):
    host: str
    port: int = 3306
    user: str
    password: str
    database: str
    query: str


class ExtractUIRequest(BaseModel):
    url: str
    selectors: Optional[List[str]] = None


# ============================================
# BROWSER AUTOMATION ENDPOINTS
# ============================================

@app.post("/browser/navigate")
async def navigate(request: NavigateRequest):
    """Navigate to URL"""
    def _navigate():
        page.goto(request.url, wait_until=request.wait_until, timeout=request.timeout)
        return {"success": True, "url": page.url, "title": page.title()}
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(executor, _navigate)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/browser/fill")
async def fill_field(request: FillFieldRequest):
    """Fill input field"""
    def _fill():
        if request.clear_first:
            page.fill(request.selector, "")
        page.fill(request.selector, request.value)
        return {"success": True, "selector": request.selector}
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(executor, _fill)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/browser/click")
async def click_element(request: ClickRequest):
    """Click element"""
    def _click():
        page.click(request.selector, timeout=request.timeout)
        return {"success": True, "selector": request.selector}
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(executor, _click)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/browser/extract-ui")
async def extract_ui(request: ExtractUIRequest):
    """Extract UI elements"""
    def _extract():
        page.goto(request.url, wait_until="networkidle", timeout=30000)
        ui_data = page.evaluate("""
            () => {
                const results = {
                    inputs: [],
                    buttons: [],
                    links: []
                };
                
                // Extract inputs
                document.querySelectorAll('input').forEach(el => {
                    results.inputs.push({
                        type: el.type,
                        id: el.id,
                        name: el.name,
                        placeholder: el.placeholder
                    });
                });
                
                // Extract buttons
                document.querySelectorAll('button').forEach(el => {
                    results.buttons.push({
                        text: el.textContent.trim(),
                        id: el.id,
                        class: el.className
                    });
                });
                
                // Extract links
                document.querySelectorAll('a').forEach(el => {
                    results.links.push({
                        text: el.textContent.trim(),
                        href: el.href
                    });
                });
                
                return results;
            }
        """)
        return {"success": True, "url": page.url, "title": page.title(), "ui_data": ui_data}
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(executor, _extract)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/browser/screenshot")
async def take_screenshot():
    """Take screenshot"""
    def _screenshot():
        screenshot = page.screenshot()
        return {"success": True, "screenshot": screenshot.hex()}
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(executor, _screenshot)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/browser/context/create")
async def create_context():
    """Create new browser context for parallel testing"""
    def _create():
        context_id = str(uuid.uuid4())
        context = browser.new_context()
        new_page = context.new_page()
        contexts[context_id] = {"context": context, "page": new_page}
        return {"success": True, "context_id": context_id}
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(executor, _create)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/browser/context/close")
async def close_context(context_id: str):
    """Close browser context"""
    def _close():
        if context_id in contexts:
            contexts[context_id]["page"].close()
            contexts[context_id]["context"].close()
            del contexts[context_id]
            return {"success": True, "context_id": context_id}
        return {"success": False, "error": "Context not found"}
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(executor, _close)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# API TESTING ENDPOINTS
# ============================================

@app.post("/api/call")
async def api_call(request: APICallRequest):
    """Make API call"""
    try:
        async with httpx.AsyncClient() as client:
            if request.method.upper() == "GET":
                response = await client.get(
                    request.url,
                    headers=request.headers,
                    timeout=request.timeout
                )
            elif request.method.upper() == "POST":
                response = await client.post(
                    request.url,
                    headers=request.headers,
                    json=request.body,
                    timeout=request.timeout
                )
            elif request.method.upper() == "PUT":
                response = await client.put(
                    request.url,
                    headers=request.headers,
                    json=request.body,
                    timeout=request.timeout
                )
            elif request.method.upper() == "DELETE":
                response = await client.delete(
                    request.url,
                    headers=request.headers,
                    timeout=request.timeout
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported method: {request.method}")
            
            return {
                "success": True,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "json": response.json() if response.headers.get("content-type") == "application/json" else None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DATABASE VALIDATION ENDPOINTS
# ============================================

@app.post("/database/query")
async def database_query(request: DatabaseQueryRequest):
    """Execute database query"""
    try:
        connection = pymysql.connect(
            host=request.host,
            port=request.port,
            user=request.user,
            password=request.password,
            database=request.database,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(request.query)
                
                # SELECT query
                if request.query.strip().upper().startswith("SELECT"):
                    results = cursor.fetchall()
                    return {
                        "success": True,
                        "rows": results,
                        "count": len(results)
                    }
                # INSERT/UPDATE/DELETE
                else:
                    connection.commit()
                    return {
                        "success": True,
                        "affected_rows": cursor.rowcount
                    }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "browser": "running" if browser else "stopped",
        "active_contexts": len(contexts),
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint - server info"""
    return {
        "service": "MCP Browser Automation Server",
        "version": "1.0.0",
        "browser_status": "running" if browser else "stopped",
        "parallel_contexts": len(contexts),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "browser": "/browser/*",
            "contexts": "/browser/context/*"
        },
        "features": [
            "Single page automation",
            "Parallel browser contexts",
            "API testing",
            "Database validation"
        ]
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MCP Test Server",
        "version": "1.0.0",
        "endpoints": {
            "browser": "/browser/*",
            "api": "/api/*",
            "database": "/database/*",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
