"""
Catalyst Cache configuration for SurakshaAI.
Replaces Redis with Zoho Catalyst Cache.
"""
import os
from typing import Any, Optional

try:
    from catalyst import Catalyst
    from catalyst.cache import Cache
    catalyst_available = True
except ImportError:
    catalyst_available = False


class CatalystCacheConfig:
    """Configuration for Catalyst Cache."""
    
    def __init__(self):
        self.cache = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Catalyst cache."""
        if catalyst_available:
            try:
                app = Catalyst.initialize()
                self.cache = Cache(app)
            except Exception as e:
                print(f"Error initializing Catalyst Cache: {e}")
        else:
            print("Warning: Catalyst SDK not available. Using mock cache.")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if self.cache:
            return self.cache.get(key)
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with optional TTL."""
        if self.cache:
            try:
                self.cache.put(key, value, ttl)
                return True
            except Exception as e:
                print(f"Error setting cache key {key}: {e}")
        return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if self.cache:
            try:
                self.cache.delete(key)
                return True
            except Exception as e:
                print(f"Error deleting cache key {key}: {e}")
        return False
    
    def flush(self) -> bool:
        """Flush all cache."""
        if self.cache:
            try:
                self.cache.flush()
                return True
            except Exception as e:
                print(f"Error flushing cache: {e}")
        return False


# Singleton instance
cache_config = CatalystCacheConfig()
