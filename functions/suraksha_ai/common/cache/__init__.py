try:
    from common.cache.cache_manager import CacheManager, cached
except ImportError:
    from cache.cache_manager import CacheManager, cached

__all__ = ["CacheManager", "cached"]
