"""
Caching Utilities

Simple TTL-based caching for expensive Boomi API operations.
Particularly useful for component dependency analysis and repeated queries.
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Callable
from functools import wraps


class ComponentCache:
    """
    Simple TTL-based cache for component data.

    Useful for dependency analysis where the same component
    might be queried multiple times in a single operation.
    """

    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache with TTL.

        Args:
            ttl_seconds: Time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value if still valid.

        Args:
            key: Cache key (usually component ID)

        Returns:
            Cached data if valid, None if expired or not found
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        age = datetime.now() - entry["timestamp"]

        if age < timedelta(seconds=self._ttl):
            return entry["data"]

        # Expired, remove from cache
        del self._cache[key]
        return None

    def set(self, key: str, data: Any) -> None:
        """
        Store data in cache with current timestamp.

        Args:
            key: Cache key
            data: Data to cache
        """
        self._cache[key] = {
            "data": data,
            "timestamp": datetime.now()
        }

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()

    def size(self) -> int:
        """Get number of cached items."""
        return len(self._cache)

    def remove(self, key: str) -> bool:
        """
        Remove specific key from cache.

        Args:
            key: Cache key to remove

        Returns:
            True if key was found and removed
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False


class GenericCache:
    """
    Generic TTL-based cache for any data.

    More flexible than ComponentCache, can be used for
    any cacheable operation.
    """

    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        """
        Initialize cache with TTL and size limit.

        Args:
            ttl_seconds: Time-to-live in seconds
            max_size: Maximum number of entries (LRU eviction)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._access_order: Dict[str, datetime] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value if still valid.

        Args:
            key: Cache key

        Returns:
            Cached data if valid, None otherwise
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        age = datetime.now() - entry["timestamp"]

        if age < timedelta(seconds=self._ttl):
            # Update access time for LRU
            self._access_order[key] = datetime.now()
            return entry["data"]

        # Expired
        self._evict(key)
        return None

    def set(self, key: str, data: Any) -> None:
        """
        Store data in cache.

        Args:
            key: Cache key
            data: Data to cache
        """
        # Evict if at capacity
        if len(self._cache) >= self._max_size and key not in self._cache:
            self._evict_lru()

        now = datetime.now()
        self._cache[key] = {
            "data": data,
            "timestamp": now
        }
        self._access_order[key] = now

    def _evict(self, key: str) -> None:
        """Remove specific key from cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            del self._access_order[key]

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._access_order:
            return

        # Find oldest access time
        lru_key = min(self._access_order.items(), key=lambda x: x[1])[0]
        self._evict(lru_key)

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._access_order.clear()

    def size(self) -> int:
        """Get number of cached items."""
        return len(self._cache)


def create_cache(cache_type: str = "component", **kwargs) -> Any:
    """
    Factory function to create appropriate cache type.

    Args:
        cache_type: Type of cache ("component" or "generic")
        **kwargs: Arguments for cache constructor

    Returns:
        Cache instance
    """
    if cache_type == "component":
        return ComponentCache(**kwargs)
    elif cache_type == "generic":
        return GenericCache(**kwargs)
    else:
        raise ValueError(f"Unknown cache type: {cache_type}")


def cached(ttl_seconds: int = 300, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results.

    Args:
        ttl_seconds: Time-to-live for cached results
        key_func: Function to generate cache key from function args

    Returns:
        Decorated function with caching

    Example:
        @cached(ttl_seconds=600)
        def expensive_query(component_id):
            return sdk.component.get_component(component_id)
    """
    cache = GenericCache(ttl_seconds=ttl_seconds)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name + stringified args
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        # Expose cache for manual management
        wrapper.cache = cache
        return wrapper

    return decorator
