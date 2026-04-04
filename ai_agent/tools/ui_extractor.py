"""
UI Extractor Tool (NO AI)
Extracts UI elements using Playwright for agent analysis
"""
from playwright.sync_api import sync_playwright
from typing import Dict, List
import json


class UIExtractor:
    """Extracts structured UI data without AI"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
    
    def extract_ui_elements(self, url: str) -> Dict:
        """
        Extract UI elements from a page
        
        Args:
            url: Target URL to analyze
            
        Returns:
            Structured UI data with inputs, buttons, dropdowns, etc.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            
            try:
                # Navigate to URL
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)  # Wait for dynamic content
                
                # Extract all interactive elements
                elements = page.evaluate("""
                    () => {
                        const results = {
                            inputs: [],
                            buttons: [],
                            dropdowns: [],
                            checkboxes: [],
                            links: []
                        };
                        
                        // Extract input fields
                        document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="number"]')
                            .forEach(el => {
                                results.inputs.push({
                                    type: el.type,
                                    name: el.name || '',
                                    id: el.id || '',
                                    placeholder: el.placeholder || '',
                                    label: el.labels?.[0]?.innerText || ''
                                });
                            });
                        
                        // Extract buttons
                        document.querySelectorAll('button, input[type="button"], input[type="submit"]')
                            .forEach(el => {
                                results.buttons.push({
                                    text: el.innerText || el.value || '',
                                    id: el.id || '',
                                    type: el.type || 'button'
                                });
                            });
                        
                        // Extract dropdowns
                        document.querySelectorAll('select')
                            .forEach(el => {
                                const options = Array.from(el.options).map(opt => opt.text);
                                results.dropdowns.push({
                                    name: el.name || '',
                                    id: el.id || '',
                                    label: el.labels?.[0]?.innerText || '',
                                    options: options.slice(0, 5)  // First 5 options only for token efficiency
                                });
                            });
                        
                        // Extract checkboxes
                        document.querySelectorAll('input[type="checkbox"]')
                            .forEach(el => {
                                results.checkboxes.push({
                                    name: el.name || '',
                                    id: el.id || '',
                                    label: el.labels?.[0]?.innerText || ''
                                });
                            });
                        
                        // Extract important links (navigation)
                        document.querySelectorAll('nav a[href], .menu a[href]')
                            .forEach(el => {
                                results.links.push({
                                    text: el.innerText?.trim() || '',
                                    href: el.href
                                });
                            });
                        
                        return results;
                    }
                """)
                
                # Get page title and URL
                page_info = {
                    "url": page.url,
                    "title": page.title(),
                    "elements": elements
                }
                
                return page_info
                
            finally:
                browser.close()
    
    def extract_summary(self, url: str) -> Dict:
        """Quick extraction of element counts only (token-efficient)"""
        full_data = self.extract_ui_elements(url)
        
        return {
            "url": full_data["url"],
            "title": full_data["title"],
            "summary": {
                "inputs": len(full_data["elements"]["inputs"]),
                "buttons": len(full_data["elements"]["buttons"]),
                "dropdowns": len(full_data["elements"]["dropdowns"]),
                "checkboxes": len(full_data["elements"]["checkboxes"]),
                "links": len(full_data["elements"]["links"])
            },
            "sample_elements": {
                "inputs": full_data["elements"]["inputs"][:3],  # First 3 only
                "buttons": full_data["elements"]["buttons"][:3],
                "dropdowns": full_data["elements"]["dropdowns"][:2]
            }
        }


# Utility function for easy import
def extract_ui(url: str, headless: bool = False) -> Dict:
    """Quick UI extraction function"""
    extractor = UIExtractor(headless=headless)
    return extractor.extract_summary(url)  # Use summary for token efficiency


if __name__ == "__main__":
    # Test extraction
    import sys
    
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://ce-ts-dev.trinitylifesciences.com/segments"
    
    print(f"Extracting UI from: {test_url}")
    extractor = UIExtractor(headless=False)
    data = extractor.extract_summary(test_url)
    
    print(json.dumps(data, indent=2))
