"""
Token 压缩模块
基于 tiktoken 的对话历史压缩，支持摘要生成
"""

import json
from typing import List, Dict, Optional
from datetime import datetime

# 尝试导入 tiktoken，如果不可用则使用简单估算
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("[TokenCompressor] tiktoken 未安装，使用字符数估算")


class TokenCompressor:
    """Token 压缩器"""
    
    def __init__(self, model: str = "qwen3-max", max_tokens: int = 4000):
        """
        Args:
            model: 模型名称，用于 tiktoken 编码
            max_tokens: 最大 Token 数阈值
        """
        self.max_tokens = max_tokens
        self.model = model
        
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoding = tiktoken.encoding_for_model(model)
            except Exception:
                self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoding = None
    
    def count_tokens(self, text: str) -> int:
        """计算文本的 Token 数"""
        if self.encoding:
            return len(self.encoding.encode(text))
        # 简单估算：中文字符 ≈ 2 tokens，英文 ≈ 0.75 tokens
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 2 + other_chars * 0.75)
    
    def compress_history(self, messages: List[Dict[str, str]], 
                        keep_first: int = 1,
                        keep_last: int = 5) -> List[Dict[str, str]]:
        """
        压缩对话历史
        
        策略：
        1. 保留首轮对话（系统提示）
        2. 保留最近 N 轮
        3. 中间历史用摘要替代
        
        Args:
            messages: 消息列表
            keep_first: 保留前 N 条
            keep_last: 保留后 N 条
        
        Returns:
            压缩后的消息列表
        """
        if len(messages) <= keep_first + keep_last:
            return messages
        
        # 计算总 Token 数
        total_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        total_tokens = self.count_tokens(total_text)
        
        if total_tokens <= self.max_tokens:
            return messages
        
        # 需要压缩
        print(f"[TokenCompressor] 历史 Token 数 {total_tokens} > {self.max_tokens}，开始压缩")
        
        # 保留首轮和最近轮次
        first_messages = messages[:keep_first]
        last_messages = messages[-keep_last:]
        
        # 中间部分需要摘要
        middle_messages = messages[keep_first:-keep_last]
        
        if middle_messages:
            # 生成摘要
            summary = self._generate_summary(middle_messages)
            summary_msg = {
                "role": "system",
                "content": f"[历史对话摘要] {summary}",
                "is_summary": True
            }
            
            compressed = first_messages + [summary_msg] + last_messages
        else:
            compressed = first_messages + last_messages
        
        # 验证压缩后 Token 数
        compressed_text = "\n".join([f"{m['role']}: {m['content']}" for m in compressed])
        compressed_tokens = self.count_tokens(compressed_text)
        print(f"[TokenCompressor] 压缩后 Token 数: {compressed_tokens}")
        
        return compressed
    
    def _generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """生成对话摘要（使用 LLM 生成高质量摘要）"""
        try:
            # 尝试导入 LLM 服务
            from app.services.llm_service import LLMService
            llm = LLMService()
            
            # 构建对话文本
            conversation = []
            for msg in messages:
                role = "用户" if msg['role'] == 'user' else "助手"
                conversation.append(f"{role}：{msg['content']}")
            
            conversation_text = "\n".join(conversation)
            
            # 使用 LLM 生成摘要
            system_prompt = "你是一个对话总结专家。请将以下对话压缩为一段简洁的摘要，保留关键信息和结论。"
            user_prompt = f"请总结以下对话：\n\n{conversation_text[:3000]}"
            
            summary = llm.chat(system_prompt, user_prompt)
            
            # 确保摘要长度合适
            if len(summary) > 200:
                summary = summary[:200] + "..."
            
            return summary
            
        except Exception as e:
            print(f"[TokenCompressor] LLM 摘要生成失败，使用降级方案: {e}")
            # 降级方案：提取关键信息
            topics = []
            key_points = []
            
            for msg in messages:
                if msg['role'] == 'user':
                    content = msg['content']
                    if len(content) > 20:
                        topics.append(content[:20] + "...")
                    else:
                        topics.append(content)
                else:
                    content = msg['content']
                    if len(content) > 30:
                        key_points.append(content[:30] + "...")
                    else:
                        key_points.append(content)
            
            summary_parts = []
            if topics:
                summary_parts.append(f"讨论了 {len(topics)} 个问题")
            if key_points:
                summary_parts.append(f"主要结论: {'; '.join(key_points[:3])}")
            
            return "；".join(summary_parts) if summary_parts else "历史对话已压缩"
    
    def compress_for_prompt(self, history_str: str, current_input: str, 
                           max_history_tokens: int = 2000) -> str:
        """
        为 Prompt 压缩历史记录
        
        Args:
            history_str: 历史记录字符串
            current_input: 当前输入
            max_history_tokens: 历史记录最大 Token 数
        
        Returns:
            压缩后的历史字符串
        """
        if not history_str or history_str == "无历史对话":
            return history_str
        
        # 计算当前历史 Token 数
        history_tokens = self.count_tokens(history_str)
        
        if history_tokens <= max_history_tokens:
            return history_str
        
        # 需要压缩历史
        print(f"[TokenCompressor] 历史记录 Token 数 {history_tokens} > {max_history_tokens}，进行压缩")
        
        # 简单压缩：保留最近的部分
        lines = history_str.split('\n')
        
        # 尝试保留最近 50% 的内容
        half_idx = len(lines) // 2
        compressed_lines = lines[half_idx:]
        
        compressed = '\n'.join(compressed_lines)
        compressed_tokens = self.count_tokens(compressed)
        
        # 如果还超限，继续压缩
        while compressed_tokens > max_history_tokens and len(compressed_lines) > 2:
            compressed_lines = compressed_lines[2:]  # 移除一轮对话
            compressed = '\n'.join(compressed_lines)
            compressed_tokens = self.count_tokens(compressed)
        
        print(f"[TokenCompressor] 压缩后历史 Token 数: {compressed_tokens}")
        
        return f"[历史记录已压缩，保留最近对话]\n{compressed}"


# 全局压缩器实例
_compressor_instance: Optional[TokenCompressor] = None


def get_compressor(model: str = "gpt-3.5-turbo", max_tokens: int = 4000) -> TokenCompressor:
    """获取 Token 压缩器单例"""
    global _compressor_instance
    if _compressor_instance is None:
        _compressor_instance = TokenCompressor(model=model, max_tokens=max_tokens)
    return _compressor_instance
