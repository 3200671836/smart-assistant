"""
办公工具服务层
提供文档总结、会议纪要生成等功能
"""

import json
from app.services.llm_service import LLMService


class OfficeService:
    """办公工具服务"""

    def __init__(self):
        self.llm = LLMService()

    def summarize_document(self, text: str) -> dict:
        """
        文档智能总结（支持长文档分块摘要）

        Args:
            text: 文档正文

        Returns:
            {
                "summary": "一句话总结",
                "key_points": ["要点1", "要点2", ...],
                "chunk_summaries": ["分块1摘要", "分块2摘要", ...] (仅长文档)
            }
        """
        # 判断是否为长文档
        if len(text) <= 4000:
            # 短文档直接处理
            return self._summarize_short_document(text)
        else:
            # 长文档分块摘要
            return self._summarize_long_document(text)
    
    def _summarize_short_document(self, text: str) -> dict:
        """短文档总结（≤4000字）"""
        system_prompt = """你是一位专业的文档分析师。请对提供的文档进行总结，输出JSON格式：
{
    "summary": "一句话总结文档核心内容（不超过100字）",
    "key_points": ["关键要点1", "关键要点2", "关键要点3", ...]
}
要求：
1. summary 必须是一句话，精炼准确
2. key_points 列出3-7个核心要点，每个要点不超过50字
3. 只输出JSON，不要任何其他文字"""

        user_prompt = f"请总结以下文档：\n\n{text[:4000]}"

        result = self.llm.extract_json(system_prompt, user_prompt)
        if result is None:
            return {
                "summary": "文档总结生成失败，请重试",
                "key_points": ["无法提取要点"]
            }

        return {
            "summary": result.get("summary", "暂无总结"),
            "key_points": result.get("key_points", [])
        }
    
    def _summarize_long_document(self, text: str) -> dict:
        """长文档分块摘要（>4000字）"""
        # 1. 分块（每块约2000字，重叠200字）
        chunk_size = 2000
        overlap = 200
        chunks = []
        
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)
            if len(chunks) >= 10:  # 最多10块
                break
        
        print(f"[OfficeService] 长文档分块：{len(chunks)} 块")
        
        # 2. 为每块生成摘要
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            system_prompt = """请用一句话总结以下文档片段的核心内容（不超过50字）。"""
            user_prompt = f"文档片段：\n\n{chunk}"
            
            summary = self.llm.chat(system_prompt, user_prompt)
            chunk_summaries.append({
                "chunk_id": i + 1,
                "summary": summary[:100] if len(summary) > 100 else summary
            })
        
        # 3. 合并所有摘要，生成整体总结
        all_summaries = "\n".join([f"分块{i}: {s['summary']}" for i, s in enumerate(chunk_summaries, 1)])
        
        system_prompt = """你是一位文档分析师。以下是长文档各分块的摘要，请基于这些摘要生成整体总结。
输出JSON格式：
{
    "summary": "整体一句话总结（不超过100字）",
    "key_points": ["整体关键要点1", "整体关键要点2", "整体关键要点3"]
}
要求：
1. 基于所有分块摘要，提炼核心内容
2. summary 要覆盖文档主要主题
3. key_points 列出最重要的3-5个要点"""
        
        user_prompt = f"各分块摘要：\n\n{all_summaries}"
        
        result = self.llm.extract_json(system_prompt, user_prompt)
        if result is None:
            # 降级：使用第一个分块摘要
            first_summary = chunk_summaries[0]["summary"] if chunk_summaries else "无法生成总结"
            return {
                "summary": first_summary,
                "key_points": ["文档过长，建议分段阅读"],
                "chunk_summaries": [s["summary"] for s in chunk_summaries]
            }
        
        return {
            "summary": result.get("summary", "暂无总结"),
            "key_points": result.get("key_points", []),
            "chunk_summaries": [s["summary"] for s in chunk_summaries],
            "total_chunks": len(chunks)
        }

    def generate_meeting_minutes(self, text: str) -> dict:
        """
        会议纪要生成

        Args:
            text: 会议记录原文

        Returns:
            {
                "minutes": {
                    "topics": [
                        {
                            "name": "议题名称",
                            "discussion": "讨论要点",
                            "decision": "决策结论"
                        }
                    ]
                },
                "todos": [
                    {
                        "task": "任务描述",
                        "assignee": "负责人",
                        "due_date": "截止时间"
                    }
                ]
            }
        """
        system_prompt = """你是一位专业的会议记录整理员。请将会议记录整理为结构化的会议纪要，输出JSON格式：
{
    "minutes": {
        "topics": [
            {
                "name": "议题名称",
                "discussion": "讨论要点摘要",
                "decision": "决策结论或待决策事项"
            }
        ]
    },
    "todos": [
        {
            "task": "具体任务描述",
            "assignee": "负责人（如记录中有提到）",
            "due_date": "截止时间（如记录中有提到，格式：YYYY-MM-DD或'无明确时间'）"
        }
    ]
}
要求：
1. topics 至少列出2个主要议题，每个议题包含讨论要点和决策结论
2. todos 列出所有明确的待办事项，如果记录中没有明确负责人或时间，填写"待确认"
3. 只输出JSON，不要任何其他文字"""

        # 长文本截断
        max_chars = 8000
        truncated = text[:max_chars] if len(text) > max_chars else text
        if len(text) > max_chars:
            truncated += "\n...（会议记录已截断）"

        user_prompt = f"请整理以下会议记录：\n\n{truncated}"

        result = self.llm.extract_json(system_prompt, user_prompt)
        if result is None:
            return {
                "minutes": {"topics": []},
                "todos": []
            }

        # 确保返回格式正确
        minutes = result.get("minutes", {})
        if "topics" not in minutes:
            minutes["topics"] = []

        todos = result.get("todos", [])
        if not isinstance(todos, list):
            todos = []

        return {
            "minutes": minutes,
            "todos": todos
        }


# 模块级单例
_office_service: OfficeService | None = None


def get_office_service() -> OfficeService:
    """获取办公工具服务单例"""
    global _office_service
    if _office_service is None:
        _office_service = OfficeService()
    return _office_service
