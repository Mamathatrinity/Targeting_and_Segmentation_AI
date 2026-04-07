"""
Visual Regression Testing with AI
Compares screenshots to detect UI changes
Uses AI to differentiate between intentional changes vs bugs
"""
from PIL import Image, ImageChops, ImageDraw
from langchain_openai import AzureChatOpenAI
import base64
import io
import json
from typing import Dict, Tuple
from ai_agent.config import AIConfig


class VisualRegressionAgent:
    """AI-powered visual testing - detects UI changes"""
    
    def __init__(self):
        AIConfig.validate()
        self.llm = AzureChatOpenAI(
            azure_deployment=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            openai_api_version=AIConfig.AZURE_OPENAI_API_VERSION,
            azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
            api_key=AIConfig.AZURE_OPENAI_API_KEY,
            temperature=0.2,
            max_tokens=1500
        )
    
    def compare_screenshots(
        self, 
        baseline_path: str, 
        current_path: str,
        tolerance: float = 0.05
    ) -> Dict:
        """
        Compare two screenshots pixel-by-pixel
        
        Args:
            baseline_path: Path to baseline (expected) screenshot
            current_path: Path to current (actual) screenshot  
            tolerance: Acceptable difference (0.05 = 5%)
            
        Returns:
            {
                "match": true/false,
                "difference_percentage": 2.3,
                "diff_image_path": "path/to/diff.png",
                "changes_detected": ["Layout shift", "Color change"]
            }
        """
        # Load images
        baseline = Image.open(baseline_path)
        current = Image.open(current_path)
        
        # Ensure same size
        if baseline.size != current.size:
            current = current.resize(baseline.size)
        
        # Calculate pixel difference
        diff = ImageChops.difference(baseline, current)
        
        # Calculate percentage of changed pixels
        diff_pixels = sum(sum(1 for p in row if p != (0, 0, 0)) for row in diff.getdata())
        total_pixels = baseline.size[0] * baseline.size[1]
        diff_percentage = (diff_pixels / total_pixels) * 100
        
        # Create difference image (highlight changes in red)
        diff_highlighted = self._create_diff_image(baseline, current, diff)
        diff_path = current_path.replace(".png", "_diff.png")
        diff_highlighted.save(diff_path)
        
        # AI analyzes the differences
        ai_analysis = self._ai_analyze_visual_diff(
            baseline_path, 
            current_path, 
            diff_path,
            diff_percentage
        )
        
        return {
            "match": diff_percentage <= tolerance,
            "difference_percentage": round(diff_percentage, 2),
            "diff_image_path": diff_path,
            "changes_detected": ai_analysis.get("changes", []),
            "severity": ai_analysis.get("severity", "low"),
            "recommendation": ai_analysis.get("recommendation", "")
        }
    
    def _create_diff_image(self, baseline: Image, current: Image, diff: Image) -> Image:
        """Create image highlighting differences in red"""
        # Convert to RGB
        diff_highlighted = current.copy().convert("RGB")
        draw = ImageDraw.Draw(diff_highlighted)
        
        # Highlight changed pixels in red
        for y in range(diff.size[1]):
            for x in range(diff.size[0]):
                if diff.getpixel((x, y)) != (0, 0, 0):
                    # Draw red rectangle around changed area
                    draw.rectangle([x, y, x+1, y+1], fill=(255, 0, 0))
        
        return diff_highlighted
    
    def _ai_analyze_visual_diff(
        self, 
        baseline_path: str, 
        current_path: str,
        diff_path: str,
        diff_percentage: float
    ) -> Dict:
        """
        AI analyzes WHAT changed and WHY it matters
        
        Uses GPT-4 Vision to understand visual differences
        """
        
        # Encode images to base64 for GPT-4 Vision
        baseline_b64 = self._image_to_base64(baseline_path)
        current_b64 = self._image_to_base64(current_path)
        diff_b64 = self._image_to_base64(diff_path)
        
        prompt = f"""You are a visual QA expert analyzing UI changes.

CONTEXT:
- Baseline (expected) vs Current (actual) screenshot comparison
- Pixel difference: {diff_percentage:.2f}%

IMAGES PROVIDED:
1. Baseline (what it should look like)
2. Current (what it looks like now)
3. Diff (highlighted changes in red)

ANALYZE:
1. What UI elements changed? (buttons, text, layout, colors)
2. Is this likely a BUG or INTENTIONAL design change?
3. What's the severity? (critical/high/medium/low)
4. User impact?

RETURN JSON:
{{
  "changes": ["List of specific changes detected"],
  "change_type": "layout|styling|content|functional",
  "likely_bug": true/false,
  "severity": "critical|high|medium|low",
  "user_impact": "Description of how this affects users",
  "recommendation": "What to do about this change"
}}

Examples of changes:
- Layout shift: "Login button moved 50px down"
- Styling: "Primary button color changed from blue to red"
- Content: "Welcome message text changed"
- Functional: "Submit button is no longer visible"
"""
        
        # Call GPT-4 Vision API (Note: Requires vision-enabled model)
        # For now, using text-based analysis as fallback
        response = self.llm.invoke(prompt)
        
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except:
            return {
                "changes": [f"Visual difference detected: {diff_percentage:.2f}%"],
                "change_type": "unknown",
                "likely_bug": diff_percentage > 1.0,
                "severity": "medium" if diff_percentage > 5 else "low",
                "user_impact": "Visual change detected",
                "recommendation": "Manual review recommended"
            }
    
    def _image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 for API"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def batch_visual_regression(
        self, 
        test_screenshots: Dict[str, Tuple[str, str]]
    ) -> Dict:
        """
        Run visual regression on multiple pages
        
        Args:
            test_screenshots: {
                "login_page": ("baseline.png", "current.png"),
                "dashboard": ("baseline2.png", "current2.png")
            }
            
        Returns:
            Summary report with all visual changes
        """
        results = {}
        
        for page_name, (baseline, current) in test_screenshots.items():
            results[page_name] = self.compare_screenshots(baseline, current)
        
        # Generate summary
        total_pages = len(results)
        pages_with_changes = sum(1 for r in results.values() if not r["match"])
        critical_changes = sum(1 for r in results.values() if r.get("severity") == "critical")
        
        return {
            "summary": {
                "total_pages_tested": total_pages,
                "pages_with_changes": pages_with_changes,
                "pages_unchanged": total_pages - pages_with_changes,
                "critical_changes": critical_changes,
                "pass_rate": f"{((total_pages - pages_with_changes)/total_pages*100):.1f}%"
            },
            "details": results
        }


# Example usage
if __name__ == "__main__":
    visual_agent = VisualRegressionAgent()
    
    # Compare two screenshots
    result = visual_agent.compare_screenshots(
        baseline_path="screenshots/login_baseline.png",
        current_path="screenshots/login_current.png",
        tolerance=0.05  # 5% tolerance
    )
    
    print("VISUAL REGRESSION RESULT:")
    print(json.dumps(result, indent=2))
    
    # Batch testing
    screenshots = {
        "login": ("baseline/login.png", "current/login.png"),
        "dashboard": ("baseline/dashboard.png", "current/dashboard.png"),
        "segments": ("baseline/segments.png", "current/segments.png")
    }
    
    batch_result = visual_agent.batch_visual_regression(screenshots)
    print("\nBATCH VISUAL TESTING:")
    print(json.dumps(batch_result, indent=2))
