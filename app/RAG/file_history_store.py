"""
会话历史存储模块
将对话历史持久化到本地文件，支持长期记忆
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class ChatHistoryStore:
    """基于文件的会话历史存储"""
    
    def __init__(self, history_file: str = "./chat_history.json"):
        self.history_file = Path(history_file)
        self.history: List[dict] = []
        self._load()
    
    def _load(self):
        """从文件加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except json.JSONDecodeError:
                self.history = []
        else:
            self.history = []
    
    def _save(self):
        """保存历史记录到文件"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def add_message(self, role: str, content: str, metadata: Optional[dict] = None):
        """
        添加消息到历史记录
        
        Args:
            role: 角色 (user/assistant/system)
            content: 消息内容
            metadata: 附加元数据 (可选)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if metadata:
            message["metadata"] = metadata
        
        self.history.append(message)
        self._save()
    
    def add_user_message(self, content: str):
        """添加用户消息"""
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.add_message("assistant", content)
    
    def get_history(self, limit: Optional[int] = None) -> List[dict]:
        """
        获取历史记录
        
        Args:
            limit: 返回最近 N 条消息，None 表示全部
        
        Returns:
            消息列表
        """
        if limit is None:
            return self.history.copy()
        return self.history[-limit:] if limit > 0 else []
    
    def get_conversations(self, limit: int = 10) -> List[List[dict]]:
        """
        获取最近的会话轮次
        
        Args:
            limit: 返回最近 N 轮对话
        
        Returns:
            会话列表 (每轮是消息列表)
        """
        # 将消息按轮次分组 (user + assistant 为一轮)
        conversations = []
        current_conv = []
        
        for msg in self.history:
            current_conv.append(msg)
            if msg["role"] == "assistant":
                conversations.append(current_conv)
                current_conv = []
        
        # 处理最后可能未完成的对话
        if current_conv and current_conv[-1]["role"] == "user":
            conversations.append(current_conv)
        
        # 返回最近的 N 轮对话
        return conversations[-limit:] if limit > 0 else conversations
    
    def clear(self):
        """清空历史记录"""
        self.history = []
        self._save()
    
    def get_messages_for_langchain(self, limit: int = 10) -> List[tuple]:
        """
        获取适合 LangChain 的消息格式
        
        Args:
            limit: 最近 N 轮对话
        
        Returns:
            [(role, content), ...] 格式的列表
        """
        recent = self.get_history(limit=limit * 2)  # user + assistant = 2 messages per round
        return [(msg["role"], msg["content"]) for msg in recent]
    
    def __len__(self):
        return len(self.history)
    
    def __repr__(self):
        return f"ChatHistoryStore(messages={len(self.history)})"


# 便捷函数：创建全局历史存储实例
_default_store: Optional[ChatHistoryStore] = None


def get_history_store(history_file: str = "./chat_history.json") -> ChatHistoryStore:
    """获取或创建全局历史存储实例"""
    global _default_store
    if _default_store is None or _default_store.history_file != Path(history_file):
        _default_store = ChatHistoryStore(history_file)
    return _default_store