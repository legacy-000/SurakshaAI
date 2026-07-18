import time
import logging
from threading import RLock, Thread, Event
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable, Optional, Tuple

logger = logging.getLogger(__name__)

# Sentinel object to detect cache misses, allowing caching of None values.
_MISS_SENTINEL = object()


class CacheManager:
    """
    Thread-safe, in-memory TTL cache using a singleton pattern.
    Supports LRU eviction when reaching the max size, background cleanup,
    and statistics tracking.
    """
    _instance: Optional["CacheManager"] = None
    _lock = RLock()

    def __new__(cls, *args, **kwargs) -> "CacheManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CacheManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, max_size: Optional[int] = None, cleanup_interval_seconds: Optional[int] = None) -> None:
        with self._lock:
            if getattr(self, "_initialized", False):
                if max_size is not None:
                    self.max_size = max_size
                if cleanup_interval_seconds is not None:
                    self.cleanup_interval = cleanup_interval_seconds
                return
            self.max_size = max_size if max_size is not None else 1000
            self.cleanup_interval = cleanup_interval_seconds if cleanup_interval_seconds is not None else 60

            # Cache storage: key -> (value, expiry_timestamp)
            self._cache: OrderedDict[Any, Tuple[Any, Optional[float]]] = OrderedDict()

            # Statistics
            self._hits = 0
            self._misses = 0
            self._evictions = 0

            # Background thread for cleanup
            self._shutdown_event = Event()
            self._cleanup_thread = Thread(
                target=self._cleanup_loop,
                daemon=True,
                name="CacheManagerCleanupThread"
            )
            self._cleanup_thread.start()

            self._initialized = True
            logger.info(
                "Initialized CacheManager singleton with max_size=%d, cleanup_interval=%ds",
                self.max_size,
                self.cleanup_interval
            )

    @property
    def hits(self) -> int:
        with self._lock:
            return self._hits

    @property
    def misses(self) -> int:
        with self._lock:
            return self._misses

    @property
    def evictions(self) -> int:
        with self._lock:
            return self._evictions

    @property
    def hit_rate(self) -> float:
        with self._lock:
            total = self._hits + self._misses
            return self._hits / total if total > 0 else 0.0

    def get(self, key: Any, default: Any = None) -> Any:
        """
        Retrieve an item from the cache. Updates LRU order.
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default

            value, expiry = self._cache[key]

            # Check expiration
            if expiry is not None and time.time() > expiry:
                del self._cache[key]
                self._misses += 1
                logger.debug("Cache miss (expired) for key: %s", key)
                return default

            # Cache hit: move key to end of OrderedDict for LRU tracking
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        """
        Add or update an item in the cache. Evicts LRU item if capacity is exceeded.
        """
        with self._lock:
            expiry = time.time() + ttl if ttl is not None else None

            if key in self._cache:
                self._cache[key] = (value, expiry)
                self._cache.move_to_end(key)
                return

            # Check size before inserting new item
            if len(self._cache) >= self.max_size:
                # Evict oldest item (the first item in OrderedDict)
                evicted_key, _ = self._cache.popitem(last=False)
                self._evictions += 1
                logger.debug("Cache capacity reached. Evicted key: %s", evicted_key)

            self._cache[key] = (value, expiry)

    def delete(self, key: Any) -> bool:
        """
        Manually remove an item from the cache.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """
        Clear all cached items and reset statistics.
        """
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            logger.info("CacheManager cleared")

    def get_stats(self) -> dict:
        """
        Return cache statistics tracking hits, misses, hit rate, and evictions.
        """
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self.hit_rate,
                "evictions": self._evictions,
                "size": len(self._cache),
                "max_size": self.max_size
            }

    def cleanup_expired(self) -> None:
        """
        Scan and remove all expired keys from the cache.
        """
        with self._lock:
            now = time.time()
            expired_keys = [
                k for k, (_, expiry) in self._cache.items()
                if expiry is not None and now > expiry
            ]
            for k in expired_keys:
                del self._cache[k]
            if expired_keys:
                logger.info("Background cleanup evicted %d expired cache keys", len(expired_keys))

    def _cleanup_loop(self) -> None:
        """
        Loop run by the background thread to periodically clean up expired cache keys.
        """
        while not self._shutdown_event.is_set():
            if self._shutdown_event.wait(self.cleanup_interval):
                break
            try:
                self.cleanup_expired()
            except Exception as e:
                logger.error("Error during background cache cleanup: %s", e, exc_info=True)

    def shutdown(self) -> None:
        """
        Shut down the background cleanup thread.
        """
        self._shutdown_event.set()
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=1.0)
            logger.info("CacheManager background thread stopped")


def cached(ttl: Optional[float] = None, key_prefix: str = "cached") -> Callable:
    """
    Decorator to cache a function's return values in the CacheManager.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache_manager = CacheManager()

            # Serialize arguments safely. Convert unhashable elements to string.
            serialized_args = ",".join(repr(arg) for arg in args)
            serialized_kwargs = ",".join(f"{k}={repr(v)}" for k, v in sorted(kwargs.items()))

            # Formulate the cache key
            key = f"{key_prefix}:{func.__module__}.{func.__name__}({serialized_args})({serialized_kwargs})"

            cached_value = cache_manager.get(key, default=_MISS_SENTINEL)
            if cached_value is not _MISS_SENTINEL:
                return cached_value

            # Fetch fresh value
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl=ttl)
            return result
        return wrapper
    return decorator
