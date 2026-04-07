"""
MCP Server - Centralized Test Infrastructure
Provides browser automation, API testing, and database validation as a service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from playwright.sync_api import sync_playwright, Browser, Page
import httpx
import pymysql
from contextlib import asynccontextmanager
import uvicorn

# Global resources
browser: Optional[Browser] = None
page: Optional[Page] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global browser, page
    
    # Startup: Initialize browser
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    print("✓ MCP Server: Browser initialized")
    
    yield
    
    # Shutdown: Cleanup
    if page:
        page.close()
    if browser:
        browser.close()
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
    try:
        page.goto(request.url, wait_until=request.wait_until, timeout=request.timeout)
        return {
            "success": True,
            "url": page.url,
            "title": page.title()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/browser/fill")
async def fill_field(request: FillFieldRequest):
    """Fill input field"""
    try:
        if request.clear_first:
            page.fill(request.selector, "")
        page.fill(request.selector, request.value)
        return {"success": True, "selector": request.selector}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/browser/click")
async def click_element(request: ClickRequest):
    """Click element"""
    try:
        page.click(request.selector, timeout=request.timeout)
        return {"success": True, "selector": request.selector}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/browser/extract-ui")
async def extract_ui(request: ExtractUIRequest):
    """Extract UI elements"""
    try:
        page.goto(request.url, wait_until="networkidle", timeout=30000)
        
        # Extract all interactive elements
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
        
        return {
            "success": True,
            "url": page.url,
            "title": page.title(),
            "ui_data": ui_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/browser/screenshot")
async def take_screenshot():
    """Take screenshot"""
    try:
        screenshot = page.screenshot()
        return {
            "success": True,
            "screenshot": screenshot.hex()
        }
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
        "version": "1.0.0"
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
