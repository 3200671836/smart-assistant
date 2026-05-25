"""
历史记录存储工厂
根据 Redis 可用性自动选择存储方式
"""

from typing import Union
from app.core.redis_cache import get_redis_cache
from app.RAG.redis_history_store import RedisHistoryStore


class DBHistoryStore:
    """数据库历史记录存储（兼容旧版）"""
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._messages = []  # 内存存储，实际应由 HistoryService 持久化
    
    def add_message(self, role: str, content: str) -> bool:
        """添加消息到历史记录"""
        self._messages.append({"role": role, "content": content})
        # 只保留最近20条
        if len(self._messages) > 20:
            self._messages = self._messages[-20:]
        return True
    
    def get_history(self, limit: int = 10):
        """获取历史记录，返回最近 limit 条"""
        return self._messages[-limit:] if self._messages else []
    
    def get_history_str(self, limit: int = 10) -> str:
        """获取格式化的历史字符串"""
        messages = self.get_history(limit)
        if not messages:
            return "无历史对话"
        
        lines = []
        for msg in messages:
            role = "用户" if msg["role"] == "user" else "助手"
            lines.append(f"{role}：{msg['content']}")
        return "\n".join(lines)
    
    def clear(self) -> bool:
        """清空历史记录"""
        self._messages = []
        return True


def get_history_store(session_id: str = "default", use_redis: bool = True):
    """
    获取历史记录存储
    
    优先使用 Redis，如果不可用则回退到数据库
    """
    if use_redis:
        redis_cache = get_redis_cache()
        if redis_cache.is_available():
            return RedisHistoryStore(session_id)
    
    return DBHistoryStore(session_id)
