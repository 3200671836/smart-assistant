"""
数据库会话历史存储模块
从 SQLAlchemy 数据库读取对话历史，支持多轮对话上下文
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import HistoryRecord, SessionLocal


class DBHistoryStore:
    """基于数据库的会话历史存储"""
    
    def __init__(self, db: Session = None):
        self.db = db
        self._local_db = None
        if db is None:
            # 创建独立的数据库会话
            self._local_db = SessionLocal()
            self.db = self._local_db
    
    def __del__(self):
        """清理数据库会话"""
        if self._local_db:
            self._local_db.close()
    
    def add_message(self, role: str, content: str, metadata: Optional[dict] = None):
        """
        添加消息到历史记录（由 chat.py 统一管理，这里不需要实现）
        """
        pass
    
    def add_user_message(self, content: str):
        """添加用户消息（由 chat.py 统一管理）"""
        pass
    
    def add_assistant_message(self, content: str):
        """添加助手消息（由 chat.py 统一管理）"""
        pass
    
    def get_history(self, limit: Optional[int] = 10) -> List[dict]:
        """
        从数据库获取最近的对话历史
        
        Args:
            limit: 返回最近 N 轮对话（每轮包含 user + assistant）
        
        Returns:
            消息列表，格式: [{"role": "user", "content": "..."}, ...]
        """
        try:
            records = self.db.query(HistoryRecord)\
                .filter(HistoryRecord.tool_name == "chat")\
                .order_by(HistoryRecord.created_at.desc())\
                .limit(limit)\
                .all()
            
            history = []
            # 反转顺序，让最早的在前
            for record in reversed(records):
                # 用户消息
                history.append({
                    "role": "user",
                    "content": record.input_summary or ""
                })
                # 助手消息
                result = record.result_json or {}
                response = result.get("response") or record.result_text or ""
                history.append({
                    "role": "assistant", 
                    "content": response
                })
            
            return history
        except Exception as e:
            print(f"从数据库获取历史记录失败: {e}")
            return []
    
    def get_messages_for_langchain(self, limit: int = 10) -> List[tuple]:
        """
        获取适合 LangChain 的消息格式
        
        Args:
            limit: 最近 N 轮对话
        
        Returns:
            [(role, content), ...] 格式的列表
        """
        history = self.get_history(limit=limit)
        return [(msg["role"], msg["content"]) for msg in history]
    
    def clear(self):
        """清空历史记录（不实现，由数据库管理）"""
        pass
    
    def __len__(self):
        try:
            return self.db.query(HistoryRecord)\
                .filter(HistoryRecord.tool_name == "chat")\
                .count()
        except:
            return 0
    
    def __repr__(self):
        return f"DBHistoryStore(messages={len(self)})"


# 便捷函数
def get_db_history_store(db: Session = None) -> DBHistoryStore:
    """获取数据库历史存储实例"""
    return DBHistoryStore(db)
