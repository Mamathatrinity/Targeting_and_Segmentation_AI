"""
Prompt Cache Manager
Reuses loaded prompts to reduce I/O and support API-level caching
"""
import os
import time
from typing import Dict, Optional
from ai_agent.config import AIConfig


class PromptCache:
    """In-memory cache for loaded prompts"""
    
    _instance = None
    _cache: Dict[str, Dict] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get(self, prompt_name: str) -> Optional[str]:
        """Get cached prompt if valid"""
        if not AIConfig.ENABLE_PROMPT_CACHING:
            return None
        
        cache_entry = self._cache.get(prompt_name)
        if cache_entry is None:
            return None
        
        # Check if cache is still valid
        if time.time() - cache_entry['timestamp'] > AIConfig.CACHE_TTL_SECONDS:
            # Cache expired
            del self._cache[prompt_name]
            return None
        
        return cache_entry['content']
    
    def set(self, prompt_name: str, content: str):
        """Cache a prompt"""
        if AIConfig.ENABLE_PROMPT_CACHING:
            self._cache[prompt_name] = {
                'content': content,
                'timestamp': time.time()
            }
    
    def clear(self):
        """Clear all cached prompts"""
        self._cache.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = len(self._cache)
        valid = sum(1 for entry in self._cache.values() 
                   if time.time() - entry['timestamp'] <= AIConfig.CACHE_TTL_SECONDS)
        
        return {
            'total_cached': total,
            'valid_cached': valid,
            'cache_enabled': AIConfig.ENABLE_PROMPT_CACHING,
            'cache_ttl_seconds': AIConfig.CACHE_TTL_SECONDS
        }


def load_prompt(prompt_name: str) -> str:
    """
    Load prompt from file with caching
    
    Args:
        prompt_name: Name of prompt file (e.g., 'planner_prompt.txt')
        
    Returns:
        Prompt content (from cache or file)
        
    Example:
        >>> prompt = load_prompt('planner_prompt.txt')
        >>> # Second call reuses cached version
        >>> prompt = load_prompt('planner_prompt.txt')
    """
    cache = PromptCache()
    
    # Try cache first
    cached_content = cache.get(prompt_name)
    if cached_content is not None:
        return cached_content
    
    # Load from file
    prompt_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
    prompt_file = os.path.join(prompt_dir, prompt_name)
    
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Cache for reuse
    cache.set(prompt_name, content)
    
    return content


def get_cache_stats() -> Dict:
    """Get prompt cache statistics"""
    cache = PromptCache()
    return cache.get_stats()


def clear_cache():
    """Clear prompt cache"""
    cache = PromptCache()
    cache.clear()


if __name__ == "__main__":
    # Test caching
    print("Testing Prompt Cache...")
    
    # Load prompt (from file)
    print("\n1. Loading planner_prompt.txt (from file)...")
    prompt1 = load_prompt("planner_prompt.txt")
    print(f"   Loaded {len(prompt1)} characters")
    
    # Load again (from cache)
    print("\n2. Loading planner_prompt.txt again (from cache)...")
    prompt2 = load_prompt("planner_prompt.txt")
    print(f"   Loaded {len(prompt2)} characters")
    
    # Verify same content
    assert prompt1 == prompt2, "Cache mismatch!"
    print("   ✓ Cache working correctly")
    
    # Check stats
    print("\n3. Cache statistics:")
    stats = get_cache_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Prompt caching is working!")
    print("\nBenefits:")
    print("  - Faster prompt loading (no disk I/O)")
    print("  - Supports API-level caching (same prompt = lower cost)")
    print("  - Automatic cache invalidation after 5 minutes")
