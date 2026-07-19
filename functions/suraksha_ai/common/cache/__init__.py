try:
    from common.cache.cache_manager import CacheManager, cached
except ImportError:
    from cache.cache_manager import CacheManager, cached

import json
import os
import time
import hashlib

CACHE_DIR = "/tmp/suraksha_cache"
DEFAULT_TTL = 300


def cache_get(key: str):
    h = hashlib.md5(key.encode()).hexdigest()
    p = os.path.join(CACHE_DIR, h[:2], h)
    try:
        with open(p) as f:
            entry = json.load(f)
        if time.time() - entry["ts"] < entry.get("ttl", DEFAULT_TTL):
            return entry["data"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return None


def cache_set(key: str, data, ttl: int = DEFAULT_TTL):
    h = hashlib.md5(key.encode()).hexdigest()
    p = os.path.join(CACHE_DIR, h[:2], h)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump({"ts": time.time(), "ttl": ttl, "data": data}, f)


__all__ = ["CacheManager", "cached", "cache_get", "cache_set"]
