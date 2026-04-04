"""
Cost Tracker - Monitor LLM Token Usage and Costs
Helps track API costs for Azure GPT-4o usage
"""

class CostTracker:
    """
    Simple cost tracker for LLM usage
    
    Pricing based on Azure GPT-4o (approximate):
    - Input: $0.005 per 1K tokens
    - Output: $0.015 per 1K tokens
    """
    
    # Azure GPT-4o pricing (update these if pricing changes)
    INPUT_COST_PER_1K = 0.005   # $0.005 per 1K input tokens
    OUTPUT_COST_PER_1K = 0.015  # $0.015 per 1K output tokens
    
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.agent_costs = {}  # Track cost per agent
    
    def add_tokens(self, input_tokens: int, output_tokens: int, agent_name: str = "unknown"):
        """
        Add token usage
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            agent_name: Name of the agent (planner, designer, etc.)
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        # Track per agent
        if agent_name not in self.agent_costs:
            self.agent_costs[agent_name] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0
            }
        
        self.agent_costs[agent_name]["input_tokens"] += input_tokens
        self.agent_costs[agent_name]["output_tokens"] += output_tokens
        self.agent_costs[agent_name]["cost"] = self._calculate_cost(
            self.agent_costs[agent_name]["input_tokens"],
            self.agent_costs[agent_name]["output_tokens"]
        )
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for given tokens"""
        input_cost = (input_tokens / 1000) * self.INPUT_COST_PER_1K
        output_cost = (output_tokens / 1000) * self.OUTPUT_COST_PER_1K
        return input_cost + output_cost
    
    def get_total_cost(self) -> float:
        """Get total estimated cost"""
        return self._calculate_cost(self.total_input_tokens, self.total_output_tokens)
    
    def get_summary(self) -> dict:
        """Get cost summary"""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "estimated_cost_usd": round(self.get_total_cost(), 4),
            "agent_breakdown": self.agent_costs
        }
    
    def print_summary(self):
        """Print formatted cost summary"""
        print("\n" + "="*60)
        print("💰 Cost Summary")
        print("="*60)
        
        print(f"\nTotal Tokens:")
        print(f"  Input:  {self.total_input_tokens:,} tokens")
        print(f"  Output: {self.total_output_tokens:,} tokens")
        print(f"  Total:  {self.total_input_tokens + self.total_output_tokens:,} tokens")
        
        print(f"\nEstimated Cost: ${self.get_total_cost():.4f} USD")
        
        if self.agent_costs:
            print(f"\nBreakdown by Agent:")
            for agent, data in sorted(self.agent_costs.items(), 
                                     key=lambda x: x[1]["cost"], 
                                     reverse=True):
                print(f"  {agent}:")
                print(f"    Tokens: {data['input_tokens'] + data['output_tokens']:,}")
                print(f"    Cost:   ${data['cost']:.4f}")
        
        print("="*60)
    
    def reset(self):
        """Reset all counters"""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.agent_costs = {}


# Global instance
_tracker = None

def get_cost_tracker() -> CostTracker:
    """Get global cost tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker


if __name__ == "__main__":
    # Example usage
    tracker = get_cost_tracker()
    
    # Simulate some usage
    tracker.add_tokens(150, 300, "planner")
    tracker.add_tokens(200, 450, "designer")
    tracker.add_tokens(100, 180, "validator")
    
    # Print summary
    tracker.print_summary()
    
    # Get programmatic summary
    import json
    print("\nJSON Summary:")
    print(json.dumps(tracker.get_summary(), indent=2))
