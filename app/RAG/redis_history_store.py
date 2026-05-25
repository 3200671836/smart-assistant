"""
Redis 历史记录存储
基于 Redis 的对话历史管理，支持 TTL 自动过期
"""

import json
from typing import List, Dict, Optional
from app.core.redis_cache import get_cache


class RedisHistoryStore:
    """Redis 历史记录存储"""
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.cache = get_cache()
    
    def add_message(self, role: str, content: str) -> bool:
        """添加消息"""
        return self.cache.add_chat_message(self.session_id, role, content)
    
    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取历史记录"""
        return self.cache.get_chat_history(self.session_id, limit)
    
    def clear(self) -> bool:
        """清空历史"""
        return self.cache.clear_chat_history(self.session_id)
    
    def get_history_str(self, limit: int = 10) -> str:
        """获取格式化的历史字符串"""
        messages = self.get_history(limit)
        if not messages:
            return "无历史对话"
        
        lines = []
        for msg in messages:  # get_history 已经按时间顺序返回
            role = "用户" if msg["role"] == "user" else "助手"
            lines.append(f"{role}：{msg['content']}")
        return "\n".join(lines)
