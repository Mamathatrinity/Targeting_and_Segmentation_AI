"""
UI Extractor Tool (NO AI)
Extracts UI elements using MCP Client for agent analysis
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from mcp_server.client import MCPClient
from typing import Dict, List
import json


class UIExtractor:
    """Extracts structured UI data without AI (via MCP Server)"""
    
    def __init__(self, mcp_url: str = "http://localhost:8080"):
        self.mcp = MCPClient(mcp_url)
    
    def extract_ui_elements(self, url: str) -> Dict:
        """
        Extract UI elements from a page
        
        Args:
            url: Target URL to analyze
            
        Returns:
            Structured UI data with inputs, buttons, dropdowns, etc.
        """
        # Use MCP server to extract UI
        result = self.mcp.extract_ui(url)
        
        if result.get("success"):
            return result.get("ui_data", {})
    
    def extract_summary(self, url: str) -> Dict:
        """Ultra-minimal extraction (90% token reduction)"""
        full_data = self.extract_ui_elements(url)
        
        # Compress to absolute minimum - only type and selector
        def compress_elements(elements, key_field='id'):
            compressed = []
            for el in elements[:3]:  # Max 3 samples
                # Build minimal selector
                if el.get('id'):
                    selector = f"#{el['id']}"
                elif el.get('name'):
                    selector = f"[name='{el['name']}']"
                else:
                    selector = f"{el.get('type', 'input')}"
                compressed.append(selector)
            return compressed
        
        return {
            "url": full_data["url"],
            "title": full_data["title"],
            "inputs": compress_elements(full_data["elements"]["inputs"]),
            "buttons": compress_elements(full_data["elements"]["buttons"]),
            "dropdowns": compress_elements(full_data["elements"]["dropdowns"]),
            "total": len(full_data["elements"]["inputs"]) + len(full_data["elements"]["buttons"])
        }


# Utility function for easy import
def extract_ui(url: str, mcp_url: str = "http://localhost:8080") -> Dict:
    """Quick UI extraction function"""
    extractor = UIExtractor(mcp_url=mcp_url)
    return extractor.extract_summary(url)  # Use summary for token efficiency


if __name__ == "__main__":
    # Test extraction
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://ce-ts-dev.trinitylifesciences.com/segments"
    
    print(f"Extracting UI from: {test_url}")
    print("Note: Make sure MCP server is running (python mcp_server/server.py)")
    extractor = UIExtractor()
    data = extractor.extract_summary(test_url)
    
    print(json.dumps(data, indent=2))
