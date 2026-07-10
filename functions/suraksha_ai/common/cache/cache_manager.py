import time


class CacheManager:
    def __init__(self):
        self._cache = {}
        self._ttl = {}

    def get(self, key: str):
        if key in self._cache:
            if time.time() < self._ttl.get(key, 0):
                return self._cache[key]
            del self._cache[key]
            del self._ttl[key]
        return None

    def set(self, key: str, value, ttl_seconds: int = 300):
        self._cache[key] = value
        self._ttl[key] = time.time() + ttl_seconds

    def delete(self, key: str):
        self._cache.pop(key, None)
        self._ttl.pop(key, None)

    def clear(self):
        self._cache.clear()
        self._ttl.clear()
