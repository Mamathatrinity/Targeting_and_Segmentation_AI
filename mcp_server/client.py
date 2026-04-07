"""
MCP Client - Python client for MCP Server
Use this in your AI testing agents to communicate with MCP Server
"""
import httpx
from typing import Dict, Any, Optional, List


class MCPClient:
    """Client to communicate with MCP Server"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize MCP Client
        
        Args:
            base_url: MCP Server URL (default: http://localhost:8080)
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=60.0)
    
    # ============================================
    # BROWSER AUTOMATION
    # ============================================
    
    def navigate(self, url: str, wait_until: str = "networkidle", timeout: int = 30000) -> Dict:
        """
        Navigate to URL
        
        Args:
            url: Target URL
            wait_until: Wait strategy (networkidle, load, domcontentloaded)
            timeout: Timeout in milliseconds
            
        Returns:
            {"success": True, "url": str, "title": str}
        """
        response = self.client.post(
            f"{self.base_url}/browser/navigate",
            json={"url": url, "wait_until": wait_until, "timeout": timeout}
        )
        response.raise_for_status()
        return response.json()
    
    def fill_field(self, selector: str, value: str, clear_first: bool = True) -> Dict:
        """
        Fill input field
        
        Args:
            selector: CSS selector
            value: Text to fill
            clear_first: Clear field before filling
            
        Returns:
            {"success": True, "selector": str}
        """
        response = self.client.post(
            f"{self.base_url}/browser/fill",
            json={"selector": selector, "value": value, "clear_first": clear_first}
        )
        response.raise_for_status()
        return response.json()
    
    def click(self, selector: str, timeout: int = 5000) -> Dict:
        """
        Click element
        
        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
            
        Returns:
            {"success": True, "selector": str}
        """
        response = self.client.post(
            f"{self.base_url}/browser/click",
            json={"selector": selector, "timeout": timeout}
        )
        response.raise_for_status()
        return response.json()
    
    def extract_ui(self, url: str) -> Dict:
        """
        Extract UI elements from page
        
        Args:
            url: Target URL
            
        Returns:
            {"success": True, "url": str, "title": str, "ui_data": {...}}
        """
        response = self.client.post(
            f"{self.base_url}/browser/extract-ui",
            json={"url": url}
        )
        response.raise_for_status()
        return response.json()
    
    def screenshot(self) -> Dict:
        """
        Take screenshot of current page
        
        Returns:
            {"success": True, "screenshot": str (hex)}
        """
        response = self.client.get(f"{self.base_url}/browser/screenshot")
        response.raise_for_status()
        return response.json()
    
    # ============================================
    # API TESTING
    # ============================================
    
    def api_call(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict:
        """
        Make API call
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: API endpoint URL
            headers: Request headers
            body: Request body (JSON)
            timeout: Timeout in seconds
            
        Returns:
            {"success": True, "status_code": int, "body": str, "json": dict}
        """
        response = self.client.post(
            f"{self.base_url}/api/call",
            json={
                "method": method,
                "url": url,
                "headers": headers,
                "body": body,
                "timeout": timeout
            }
        )
        response.raise_for_status()
        return response.json()
    
    # ============================================
    # DATABASE VALIDATION
    # ============================================
    
    def query_database(
        self,
        query: str,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int = 3306
    ) -> Dict:
        """
        Execute database query
        
        Args:
            query: SQL query
            host: Database host
            user: Database user
            password: Database password
            database: Database name
            port: Database port
            
        Returns:
            For SELECT: {"success": True, "rows": [...], "count": int}
            For INSERT/UPDATE/DELETE: {"success": True, "affected_rows": int}
        """
        response = self.client.post(
            f"{self.base_url}/database/query",
            json={
                "query": query,
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": database
            }
        )
        response.raise_for_status()
        return response.json()
    
    # ============================================
    # HEALTH CHECK
    # ============================================
    
    def health_check(self) -> Dict:
        """
        Check MCP Server health
        
        Returns:
            {"status": "healthy", "browser": "running", "version": "1.0.0"}
        """
        response = self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def close(self):
        """Close HTTP client"""
        self.client.close()


# Example usage
if __name__ == "__main__":
    # Initialize client
    mcp = MCPClient("http://localhost:8080")
    
    # Check health
    health = mcp.health_check()
    print(f"MCP Server Status: {health}")
    
    # Browser automation
    result = mcp.navigate("https://example.com")
    print(f"Navigated to: {result['title']}")
    
    # Extract UI
    ui_data = mcp.extract_ui("https://example.com")
    print(f"Found {len(ui_data['ui_data']['inputs'])} inputs")
    
    # API call
    api_result = mcp.api_call("GET", "https://api.example.com/data")
    print(f"API Status: {api_result['status_code']}")
    
    # Close client
    mcp.close()
