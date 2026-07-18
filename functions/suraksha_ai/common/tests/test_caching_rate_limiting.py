from security.rate_limiter import RateLimiter, rate_limited, RateLimitExceededError
from cache.cache_manager import CacheManager, cached
from models.dto import UserContextDTO
import pytest
import sys
import os
import time

# Setup path so tests can run in isolation
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)


def test_cache_manager_basic_operations():
    cache = CacheManager(max_size=5)
    cache.clear()

    # Set and Get
    cache.set("key1", "val1", ttl=10)
    assert cache.get("key1") == "val1"

    # Get stats
    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 0
    assert stats["size"] == 1

    # Expiry
    cache.set("key2", "val2", ttl=0.1)
    assert cache.get("key2") == "val2"
    time.sleep(0.15)
    assert cache.get("key2") is None

    # Expiry miss stats
    stats = cache.get_stats()
    assert stats["misses"] == 1


def test_cache_manager_lru_eviction():
    cache = CacheManager(max_size=3)
    cache.clear()

    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)

    # Access "a" to make "b" the least recently used
    assert cache.get("a") == 1

    # Set "d" -> should evict "b"
    cache.set("d", 4)

    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert cache.get("d") == 4

    stats = cache.get_stats()
    assert stats["evictions"] == 1


def test_cached_decorator():
    cache = CacheManager()
    cache.clear()

    call_count = 0

    @cached(ttl=5, key_prefix="test_decorator")
    def compute(x, y):
        nonlocal call_count
        call_count += 1
        return x + y

    # First call - cache miss
    res1 = compute(2, 3)
    assert res1 == 5
    assert call_count == 1

    # Second call - cache hit
    res2 = compute(2, 3)
    assert res2 == 5
    assert call_count == 1

    # Different args - cache miss
    res3 = compute(3, 4)
    assert res3 == 7
    assert call_count == 2


def test_rate_limiter_token_bucket():
    # Instantiate with custom tight limits for testing
    limiter = RateLimiter(rates={"test_action": 60})  # 60/min = 1/sec

    # Check limit for client1
    res1 = limiter.check_rate_limit("client1", "test_action", tokens_to_consume=30)
    assert res1.allowed is True
    assert res1.remaining == 30

    # Check limit again, consume another 20
    res2 = limiter.check_rate_limit("client1", "test_action", tokens_to_consume=20)
    assert res2.allowed is True
    assert res2.remaining == 10

    # Try to consume 15 -> not enough
    res3 = limiter.check_rate_limit("client1", "test_action", tokens_to_consume=15)
    assert res3.allowed is False
    assert res3.retry_after_seconds > 0


def test_rate_limited_decorator_and_sysadmin_bypass():
    _limiter = RateLimiter(rates={"restricted_action": 1})  # 1 per minute  # noqa: F841

    call_count = 0

    @rate_limited("restricted_action")
    def perform_action(user: UserContextDTO):
        nonlocal call_count
        call_count += 1
        return "success"

    regular_user = UserContextDTO(
        user_id="INV001", kgid="INV001", first_name="Ravi",
        email="", role_id=1, role_name="Investigator"
    )

    admin_user = UserContextDTO(
        user_id="ADM001", kgid="ADM001", first_name="Vikram",
        email="", role_id=5, role_name="System Administrator"
    )

    # First call for regular user -> allowed
    assert perform_action(user=regular_user) == "success"
    assert call_count == 1

    # Second call for regular user -> rate limited
    with pytest.raises(RateLimitExceededError):
        perform_action(user=regular_user)

    # Call for System Administrator -> bypass, should succeed
    assert perform_action(user=admin_user) == "success"
    assert call_count == 2
