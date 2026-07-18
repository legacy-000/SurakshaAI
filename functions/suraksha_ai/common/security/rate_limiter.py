import time
import logging
from dataclasses import dataclass
from threading import RLock, Thread, Event
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Safe imports for user context and constants
try:
    from models.dto import UserContextDTO
except ImportError:
    try:
        from common.models.dto import UserContextDTO
    except ImportError:
        # Fallback dummy class if not available during bootstrap/isolated tests
        class UserContextDTO:
            pass

try:
    from config.constants import ROLE_SYSTEM_ADMIN
except ImportError:
    try:
        from common.config.constants import ROLE_SYSTEM_ADMIN
    except ImportError:
        ROLE_SYSTEM_ADMIN = "System Administrator"


@dataclass
class RateLimitResult:
    """Represents the result of a rate limiting check."""
    allowed: bool
    remaining: int
    reset_at: float
    retry_after_seconds: float


class RateLimitExceededError(Exception):
    """Exception raised when a client exceeds their rate limit."""

    def __init__(self, action: str, result: RateLimitResult):
        self.action = action
        self.result = result
        message = (
            f"Rate limit exceeded for action '{action}'. "
            f"Retry after {result.retry_after_seconds:.1f} seconds."
        )
        super().__init__(message)


class TokenBucket:
    """Individual token bucket implementation for rate limiting."""

    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self, tokens_to_consume: float = 1.0) -> Tuple[bool, int, float, float]:
        """
        Attempt to consume tokens from the bucket.

        Returns:
            allowed: True if enough tokens were available, False otherwise
            remaining: Rounded number of remaining tokens
            reset_at: Unix timestamp when the bucket will be completely full again
            retry_after_seconds: Seconds to wait before having enough tokens to consume
        """
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        # Refill tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

        if self.tokens >= tokens_to_consume:
            self.tokens -= tokens_to_consume
            remaining = int(self.tokens)
            # Time to fully refill the bucket
            time_to_fill = (self.capacity - self.tokens) / self.refill_rate if self.refill_rate > 0 else 0.0
            reset_at = now + time_to_fill
            return True, remaining, reset_at, 0.0
        else:
            remaining = int(self.tokens)
            needed = tokens_to_consume - self.tokens
            retry_after_seconds = needed / self.refill_rate if self.refill_rate > 0 else float('inf')

            # Time to fully refill the bucket
            time_to_fill = (self.capacity - self.tokens) / self.refill_rate if self.refill_rate > 0 else 0.0
            reset_at = now + time_to_fill
            return False, remaining, reset_at, retry_after_seconds


# Default limits per action (requests per minute)
DEFAULT_RATES = {
    "chat_query": 60,
    "run_sql": 10,
    "login": 5,
    "send_message": 30,
    "default": 120
}


class RateLimiter:
    """
    Thread-safe Token-Bucket Rate Limiter with singleton pattern.
    Configurable rates per action, inactive bucket cleanup, and System Admin bypass.
    """
    _instance: Optional["RateLimiter"] = None
    _lock = RLock()

    def __new__(cls, *args, **kwargs) -> "RateLimiter":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RateLimiter, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, rates: Optional[Dict[str, int]] = None, cleanup_interval_seconds: int = 300) -> None:
        with self._lock:
            if getattr(self, "_initialized", False):
                if rates:
                    self.rates.update(rates)
                return

            self.rates = dict(DEFAULT_RATES)
            if rates:
                self.rates.update(rates)

            self.cleanup_interval = cleanup_interval_seconds
            self._buckets: Dict[Tuple[str, str], TokenBucket] = {}

            # Background thread for cleanup of inactive buckets
            self._shutdown_event = Event()
            self._cleanup_thread = Thread(
                target=self._cleanup_loop,
                daemon=True,
                name="RateLimiterCleanupThread"
            )
            self._cleanup_thread.start()

            self._initialized = True
            logger.info("Initialized RateLimiter singleton")

    def check_rate_limit(self, client_id: str, action: str, tokens_to_consume: float = 1.0) -> RateLimitResult:
        """
        Check rate limit for a client and action.
        """
        with self._lock:
            key = (client_id, action)
            if key not in self._buckets:
                # Retrieve configuration limit for the action
                limit_per_minute = self.rates.get(action, self.rates["default"])
                capacity = float(limit_per_minute)
                refill_rate = capacity / 60.0  # limit/min -> tokens/sec
                self._buckets[key] = TokenBucket(capacity, refill_rate)

            bucket = self._buckets[key]
            allowed, remaining, reset_at, retry_after = bucket.consume(tokens_to_consume)

            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                reset_at=reset_at,
                retry_after_seconds=retry_after
            )

    def cleanup_inactive_buckets(self, max_inactive_seconds: float = 3600) -> None:
        """
        Remove buckets that haven't been accessed for more than max_inactive_seconds.
        """
        with self._lock:
            now = time.time()
            inactive_keys = [
                key for key, bucket in self._buckets.items()
                if now - bucket.last_update > max_inactive_seconds
            ]
            for key in inactive_keys:
                del self._buckets[key]
            if inactive_keys:
                logger.info("Background cleanup evicted %d inactive rate-limiter buckets", len(inactive_keys))

    def _cleanup_loop(self) -> None:
        """
        Periodic execution of bucket cleanup inside the background thread.
        """
        while not self._shutdown_event.is_set():
            if self._shutdown_event.wait(self.cleanup_interval):
                break
            try:
                self.cleanup_inactive_buckets()
            except Exception as e:
                logger.error("Error during background rate limiter cleanup: %s", e, exc_info=True)

    def shutdown(self) -> None:
        """
        Stop the background cleanup thread.
        """
        self._shutdown_event.set()
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=1.0)
            logger.info("RateLimiter background thread stopped")


def rate_limited(action: str) -> Callable:
    """
    Decorator to rate limit functions based on user contexts or client IDs.
    Bypasses checking for users with "System Administrator" role.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Look for UserContextDTO in arguments
            user = kwargs.get("user") or kwargs.get("user_context")
            if not user:
                for arg in args:
                    if isinstance(arg, UserContextDTO):
                        user = arg
                        break
                    elif hasattr(arg, "role_name"):
                        user = arg
                        break

            # Bypass rate limiting if the caller is a System Administrator
            if user and getattr(user, "role_name", None) == ROLE_SYSTEM_ADMIN:
                logger.debug("Bypassing rate limit for System Administrator: %s", user.kgid)
                return func(*args, **kwargs)

            # Determine client ID
            client_id = "anonymous"
            if user:
                client_id = getattr(user, "user_id", None) or getattr(user, "kgid", "anonymous")
            else:
                # Try to extract kgid from kwargs or args
                kgid_val = kwargs.get("kgid")
                if not kgid_val:
                    for arg in args:
                        if hasattr(arg, "kgid"):
                            kgid_val = arg.kgid
                            break
                        elif isinstance(arg, str) and (
                            arg.startswith("INV") or
                            arg.startswith("ADM") or
                            arg.startswith("TSE") or
                            arg.startswith("ANL") or
                            arg.startswith("SUP") or
                            arg.startswith("POL")
                        ):
                            kgid_val = arg
                            break
                if kgid_val:
                    client_id = kgid_val

            # Check rate limit
            limiter = RateLimiter()
            result = limiter.check_rate_limit(client_id, action)

            if not result.allowed:
                logger.warning(
                    "Rate limit exceeded for client %s on action %s. Retry after %.2fs",
                    client_id, action, result.retry_after_seconds
                )
                raise RateLimitExceededError(action, result)

            return func(*args, **kwargs)
        return wrapper
    return decorator
