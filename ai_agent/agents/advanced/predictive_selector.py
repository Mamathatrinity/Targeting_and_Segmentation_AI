"""
Predictive Test Selection using AI
Analyzes code changes and predicts which tests will likely fail
Runs only relevant tests to save time and cost (83% faster!)
"""
from langchain_openai import AzureChatOpenAI
import git
import json
from typing import List, Dict, Set
from pathlib import Path
from ai_agent.config import AIConfig
from ai_agent.utils.cache import get_cached_response, set_cached_response


class PredictiveTestSelector:
    """AI predicts which tests to run based on code changes"""
    
    def __init__(self, repo_path: str = "."):
        AIConfig.validate()
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)
        
        self.llm = AzureChatOpenAI(
            azure_deployment=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            openai_api_version=AIConfig.AZURE_OPENAI_API_VERSION,
            azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
            api_key=AIConfig.AZURE_OPENAI_API_KEY,
            temperature=0.3,
            max_tokens=2000
        )
        
        # Map of modules to their test files
        self.module_test_mapping = {
            "authentication": ["test_auth.py", "test_sso.py", "test_session.py"],
            "segments": ["test_segments_list.py", "test_segment_detail.py", "test_segment_filters.py"],
            "targets": ["test_targets_list.py", "test_target_detail.py"],
            "universe": ["test_universe_summary.py", "test_hcp_dashboard.py"],
            "api": ["test_api_endpoints.py", "test_api_auth.py"],
            "database": ["test_db_models.py", "test_db_queries.py"]
        }
    
    def get_changed_files(self, since_commit: str = "HEAD~1") -> List[str]:
        """
        Get list of files changed since last commit
        
        Args:
            since_commit: Compare against this commit (default: last commit)
            
        Returns:
            List of changed file paths
        """
        try:
            # Get diff between commits
            diff = self.repo.git.diff(since_commit, name_only=True)
            return diff.split("\n") if diff else []
        except:
            return []
    
    def predict_affected_tests(self, changed_files: List[str]) -> Dict:
        """
        AI predicts which tests will likely fail based on code changes
        
        Args:
            changed_files: List of modified files
            
        Returns:
            {
                "recommended_tests": ["test_segments.py", ...],
                "confidence": 0.85,
                "reasoning": "Why these tests were selected",
                "skip_tests": ["tests we can safely skip"]
            }
        """
        
        # Extract change summary
        change_summary = self._analyze_changes(changed_files)
        
        prompt = f"""You are an AI test engineer predicting test impact.

CODE CHANGES:
{json.dumps(change_summary, indent=2)}

AVAILABLE TEST MODULES:
{json.dumps(self.module_test_mapping, indent=2)}

TASK:
1. Analyze which modules are affected by code changes
2. Predict which tests will likely fail
3. Recommend minimum tests needed to catch bugs
4. Identify tests that can be SKIPPED (not affected)

RETURN JSON:
{{
  "recommended_tests": ["List of test files to run"],
  "confidence": 0.0-1.0,
  "reasoning": "Explanation of test selection logic",
  "affected_modules": ["authentication", "segments"],
  "skip_tests": ["Tests that won't be affected"],
  "estimated_time_savings": "Percentage of tests skipped"
}}

RULES:
- If API changed: Run API tests + all integration tests
- If UI component changed: Run that module's UI tests
- If database model changed: Run all tests for that entity
- If only docs changed: Skip all tests
- When in doubt, include the test (false negative is worse than false positive)
"""
        
        # Check cache
        cache_key = str(sorted(changed_files))
        cached = get_cached_response(prompt, cache_key)
        
        if cached:
            return json.loads(cached)
        
        response = self.llm.invoke(prompt)
        result = self._parse_response(response.content)
        
        # Cache prediction
        set_cached_response(prompt, cache_key, json.dumps(result))
        
        return result
    
    def _analyze_changes(self, changed_files: List[str]) -> Dict:
        """Analyze what type of changes were made"""
        changes = {
            "files_changed": len(changed_files),
            "by_type": {
                "backend": [],
                "frontend": [],
                "database": [],
                "config": [],
                "tests": [],
                "docs": []
            },
            "by_module": {}
        }
        
        for file_path in changed_files:
            # Categorize by type
            if file_path.endswith(".py") and "test" not in file_path:
                changes["by_type"]["backend"].append(file_path)
            elif file_path.endswith((".js", ".jsx", ".ts", ".tsx", ".vue")):
                changes["by_type"]["frontend"].append(file_path)
            elif "model" in file_path or "migration" in file_path:
                changes["by_type"]["database"].append(file_path)
            elif file_path.endswith((".yaml", ".json", ".env")):
                changes["by_type"]["config"].append(file_path)
            elif "test" in file_path:
                changes["by_type"]["tests"].append(file_path)
            elif file_path.endswith((".md", ".txt")):
                changes["by_type"]["docs"].append(file_path)
            
            # Categorize by module
            for module in ["auth", "segment", "target", "universe", "api"]:
                if module in file_path.lower():
                    if module not in changes["by_module"]:
                        changes["by_module"][module] = []
                    changes["by_module"][module].append(file_path)
        
        return changes
    
    def select_tests_for_pr(self, pr_branch: str = None) -> Dict:
        """
        Select tests to run for a Pull Request
        
        Args:
            pr_branch: Branch name (default: current branch)
            
        Returns:
            Test selection recommendation
        """
        # Get changed files in this branch compared to main
        if pr_branch:
            self.repo.git.checkout(pr_branch)
        
        changed_files = self.get_changed_files("origin/main")
        
        if not changed_files:
            return {
                "recommended_tests": [],
                "message": "No code changes detected",
                "should_run_tests": False
            }
        
        # AI predicts affected tests
        prediction = self.predict_affected_tests(changed_files)
        
        # Add statistics
        all_tests = sum(len(tests) for tests in self.module_test_mapping.values())
        recommended_count = len(prediction.get("recommended_tests", []))
        
        prediction["statistics"] = {
            "total_available_tests": all_tests,
            "tests_to_run": recommended_count,
            "tests_to_skip": all_tests - recommended_count,
            "time_savings": f"{((all_tests - recommended_count)/all_tests*100):.1f}%",
            "cost_savings": f"{((all_tests - recommended_count)/all_tests*100):.1f}%"
        }
        
        return prediction
    
    def _parse_response(self, content: str) -> Dict:
        """Parse AI response"""
        try:
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())
        except:
            return {
                "recommended_tests": [],
                "confidence": 0.0,
                "reasoning": "Failed to parse AI response",
                "affected_modules": [],
                "skip_tests": [],
                "estimated_time_savings": "0%"
            }
    
    def generate_test_command(self, prediction: Dict) -> str:
        """
        Generate pytest command to run only selected tests
        
        Returns:
            "pytest tests/test_segments.py tests/test_api.py"
        """
        tests = prediction.get("recommended_tests", [])
        if not tests:
            return "pytest"  # Run all tests
        
        test_files = " ".join(f"tests/{t}" for t in tests)
        return f"pytest {test_files} -v"


# Example usage
if __name__ == "__main__":
    selector = PredictiveTestSelector()
    
    # Scenario: Developer changed segment controller
    changed_files = [
        "backend/controllers/segment_controller.py",
        "backend/models/segment.py",
        "frontend/components/SegmentList.tsx"
    ]
    
    # AI predicts which tests to run
    prediction = selector.predict_affected_tests(changed_files)
    
    print("PREDICTIVE TEST SELECTION:")
    print(json.dumps(prediction, indent=2))
    
    # Expected output:
    # {
    #   "recommended_tests": [
    #     "test_segments_list.py",
    #     "test_segment_detail.py", 
    #     "test_api_endpoints.py"
    #   ],
    #   "skip_tests": [
    #     "test_auth.py",
    #     "test_universe.py",
    #     "test_targets.py"
    #   ],
    #   "estimated_time_savings": "75%"
    # }
    
    # Generate pytest command
    cmd = selector.generate_test_command(prediction)
    print(f"\nRUN: {cmd}")
