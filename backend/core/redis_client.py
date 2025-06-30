"""
Redis client configuration
"""

import redis.asyncio as redis
import json
from typing import Any, Optional
from .config import settings


class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
    
    async def ping(self):
        """Test Redis connection"""
        return await self.redis.ping()
    
    async def close(self):
        """Close Redis connection"""
        await self.redis.close()
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None):
        """Set a key-value pair"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self.redis.set(key, value, ex=expire)
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        value = await self.redis.get(key)
        if value:
            return value.decode('utf-8')
        return None
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value by key"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def delete(self, key: str):
        """Delete a key"""
        return await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return bool(await self.redis.exists(key))
    
    async def lpush(self, key: str, value: Any):
        """Push to list (left)"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self.redis.lpush(key, value)
    
    async def rpop(self, key: str) -> Optional[str]:
        """Pop from list (right)"""
        value = await self.redis.rpop(key)
        if value:
            return value.decode('utf-8')
        return None
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """Get list range"""
        values = await self.redis.lrange(key, start, end)
        return [v.decode('utf-8') for v in values]
    
    async def sadd(self, key: str, *values: Any):
        """Add to set"""
        string_values = []
        for value in values:
            if isinstance(value, (dict, list)):
                string_values.append(json.dumps(value))
            else:
                string_values.append(str(value))
        return await self.redis.sadd(key, *string_values)
    
    async def smembers(self, key: str) -> set:
        """Get set members"""
        values = await self.redis.smembers(key)
        return {v.decode('utf-8') for v in values}
    
    async def zadd(self, key: str, mapping: dict):
        """Add to sorted set"""
        return await self.redis.zadd(key, mapping)
    
    async def zrange(self, key: str, start: int = 0, end: int = -1, withscores: bool = False):
        """Get sorted set range"""
        values = await self.redis.zrange(key, start, end, withscores=withscores)
        if withscores:
            return [(v[0].decode('utf-8'), v[1]) for v in values]
        return [v.decode('utf-8') for v in values]
    
    async def publish(self, channel: str, message: Any):
        """Publish message to channel"""
        if isinstance(message, (dict, list)):
            message = json.dumps(message)
        return await self.redis.publish(channel, message)
    
    async def cache_response(self, key: str, data: Any, expire: int = 3600):
        """Cache API response"""
        await self.set(f"cache:{key}", data, expire)
    
    async def get_cached_response(self, key: str) -> Optional[Any]:
        """Get cached API response"""
        return await self.get_json(f"cache:{key}")


# Create global Redis client instance
redis_client = RedisClient()