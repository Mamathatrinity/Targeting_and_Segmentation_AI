"""
Self-Healing Tests Module
Automatically fixes broken selectors using AI when tests fail
Based on: Element similarity, text matching, position, and context
"""
from langchain_openai import AzureChatOpenAI
from typing import Dict, List, Optional
import json
from ai_agent.config import AIConfig
from ai_agent.utils.cache import get_cached_response, set_cached_response


class SelfHealingAgent:
    """AI agent that fixes broken test selectors automatically"""
    
    def __init__(self):
        AIConfig.validate()
        self.llm = AzureChatOpenAI(
            azure_deployment=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            openai_api_version=AIConfig.AZURE_OPENAI_API_VERSION,
            azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
            api_key=AIConfig.AZURE_OPENAI_API_KEY,
            temperature=0.3,  # Low temperature for precise selector matching
            max_tokens=1000
        )
    
    def heal_broken_selector(
        self, 
        failed_selector: str, 
        page_html: str, 
        element_context: str,
        screenshot_path: Optional[str] = None
    ) -> Dict:
        """
        AI finds replacement selector when original fails
        
        Args:
            failed_selector: The selector that no longer works (e.g., "#old-login-btn")
            page_html: Current page HTML to search for alternatives
            element_context: What the element does (e.g., "Login button")
            screenshot_path: Optional screenshot for visual analysis
            
        Returns:
            {
                "new_selector": "#new-login-button",
                "confidence": 0.95,
                "reasoning": "Found button with text 'Login' and data-testid attribute",
                "alternatives": ["[data-testid='login']", ".btn-login"]
            }
        """
        
        prompt = f"""You are a test automation expert fixing broken selectors.

FAILED SELECTOR: {failed_selector}
ELEMENT PURPOSE: {element_context}

CURRENT PAGE HTML (truncated for analysis):
{page_html[:5000]}

TASK:
1. Find the BEST replacement selector for this element
2. Prioritize stable selectors: data-testid > id > name > unique class
3. Avoid position-based selectors (nth-child)
4. Ensure selector is specific (matches only one element)

RETURN JSON:
{{
  "new_selector": "exact CSS selector",
  "confidence": 0.0-1.0,
  "reasoning": "why this selector is best",
  "alternatives": ["backup selector 1", "backup selector 2"],
  "element_found": true/false
}}
"""
        
        # Check cache (same HTML + same failed selector = same answer)
        cache_key = f"{failed_selector}_{hash(page_html[:1000])}"
        cached = get_cached_response(prompt, cache_key)
        
        if cached:
            return json.loads(cached)
        
        response = self.llm.invoke(prompt)
        result = self._parse_response(response.content)
        
        # Cache for future
        set_cached_response(prompt, cache_key, json.dumps(result))
        
        return result
    
    def auto_heal_test(self, test_failure: Dict, page_source: str) -> Dict:
        """
        Automatically heal a failed test by finding new selectors
        
        Args:
            test_failure: {
                "test_name": "Login test",
                "failed_step": {"action": "click", "selector": "#login-btn"},
                "error": "Element not found: #login-btn"
            }
            page_source: Current page HTML
            
        Returns:
            {
                "healed": true/false,
                "updated_selector": "#new-login-button",
                "updated_test": {complete updated test}
            }
        """
        
        failed_step = test_failure.get("failed_step", {})
        old_selector = failed_step.get("selector", "")
        action = failed_step.get("action", "")
        
        # Determine element purpose from action and selector
        element_context = self._infer_element_purpose(old_selector, action)
        
        # AI finds new selector
        healing_result = self.heal_broken_selector(
            failed_selector=old_selector,
            page_html=page_source,
            element_context=element_context
        )
        
        if healing_result.get("element_found") and healing_result.get("confidence", 0) > 0.7:
            # Update test with new selector
            updated_test = test_failure.copy()
            updated_test["failed_step"]["selector"] = healing_result["new_selector"]
            
            return {
                "healed": True,
                "old_selector": old_selector,
                "new_selector": healing_result["new_selector"],
                "confidence": healing_result["confidence"],
                "reasoning": healing_result["reasoning"],
                "alternatives": healing_result.get("alternatives", []),
                "updated_test": updated_test
            }
        else:
            return {
                "healed": False,
                "reason": "Could not find suitable replacement selector",
                "confidence": healing_result.get("confidence", 0)
            }
    
    def _infer_element_purpose(self, selector: str, action: str) -> str:
        """Infer what the element does from selector and action"""
        purposes = {
            "login": "Login button",
            "submit": "Submit button",
            "email": "Email input field",
            "password": "Password input field",
            "search": "Search input",
            "filter": "Filter dropdown",
            "create": "Create button",
            "delete": "Delete button",
            "cancel": "Cancel button"
        }
        
        selector_lower = selector.lower()
        for keyword, purpose in purposes.items():
            if keyword in selector_lower:
                return purpose
        
        # Fallback based on action
        action_map = {
            "click": "Clickable button or link",
            "fill": "Text input field",
            "select": "Dropdown select element"
        }
        
        return action_map.get(action, "Interactive element")
    
    def _parse_response(self, content: str) -> Dict:
        """Parse LLM JSON response"""
        try:
            # Remove markdown if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content.strip())
        except json.JSONDecodeError:
            return {
                "new_selector": "",
                "confidence": 0.0,
                "reasoning": "Failed to parse AI response",
                "alternatives": [],
                "element_found": False
            }
    
    def batch_heal_tests(self, failed_tests: List[Dict], page_sources: Dict[str, str]) -> List[Dict]:
        """
        Heal multiple failed tests at once
        
        Args:
            failed_tests: List of test failures
            page_sources: {url: html_source} mapping
            
        Returns:
            List of healing results
        """
        results = []
        
        for test in failed_tests:
            url = test.get("url", "")
            page_source = page_sources.get(url, "")
            
            if page_source:
                healing_result = self.auto_heal_test(test, page_source)
                healing_result["test_name"] = test.get("test_name")
                results.append(healing_result)
        
        return results
    
    def generate_healing_report(self, healing_results: List[Dict]) -> Dict:
        """Generate summary report of healing session"""
        total = len(healing_results)
        healed = sum(1 for r in healing_results if r.get("healed"))
        failed_to_heal = total - healed
        
        high_confidence = sum(1 for r in healing_results if r.get("confidence", 0) > 0.9)
        
        return {
            "total_failures": total,
            "successfully_healed": healed,
            "failed_to_heal": failed_to_heal,
            "heal_rate": f"{(healed/total*100):.1f}%" if total > 0 else "0%",
            "high_confidence_heals": high_confidence,
            "details": healing_results
        }


# Example usage
if __name__ == "__main__":
    healer = SelfHealingAgent()
    
    # Simulate a test failure
    test_failure = {
        "test_name": "Login test",
        "failed_step": {
            "action": "click",
            "selector": "#login-btn"  # Old selector that broke
        },
        "error": "Element not found: #login-btn",
        "url": "https://app.example.com/login"
    }
    
    # Simulated page HTML (in reality, this comes from Playwright)
    page_html = """
    <html>
        <body>
            <form>
                <input type="email" id="email" />
                <input type="password" id="password" />
                <button data-testid="login-button" class="btn-primary">Login</button>
            </form>
        </body>
    </html>
    """
    
    # AI heals the test
    result = healer.auto_heal_test(test_failure, page_html)
    
    print("SELF-HEALING RESULT:")
    print(json.dumps(result, indent=2))
    
    # Expected output:
    # {
    #   "healed": true,
    #   "new_selector": "[data-testid='login-button']",
    #   "confidence": 0.95,
    #   "reasoning": "Found button with data-testid attribute (most stable)"
    # }
