"""
AI Selector Healer
Wraps Playwright interactions. When a selector fails:
  1. Captures current page HTML (DOM snapshot)
  2. Sends broken selector + DOM + context to GPT-4o
  3. Gets a replacement selector
  4. Retries the action with the new selector

Usage:
    healer = SelectorHealer()

    # Option A: Direct healing query
    result = healer.heal(
        failed_selector="#old-btn",
        page_html=page.content(),
        element_context="Submit button to save segment",
    )

    # Option B: Safe click (auto-heals on failure)
    healer.safe_click(page, "#submit-btn", "Submit button")

    # Option C: Patch test cases dict with healed selectors
    patched = healer.patch_test_cases(test_cases, healed_map)
"""

import re
import json
import sys
import os
from typing import Dict, List, Optional

from langchain_openai import AzureChatOpenAI

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ai_agent.config import AIConfig
from ai_agent.utils.cache import get_cached_response, set_cached_response


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
HEAL_PROMPT = """\
A Playwright test failed because this CSS/XPath selector no longer exists on the page:
  BROKEN SELECTOR: {failed_selector}

ELEMENT PURPOSE: {element_context}

ERROR MESSAGE: {error_message}

Below is the current page HTML (truncated to relevant sections):
{page_html_excerpt}

Your task:
1. Find the element that best matches the purpose described above.
2. Return the most reliable selector for it (prefer: data-testid, id, aria-label, role+text).
3. Provide up to 2 alternative selectors as fallbacks.
4. Rate your confidence 0.0–1.0.

Respond ONLY with valid JSON:
{{
  "new_selector": "...",
  "alternatives": ["...", "..."],
  "confidence": 0.9,
  "reasoning": "one sentence"
}}
"""


# ---------------------------------------------------------------------------
# Selector Healer class
# ---------------------------------------------------------------------------
class SelectorHealer:
    """
    AI-powered Playwright selector healer.
    Fixes broken selectors at runtime using GPT-4o + DOM snapshot.
    """

    # Regex patterns to extract a selector from Playwright error messages
    SELECTOR_PATTERNS = [
        r"waiting for selector ['\"](.+?)['\"]",
        r"No element found for selector: ['\"]?(.+?)['\"]?$",
        r"locator\(['\"](.+?)['\"]\)",
        r"selector ['\"](.+?)['\"] resolved to",
        r"Timeout.*?waiting for.*?['\"](.+?)['\"]",
    ]

    # Max chars of HTML to send (token control)
    HTML_EXCERPT_LIMIT = 4000

    def __init__(self):
        AIConfig.validate()
        self.llm = AzureChatOpenAI(
            azure_deployment=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            openai_api_version=AIConfig.AZURE_OPENAI_API_VERSION,
            azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
            api_key=AIConfig.AZURE_OPENAI_API_KEY,
            temperature=0.2,    # Low – we want precise selector suggestions
            max_tokens=500,     # Small response (just JSON)
        )

    # ------------------------------------------------------------------
    def heal(
        self,
        failed_selector: str,
        page_html: str,
        element_context: str,
        error_message: str = "",
    ) -> Dict:
        """
        Ask GPT-4o for a replacement selector.

        Args:
            failed_selector: The selector that broke (e.g. "#old-login-btn")
            page_html: Current full page HTML (page.content())
            element_context: What the element does (e.g. "Login button")
            error_message: Original Playwright error string

        Returns:
            {
                "new_selector": str,
                "alternatives": List[str],
                "confidence": float,
                "reasoning": str
            }
        """
        if not failed_selector:
            return self._empty_result("No failed selector provided")

        # Truncate HTML to relevant section (find context around broken selector)
        html_excerpt = self._extract_relevant_html(page_html, failed_selector)

        prompt = HEAL_PROMPT.format(
            failed_selector=failed_selector,
            element_context=element_context,
            error_message=error_message[:300] if error_message else "Unknown",
            page_html_excerpt=html_excerpt,
        )

        # Cache check (same broken selector + same page → same fix)
        cache_key = f"heal:{failed_selector}:{hash(html_excerpt)}"
        cached = get_cached_response(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                pass

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()

            # Strip markdown fences if present
            if content.startswith("```"):
                content = re.sub(r"```(?:json)?", "", content).strip().rstrip("`")

            result = json.loads(content)
            set_cached_response(cache_key, json.dumps(result))
            return result

        except Exception as e:
            return self._empty_result(f"LLM call failed: {e}")

    # ------------------------------------------------------------------
    def safe_click(self, page, selector: str, context: str = "", timeout: int = 5000) -> bool:
        """
        Click an element; if it fails, attempt to heal the selector and retry.

        Args:
            page: Playwright page object
            selector: Target CSS/XPath selector
            context: What this element does (for healing prompt)
            timeout: ms to wait before declaring failure

        Returns:
            True if click succeeded (original or healed), False otherwise
        """
        try:
            page.click(selector, timeout=timeout)
            return True
        except Exception as e:
            print(f"[SelectorHealer] ⚠️  Click failed: {selector}")
            print(f"  Error: {str(e)[:100]}")

            # Capture DOM and attempt healing
            try:
                html = page.content()
            except Exception:
                html = ""

            heal_result = self.heal(
                failed_selector=selector,
                page_html=html,
                element_context=context or f"Element to click: {selector}",
                error_message=str(e),
            )

            new_selector = heal_result.get("new_selector", "")
            confidence = heal_result.get("confidence", 0)

            if new_selector and confidence >= 0.6:
                print(f"[SelectorHealer] 🔧 Trying healed selector: {new_selector} (conf={confidence})")
                try:
                    page.click(new_selector, timeout=timeout)
                    print(f"[SelectorHealer] ✅ Healed click succeeded")
                    return True
                except Exception as e2:
                    # Try alternatives
                    for alt in heal_result.get("alternatives", []):
                        try:
                            page.click(alt, timeout=2000)
                            print(f"[SelectorHealer] ✅ Alternative click succeeded: {alt}")
                            return True
                        except Exception:
                            continue

            print(f"[SelectorHealer] ❌ Could not heal: {selector}")
            return False

    # ------------------------------------------------------------------
    def safe_fill(self, page, selector: str, value: str, context: str = "", timeout: int = 5000) -> bool:
        """Fill a field; auto-heal selector on failure."""
        try:
            page.fill(selector, value, timeout=timeout)
            return True
        except Exception as e:
            print(f"[SelectorHealer] ⚠️  Fill failed: {selector}")
            try:
                html = page.content()
            except Exception:
                html = ""

            heal_result = self.heal(
                failed_selector=selector,
                page_html=html,
                element_context=context or f"Input field: {selector}",
                error_message=str(e),
            )

            new_selector = heal_result.get("new_selector", "")
            if new_selector and heal_result.get("confidence", 0) >= 0.6:
                try:
                    page.fill(new_selector, value, timeout=timeout)
                    print(f"[SelectorHealer] ✅ Healed fill: {new_selector}")
                    return True
                except Exception:
                    pass

            return False

    # ------------------------------------------------------------------
    def extract_selector_from_error(self, error_message: str) -> Optional[str]:
        """
        Parse a Playwright error message and extract the broken selector.

        Returns:
            The selector string, or None if not found.
        """
        for pattern in self.SELECTOR_PATTERNS:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    # ------------------------------------------------------------------
    def patch_test_cases(self, test_cases: List[Dict], healed_map: Dict) -> List[Dict]:
        """
        Update test case step selectors based on the healed_map.

        Args:
            test_cases: List of test case dicts (each with 'steps' list)
            healed_map: {test_name: {"old": old_sel, "new": new_sel}}

        Returns:
            Patched test cases list
        """
        if not healed_map:
            return test_cases

        patched = []
        for tc in test_cases:
            name = tc.get("scenario", tc.get("name", ""))
            heal_info = healed_map.get(name)
            if not heal_info:
                patched.append(tc)
                continue

            old_sel = heal_info.get("old", "")
            new_sel = heal_info.get("new", "")
            if not old_sel or not new_sel:
                patched.append(tc)
                continue

            # Deep replace old selector with new in all steps
            tc_str = json.dumps(tc)
            tc_str = tc_str.replace(
                json.dumps(old_sel)[1:-1],  # strip surrounding quotes
                json.dumps(new_sel)[1:-1],
            )
            try:
                patched.append(json.loads(tc_str))
            except Exception:
                patched.append(tc)

        return patched

    # ------------------------------------------------------------------
    # ── Helpers ────────────────────────────────────────────────────────
    # ------------------------------------------------------------------

    def _extract_relevant_html(self, full_html: str, failed_selector: str) -> str:
        """
        Extract a relevant excerpt from the full HTML.
        Prioritises: the closest tag to where the selector should be,
        or falls back to the first N chars.
        """
        if not full_html:
            return "(no HTML available)"

        # Try to find a nearby section (simple heuristic)
        keyword = re.sub(r'[#.\[\]@="*>+~^$|:]', ' ', failed_selector).split()
        keyword = [k for k in keyword if len(k) > 2]

        if keyword:
            best_pos = -1
            for kw in keyword:
                pos = full_html.lower().find(kw.lower())
                if pos != -1:
                    best_pos = pos
                    break

            if best_pos != -1:
                start = max(0, best_pos - 1000)
                end = min(len(full_html), best_pos + 3000)
                return full_html[start:end]

        # Fallback: first N chars
        return full_html[:self.HTML_EXCERPT_LIMIT]

    @staticmethod
    def _empty_result(reason: str) -> Dict:
        return {
            "new_selector": "",
            "alternatives": [],
            "confidence": 0.0,
            "reasoning": reason,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
_healer_instance: Optional[SelectorHealer] = None


def get_selector_healer() -> SelectorHealer:
    global _healer_instance
    if _healer_instance is None:
        _healer_instance = SelectorHealer()
    return _healer_instance


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Quick smoke test (no real page needed)
    healer = SelectorHealer()

    sample_html = """
    <html><body>
      <header>
        <nav>
          <button data-testid="nav-home" class="btn-primary">Home</button>
          <button data-testid="nav-segment" aria-label="Go to Segments">Segments</button>
        </nav>
      </header>
    </body></html>
    """

    result = healer.heal(
        failed_selector="#old-segment-btn",
        page_html=sample_html,
        element_context="Navigation button to open Segments module",
        error_message="Timeout 30000ms exceeded waiting for selector '#old-segment-btn'",
    )
    print(json.dumps(result, indent=2))

    # Test selector extraction
    error = "TimeoutError: Timeout 30000ms exceeded waiting for selector '#add-rule-btn'"
    print("\nExtracted:", healer.extract_selector_from_error(error))
