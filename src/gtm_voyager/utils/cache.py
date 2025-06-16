import time
from typing import Any, Optional, Dict

class CacheManager:
    """Cache manager for GTM Voyager Platform."""
    
    def __init__(self, default_ttl: int = 3600):
        """Initialize the cache manager."""
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl  # Time to live in seconds
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache."""
        expiry_time = time.time() + (ttl or self.default_ttl)
        self.cache[key] = {
            'value': value,
            'expiry': expiry_time
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        if key not in self.cache:
            return None
        
        cache_entry = self.cache[key]
        
        # Check if expired
        if time.time() > cache_entry['expiry']:
            del self.cache[key]
            return None
        
        return cache_entry['value']
    
    def delete(self, key: str) -> bool:
        """Delete a key from the cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry['expiry']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def size(self) -> int:
        """Get the number of items in cache."""
        return len(self.cache)
    
    def keys(self) -> list:
        """Get all cache keys."""
        return list(self.cache.keys())
