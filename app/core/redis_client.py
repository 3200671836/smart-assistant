"""
Redis 客户端模块
提供 Redis 连接池和常用缓存操作
"""

import json
import os
import redis
from typing import Any, Optional
from datetime import timedelta

# Redis 配置（支持环境变量覆盖）
REDIS_HOST = os.getenv("REDIS_HOST", "192.168.211.132")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")  # 无密码

# 全局连接池
_redis_pool = None


def get_redis_pool():
    """获取 Redis 连接池（单例）"""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
            max_connections=50,
            socket_connect_timeout=3,
            socket_timeout=3,
            health_check_interval=30,
        )
    return _redis_pool


def get_redis_client() -> redis.Redis:
    """获取 Redis 客户端实例"""
    return redis.Redis(connection_pool=get_redis_pool())


class DummyCache:
    """Redis 不可用时的降级缓存（内存字典）"""
    
    def __init__(self):
        self._data = {}
    
    def get(self, key: str):
        return self._data.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        self._data[key] = value
        return True
    
    def delete(self, key: str):
        self._data.pop(key, None)
        return True
    
    def exists(self, key: str):
        return key in self._data
    
    def expire(self, key: str, ttl: int):
        return True
    
    def flush_prefix(self, prefix: Optional[str] = None):
        keys_to_remove = [k for k in self._data.keys() if k.startswith(prefix or "")]
        for k in keys_to_remove:
            self._data.pop(k, None)
        return True


class RedisCache:
    """Redis 缓存封装"""
    
    def __init__(self, prefix: str = "rag", ttl: int = 86400):
        """
        Args:
            prefix: 键前缀，防止冲突
            ttl: 默认过期时间（秒），默认 24 小时
        """
        self.prefix = prefix
        self.default_ttl = ttl
        self._available = False
        self._dummy = DummyCache()
        
        # 尝试连接 Redis
        try:
            self.client = get_redis_client()
            self.client.ping()
            self._available = True
            print(f"[RedisCache] Redis 连接成功 (prefix={prefix})")
        except Exception as e:
            print(f"[RedisCache] Redis 连接失败，使用内存缓存降级: {e}")
            self.client = None
    
    def _key(self, key: str) -> str:
        """生成带前缀的键"""
        return f"{self.prefix}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._available:
            return self._dummy.get(self._key(key))
        try:
            value = self.client.get(self._key(key))
            if value is None:
                return None
            # 尝试 JSON 反序列化
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            print(f"Redis get 失败，使用降级: {e}")
            return self._dummy.get(self._key(key))
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self._available:
            return self._dummy.set(self._key(key), value, ttl)
        try:
            # JSON 序列化
            if not isinstance(value, (str, bytes)):
                value = json.dumps(value, ensure_ascii=False)
            
            expire = ttl or self.default_ttl
            self.client.setex(self._key(key), expire, value)
            return True
        except Exception as e:
            print(f"Redis set 失败，使用降级: {e}")
            return self._dummy.set(self._key(key), value, ttl)
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._available:
            return self._dummy.delete(self._key(key))
        try:
            self.client.delete(self._key(key))
            return True
        except Exception as e:
            print(f"Redis delete 失败，使用降级: {e}")
            return self._dummy.delete(self._key(key))
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._available:
            return self._dummy.exists(self._key(key))
        try:
            return self.client.exists(self._key(key)) > 0
        except Exception as e:
            print(f"Redis exists 失败，使用降级: {e}")
            return self._dummy.exists(self._key(key))
    
    def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        if not self._available:
            return self._dummy.expire(self._key(key), ttl)
        try:
            return self.client.expire(self._key(key), ttl)
        except Exception as e:
            print(f"Redis expire 失败，使用降级: {e}")
            return self._dummy.expire(self._key(key), ttl)
    
    def flush_prefix(self, prefix: Optional[str] = None) -> bool:
        """清空指定前缀的所有键"""
        if not self._available:
            return self._dummy.flush_prefix(prefix)
        try:
            pattern = f"{self.prefix}:{prefix}*" if prefix else f"{self.prefix}:*"
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Redis flush 失败，使用降级: {e}")
            return self._dummy.flush_prefix(prefix)


# 便捷函数
def get_cache(prefix: str = "rag", ttl: int = 86400) -> RedisCache:
    """获取缓存实例"""
    return RedisCache(prefix=prefix, ttl=ttl)


# 测试连接
if __name__ == "__main__":
    try:
        client = get_redis_client()
        client.ping()
        print("Redis 连接成功！")
        
        # 测试缓存
        cache = get_cache()
        cache.set("test", {"message": "Hello Redis"}, ttl=60)
        result = cache.get("test")
        print(f"测试缓存: {result}")
    except Exception as e:
        print(f"Redis 连接失败: {e}")
