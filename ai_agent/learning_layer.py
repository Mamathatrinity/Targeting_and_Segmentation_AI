"""
Learning Layer - Simple Failure History Tracker

Stores test failures and uses them to improve future test generation.
This implements GAP 5 from the PDF (Learning Layer).

Features:
- Stores failures to JSON file
- Provides failure history to Planner
- Tracks failure patterns over time
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any


class LearningLayer:
    """
    Simple learning layer that stores and retrieves failure history
    """
    
    def __init__(self, storage_path: str = "learning_data"):
        self.storage_path = storage_path
        self.failures_file = os.path.join(storage_path, "failures.json")
        os.makedirs(storage_path, exist_ok=True)
    
    def store_failures(self, test_results: Dict[str, Any], url: str) -> None:
        """
        Store failures from test execution.
        
        Args:
            test_results: Test execution results
            url: URL that was tested
        """
        failures = [
            t for t in test_results.get("test_results", [])
            if t.get("status") == "failed"
        ]
        
        if not failures:
            return
        
        # Load existing failures
        history = self._load_history()
        
        # Add new failures
        entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "failures": [
                {
                    "test_name": f["name"],
                    "error_type": f.get("error_type", "unknown"),
                    "failure_reason": f.get("failure_reason", ""),
                    "failed_step": f.get("failed_step")
                }
                for f in failures
            ]
        }
        
        history.append(entry)
        
        # Keep only last 50 entries (prevent file from growing too large)
        if len(history) > 50:
            history = history[-50:]
        
        # Save
        self._save_history(history)
    
    def get_recent_failures(self, limit: int = 10) -> List[Dict]:
        """
        Get recent failure history.
        
        Args:
            limit: Maximum number of recent failures to return
            
        Returns:
            List of recent failure entries
        """
        history = self._load_history()
        return history[-limit:] if history else []
    
    def get_failure_summary(self) -> Dict[str, Any]:
        """
        Get summary of failure patterns.
        
        Returns:
            Summary with common error types and patterns
        """
        history = self._load_history()
        
        if not history:
            return {"total_failures": 0, "patterns": []}
        
        # Count error types
        error_counts = {}
        for entry in history:
            for failure in entry.get("failures", []):
                error_type = failure.get("error_type", "unknown")
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # Sort by frequency
        patterns = sorted(
            [{"type": k, "count": v} for k, v in error_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )
        
        return {
            "total_failures": sum(len(e.get("failures", [])) for e in history),
            "total_runs": len(history),
            "patterns": patterns[:5]  # Top 5
        }
    
    def _load_history(self) -> List[Dict]:
        """Load failure history from file"""
        if not os.path.exists(self.failures_file):
            return []
        
        try:
            with open(self.failures_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_history(self, history: List[Dict]) -> None:
        """Save failure history to file"""
        with open(self.failures_file, 'w') as f:
            json.dump(history, f, indent=2)


# Singleton instance
_learning_layer = None

def get_learning_layer() -> LearningLayer:
    """Get global learning layer instance"""
    global _learning_layer
    if _learning_layer is None:
        _learning_layer = LearningLayer()
    return _learning_layer


if __name__ == "__main__":
    # Example usage
    learning = get_learning_layer()
    
    # Store some failures
    example_results = {
        "test_results": [
            {
                "name": "Login test",
                "status": "failed",
                "error_type": "element_not_found",
                "failure_reason": "Button not found",
                "failed_step": 3
            }
        ]
    }
    
    learning.store_failures(example_results, "https://example.com")
    
    # Get summary
    summary = learning.get_failure_summary()
    print(json.dumps(summary, indent=2))
