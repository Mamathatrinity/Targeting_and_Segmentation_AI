"""
Prompt Response Caching Layer
Reduces LLM costs by 50-70% for repeated prompts
Based on PDF recommendations (Page 278)
"""
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class PromptCache:
    """Cache LLM responses to avoid repeated API calls"""
    
    def __init__(self, ttl_hours: int = 24):
        """
        Initialize cache
        
        Args:
            ttl_hours: Time-to-live for cache entries in hours (default 24)
        """
        self.cache_store: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(hours=ttl_hours)
    
    def _get_cache_key(self, prompt: str) -> str:
        """
        Generate cache key from prompt using MD5 hash
        
        Args:
            prompt: The prompt text
            
        Returns:
            MD5 hash of the prompt
        """
        return hashlib.md5(prompt.encode('utf-8')).hexdigest()
    
    def get(self, prompt: str) -> Optional[str]:
        """
        Get cached response for a prompt
        
        Args:
            prompt: The prompt text
            
        Returns:
            Cached response if exists and not expired, None otherwise
        """
        key = self._get_cache_key(prompt)
        
        if key not in self.cache_store:
            return None
        
        cached_entry = self.cache_store[key]
        
        # Check if cache entry is expired
        if datetime.now() > cached_entry['expires_at']:
            del self.cache_store[key]
            return None
        
        cached_entry['hits'] += 1
        return cached_entry['response']
    
    def set(self, prompt: str, response: str) -> None:
        """
        Cache a prompt response
        
        Args:
            prompt: The prompt text
            response: The LLM response
        """
        key = self._get_cache_key(prompt)
        
        self.cache_store[key] = {
            'response': response,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + self.ttl,
            'hits': 0
        }
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache_store.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats (size, hits, etc.)
        """
        total_hits = sum(entry['hits'] for entry in self.cache_store.values())
        
        return {
            'total_entries': len(self.cache_store),
            'total_hits': total_hits,
            'cache_size_bytes': len(json.dumps(self.cache_store)),
            'entries': len(self.cache_store)
        }


# Global cache instance
_global_cache = PromptCache(ttl_hours=24)


def get_cached_response(prompt: str) -> Optional[str]:
    """
    Get cached response for a prompt (convenience function)
    
    Args:
        prompt: The prompt text
        
    Returns:
        Cached response if exists, None otherwise
    """
    return _global_cache.get(prompt)


def set_cached_response(prompt: str, response: str) -> None:
    """
    Cache a prompt response (convenience function)
    
    Args:
        prompt: The prompt text
        response: The LLM response
    """
    _global_cache.set(prompt, response)


def clear_cache() -> None:
    """Clear all cache entries (convenience function)"""
    _global_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics (convenience function)"""
    return _global_cache.get_stats()
