"""
Redis 缓存模块
提供对话历史缓存、响应缓存等功能
"""

import json
import redis
from typing import Optional, List, Dict, Any
from datetime import timedelta


class RedisCache:
    """Redis 缓存封装"""
    
    def __init__(self, host: str = "192.168.211.133", port: int = 6379, db: int = 0, password: str = None):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30
        )
        self._available = None
    
    def is_available(self) -> bool:
        """检查 Redis 是否可用"""
        if self._available is not None:
            return self._available
        try:
            self.client.ping()
            self._available = True
            return True
        except Exception:
            self._available = False
            return False
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存"""
        if not self.is_available():
            return None
        try:
            return self.client.get(key)
        except Exception:
            return None
    
    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """设置缓存"""
        if not self.is_available():
            return False
        try:
            self.client.setex(key, ttl, value)
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.is_available():
            return False
        try:
            self.client.delete(key)
            return True
        except Exception:
            return False
    
    # 对话历史相关
    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """获取对话历史，按时间顺序返回（最早的在前）"""
        if not self.is_available():
            return []
        try:
            key = f"chat_history:{session_id}"
            # LRANGE 返回的是从 newest 到 oldest（因为 LPUSH）
            # 需要反转以获得 chronological order
            messages = self.client.lrange(key, 0, limit - 1)
            parsed = [json.loads(m) for m in messages]
            return list(reversed(parsed))  # 反转回时间顺序
        except Exception:
            return []
    
    def add_chat_message(self, session_id: str, role: str, content: str, ttl: int = 86400) -> bool:
        """添加对话消息"""
        if not self.is_available():
            return False
        try:
            key = f"chat_history:{session_id}"
            message = json.dumps({"role": role, "content": content}, ensure_ascii=False)
            # 使用 LPUSH 保持最新在前面
            self.client.lpush(key, message)
            # 设置过期时间
            self.client.expire(key, ttl)
            # 只保留最近 20 条
            self.client.ltrim(key, 0, 19)
            return True
        except Exception:
            return False
    
    def clear_chat_history(self, session_id: str) -> bool:
        """清空对话历史"""
        if not self.is_available():
            return False
        try:
            self.client.delete(f"chat_history:{session_id}")
            return True
        except Exception:
            return False
    
    # 响应缓存
    def get_cached_response(self, query: str) -> Optional[str]:
        """获取缓存的响应"""
        if not self.is_available():
            return None
        try:
            key = f"response_cache:{hash(query) & 0x7FFFFFFF}"
            return self.get(key)
        except Exception:
            return None
    
    def cache_response(self, query: str, response: str, ttl: int = 3600) -> bool:
        """缓存响应"""
        if not self.is_available():
            return False
        try:
            key = f"response_cache:{hash(query) & 0x7FFFFFFF}"
            return self.set(key, response, ttl)
        except Exception:
            return False


# 全局缓存实例
_cache_instance: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """获取 Redis 缓存单例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


# 兼容旧接口的 DummyCache
class DummyCache:
    """当 Redis 不可用时使用的空缓存"""
    
    def get(self, key: str) -> None:
        return None
    
    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        return False
    
    def delete(self, key: str) -> bool:
        return False
    
    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        return []
    
    def add_chat_message(self, session_id: str, role: str, content: str, ttl: int = 86400) -> bool:
        return False
    
    def clear_chat_history(self, session_id: str) -> bool:
        return False
    
    def get_cached_response(self, query: str) -> None:
        return None
    
    def cache_response(self, query: str, response: str, ttl: int = 3600) -> bool:
        return False


def get_cache() -> Any:
    """获取可用的缓存（Redis 或 Dummy）"""
    cache = get_redis_cache()
    if cache.is_available():
        return cache
    return DummyCache()
