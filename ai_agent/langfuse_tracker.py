"""
Langfuse Integration for Observability
Tracks all LLM calls, prompts, responses, tokens, and costs
"""
from typing import Optional, Any
import os


class LangfuseTracker:
    """Optional Langfuse tracking wrapper"""
    
    def __init__(self):
        self.enabled = False
        self.langfuse = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Langfuse if credentials are available"""
        try:
            from langfuse import Langfuse
            
            public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            
            if public_key and secret_key:
                self.langfuse = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host
                )
                self.enabled = True
                print("Langfuse tracking enabled")
            else:
                print("WARNING: Langfuse credentials not found - tracking disabled")
        
        except ImportError:
            print("WARNING: Langfuse not installed - tracking disabled")
        except Exception as e:
            print(f"WARNING: Langfuse initialization failed: {e}")
    
    def trace_agent(self, agent_name: str, input_data: Any, output_data: Any, metadata: dict = None):
        """
        Track agent execution
        
        Args:
            agent_name: Name of the agent (planner, designer, validator)
            input_data: Input to the agent
            output_data: Output from the agent
            metadata: Additional metadata (tokens, duration, etc.)
        """
        if not self.enabled:
            return
        
        try:
            self.langfuse.trace(
                name=agent_name,
                input=input_data,
                output=output_data,
                metadata=metadata or {}
            )
        except Exception as e:
            print(f"⚠ Langfuse tracking failed for {agent_name}: {e}")
    
    def generation(self, name: str, model: str, prompt: str, completion: str, 
                   usage: dict = None, metadata: dict = None):
        """
        Track LLM generation
        
        Args:
            name: Name of the generation (e.g., "planner_prompt")
            model: Model name (e.g., "gpt-4o")
            prompt: Input prompt
            completion: LLM response
            usage: Token usage dict with prompt_tokens, completion_tokens, total_tokens
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        try:
            self.langfuse.generation(
                name=name,
                model=model,
                prompt=prompt,
                completion=completion,
                usage=usage,
                metadata=metadata or {}
            )
        except Exception as e:
            print(f"⚠ Langfuse generation tracking failed: {e}")
    
    def flush(self):
        """Flush pending tracking data"""
        if self.enabled and self.langfuse:
            try:
                self.langfuse.flush()
            except Exception:
                pass


# Global tracker instance
_tracker = None


def get_tracker() -> LangfuseTracker:
    """Get global Langfuse tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = LangfuseTracker()
    return _tracker
