"""
MCP Server - Stdio Implementation
Browser automation, API testing, and database validation via MCP protocol
"""
import asyncio
import json
import sys
from typing import Any, Optional
from playwright.async_api import async_playwright, Browser, Page


class MCPStdioServer:
    """MCP Server using stdio transport"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def initialize(self):
        """Initialize browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        await self.send_log("Browser initialized")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def send_response(self, request_id: str, result: Any):
        """Send JSON-RPC response"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        print(json.dumps(response), flush=True)
    
    async def send_error(self, request_id: str, code: int, message: str):
        """Send JSON-RPC error"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message}
        }
        print(json.dumps(response), flush=True)
    
    async def send_log(self, message: str):
        """Send log notification"""
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/message",
            "params": {"level": "info", "message": message}
        }
        print(json.dumps(notification), flush=True)
    
    async def handle_request(self, request: dict):
        """Handle incoming MCP request"""
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})
        
        try:
            if method == "tools/list":
                result = await self.list_tools()
            elif method == "tools/call":
                result = await self.call_tool(params)
            elif method == "initialize":
                result = await self.handle_initialize(params)
            else:
                await self.send_error(request_id, -32601, f"Method not found: {method}")
                return
            
            await self.send_response(request_id, result)
        except Exception as e:
            await self.send_error(request_id, -32603, str(e))
    
    async def handle_initialize(self, params: dict) -> dict:
        """Handle MCP initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "targeting-ai-testing",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {}
            }
        }
    
    async def list_tools(self) -> dict:
        """List available tools"""
        return {
            "tools": [
                {
                    "name": "navigate",
                    "description": "Navigate to URL",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to navigate to"}
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "fill_field",
                    "description": "Fill input field",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string"},
                            "value": {"type": "string"}
                        },
                        "required": ["selector", "value"]
                    }
                },
                {
                    "name": "click",
                    "description": "Click element",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string"}
                        },
                        "required": ["selector"]
                    }
                },
                {
                    "name": "extract_ui",
                    "description": "Extract UI elements from page",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"}
                        },
                        "required": ["url"]
                    }
                }
            ]
        }
    
    async def call_tool(self, params: dict) -> dict:
        """Execute tool call"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "navigate":
            await self.page.goto(arguments["url"])
            return {"content": [{"type": "text", "text": f"Navigated to {arguments['url']}"}]}
        
        elif tool_name == "fill_field":
            await self.page.fill(arguments["selector"], arguments["value"])
            return {"content": [{"type": "text", "text": f"Filled {arguments['selector']}"}]}
        
        elif tool_name == "click":
            await self.page.click(arguments["selector"])
            return {"content": [{"type": "text", "text": f"Clicked {arguments['selector']}"}]}
        
        elif tool_name == "extract_ui":
            await self.page.goto(arguments["url"])
            ui_data = await self.page.evaluate("""
                () => {
                    const inputs = Array.from(document.querySelectorAll('input')).map(el => ({
                        type: el.type, id: el.id, name: el.name, placeholder: el.placeholder
                    }));
                    const buttons = Array.from(document.querySelectorAll('button')).map(el => ({
                        text: el.textContent.trim(), id: el.id
                    }));
                    return { inputs, buttons };
                }
            """)
            return {"content": [{"type": "text", "text": json.dumps(ui_data)}]}
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def run(self):
        """Main server loop"""
        await self.initialize()
        
        # Read from stdin
        for line in sys.stdin:
            if not line.strip():
                continue
            
            try:
                request = json.loads(line)
                await self.handle_request(request)
            except json.JSONDecodeError as e:
                await self.send_log(f"Invalid JSON: {e}")
            except Exception as e:
                await self.send_log(f"Error: {e}")


async def main():
    """Entry point"""
    server = MCPStdioServer()
    try:
        await server.run()
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
