"""
Advanced Caching System with Redis and In-Memory Fallback
Provides caching for searches, embeddings, and API responses
"""

import hashlib
import os
import pickle
from collections import OrderedDict
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

try:
    import redis
    from redis import ConnectionPool

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis not available, using in-memory cache only")

from src.core.errors import CustomLogger, ErrorCategory

logger = CustomLogger("cache_manager")


class CacheKey:
    """Generate and manage cache keys"""

    @staticmethod
    def generate(prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key from arguments"""
        # Create a string representation of all arguments
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))

        # Hash for consistency and to handle long keys
        key_string = ":".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]

        return f"{prefix}:{key_hash}"

    @staticmethod
    def search_key(query: str, collection: str, limit: int) -> str:
        """Generate key for search results"""
        return CacheKey.generate("search", query, collection, limit)

    @staticmethod
    def embedding_key(text: str) -> str:
        """Generate key for embeddings"""
        return CacheKey.generate("embedding", text)

    @staticmethod
    def resource_key(resource_id: str) -> str:
        """Generate key for individual resources"""
        return f"resource:{resource_id}"


class InMemoryCache:
    """Fallback in-memory cache with LRU eviction"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            value, expiry = self.cache[key]
            if datetime.now() < expiry:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hit_count += 1
                return value
            else:
                # Expired
                del self.cache[key]

        self.miss_count += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        ttl = ttl or self.ttl_seconds
        expiry = datetime.now() + timedelta(seconds=ttl)

        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self.cache.popitem(last=False)

        self.cache[key] = (value, expiry)
        self.cache.move_to_end(key)

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        hit_rate = self.hit_count / (self.hit_count + self.miss_count) if (self.hit_count + self.miss_count) > 0 else 0
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
        }


class RedisCache:
    """Redis-based cache implementation"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        self.pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=50,
            decode_responses=False,  # We'll handle encoding/decoding
        )
        self.client = redis.Redis(connection_pool=self.pool)
        self.default_ttl = 3600  # 1 hour

        # Test connection
        try:
            self.client.ping()
            logger.log_info("Redis cache connected successfully")
        except Exception as e:
            logger.log_error(e, category=ErrorCategory.DATABASE_ERROR)
            raise

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            value = self.client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.log_error(e, category=ErrorCategory.DATABASE_ERROR, key=key)
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in Redis with TTL"""
        try:
            ttl = ttl or self.default_ttl
            serialized = pickle.dumps(value)
            self.client.setex(key, ttl, serialized)
        except Exception as e:
            logger.log_error(e, category=ErrorCategory.DATABASE_ERROR, key=key)

    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.log_error(e, category=ErrorCategory.DATABASE_ERROR, key=key)
            return False

    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
        except Exception as e:
            logger.log_error(e, category=ErrorCategory.DATABASE_ERROR, pattern=pattern)

    def get_stats(self) -> Dict:
        """Get Redis statistics"""
        try:
            info = self.client.info()
            return {
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.log_error(e, category=ErrorCategory.DATABASE_ERROR)
            return {}


class CacheManager:
    """Main cache manager with Redis and fallback support"""

    def __init__(self, use_redis: bool = True):
        self.use_redis = use_redis and REDIS_AVAILABLE

        # Initialize Redis if available and requested
        if self.use_redis:
            try:
                redis_host = os.getenv("REDIS_HOST", "localhost")
                redis_port = int(os.getenv("REDIS_PORT", 6379))
                redis_password = os.getenv("REDIS_PASSWORD")

                self.redis_cache = RedisCache(host=redis_host, port=redis_port, password=redis_password)
                logger.log_info("Redis cache initialized")
            except Exception as e:
                logger.log_error(e, category=ErrorCategory.DATABASE_ERROR)
                self.use_redis = False
                self.redis_cache = None
        else:
            self.redis_cache = None

        # Always have in-memory cache as fallback
        self.memory_cache = InMemoryCache(max_size=500)

        # Cache configuration
        self.ttl_config = {
            "search": 1800,  # 30 minutes
            "embedding": 86400,  # 24 hours
            "resource": 3600,  # 1 hour
            "api_response": 300,  # 5 minutes
        }

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis first, then memory)"""
        # Try Redis first
        if self.redis_cache:
            value = self.redis_cache.get(key)
            if value is not None:
                # Also update memory cache
                self.memory_cache.set(key, value)
                return value

        # Fallback to memory cache
        return self.memory_cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None, cache_type: str = "default"):
        """Set value in both caches"""
        # Determine TTL
        if ttl is None:
            ttl = self.ttl_config.get(cache_type, 3600)

        # Set in Redis if available
        if self.redis_cache:
            self.redis_cache.set(key, value, ttl)

        # Always set in memory cache
        self.memory_cache.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """Delete from both caches"""
        redis_deleted = self.redis_cache.delete(key) if self.redis_cache else False
        memory_deleted = self.memory_cache.delete(key)
        return redis_deleted or memory_deleted

    def cache_search_results(self, query: str, collection: str, limit: int, results: List[Dict]):
        """Cache search results"""
        key = CacheKey.search_key(query, collection, limit)
        self.set(key, results, cache_type="search")
        logger.log_info("Cached search results", query=query[:50], results_count=len(results))

    def get_cached_search(self, query: str, collection: str, limit: int) -> Optional[List[Dict]]:
        """Get cached search results"""
        key = CacheKey.search_key(query, collection, limit)
        results = self.get(key)
        if results:
            logger.log_info("Cache hit for search", query=query[:50])
        return results

    def cache_embedding(self, text: str, embedding: List[float]):
        """Cache text embedding"""
        key = CacheKey.embedding_key(text)
        self.set(key, embedding, cache_type="embedding")

    def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding"""
        key = CacheKey.embedding_key(text)
        return self.get(key)

    def invalidate_search_cache(self):
        """Invalidate all search caches"""
        if self.redis_cache:
            self.redis_cache.clear_pattern("search:*")

        # Clear memory cache search entries
        keys_to_delete = [k for k in self.memory_cache.cache.keys() if k.startswith("search:")]
        for key in keys_to_delete:
            self.memory_cache.delete(key)

        logger.log_info("Search cache invalidated")

    def get_stats(self) -> Dict:
        """Get combined cache statistics"""
        stats = {"memory_cache": self.memory_cache.get_stats(), "redis_available": self.use_redis}

        if self.redis_cache:
            stats["redis_cache"] = self.redis_cache.get_stats()

        return stats


# Cache decorators for easy use
def cache_result(cache_type: str = "default", ttl: Optional[int] = None):
    """Decorator to cache function results"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = CacheKey.generate(func.__name__, *args, **kwargs)

            # Try to get from cache
            cache_manager = get_cache_manager()
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Cache the result
            cache_manager.set(cache_key, result, ttl=ttl, cache_type=cache_type)

            return result

        return wrapper

    return decorator


def async_cache_result(cache_type: str = "default", ttl: Optional[int] = None):
    """Decorator for async functions"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = CacheKey.generate(func.__name__, *args, **kwargs)

            # Try to get from cache
            cache_manager = get_cache_manager()
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache the result
            cache_manager.set(cache_key, result, ttl=ttl, cache_type=cache_type)

            return result

        return wrapper

    return decorator


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        use_redis = os.getenv("USE_REDIS", "false").lower() == "true"
        _cache_manager = CacheManager(use_redis=use_redis)
    return _cache_manager


# Rate limiting using cache
class RateLimiter:
    """Rate limiting using cache backend"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    def check_rate_limit(self, identifier: str, limit: int = 60, window: int = 60) -> bool:
        """Check if identifier has exceeded rate limit"""
        key = f"rate_limit:{identifier}"
        current_count = self.cache.get(key) or 0

        if current_count >= limit:
            return False

        # Increment counter
        self.cache.set(key, current_count + 1, ttl=window)
        return True

    def get_remaining(self, identifier: str, limit: int = 60) -> int:
        """Get remaining requests for identifier"""
        key = f"rate_limit:{identifier}"
        current_count = self.cache.get(key) or 0
        return max(0, limit - current_count)
