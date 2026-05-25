"""
Agent 服务层 - 实现真正的 Agent 架构
从标准 RAG pipeline 升级到自主决策的 Agent
"""

import json
from typing import List, Dict, Any, Optional
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from app.RAG.knowledge_base import KnowledgeBaseService
from app.RAG.rag import RagService
from app.core.config import settings


class AgentService:
    """ Agent 服务，支持工具调用和自主决策"""

    def __init__(self, rag_service: RagService = None):
        self.rag = rag_service or RagService()
        self.kb = KnowledgeBaseService()
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.dashscope_base_url,
            api_key=settings.dashscope_api_key,
            temperature=0.7,
        )

        # 初始化工具
        self.tools = [
            self._create_search_tool(),
            self._create_history_tool(),
            self._create_resume_analysis_tool(),
            self._create_document_summary_tool(),
        ]

        # 创建 Agent
        self.agent = self._create_agent()

    def _create_search_tool(self):
        """创建知识库检索工具"""

        @tool
        def search_knowledge_base(query: str) -> str:
            """
            在个人知识库中搜索相关文档片段。
            
            当用户询问简历、文档内容、项目经历、技能等与个人知识库相关的问题时使用此工具。
            
            Args:
                query: 搜索关键词
            
            Returns:
                相关文档片段，格式为"文档1内容\n---\n文档2内容..."
            """
            try:
                # 使用混合检索
                results = self.kb.search(query, k=3)
                if not results:
                    return "知识库中没有找到相关信息。"

                # 格式化结果
                formatted = []
                for i, doc in enumerate(results, 1):
                    content = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                    source = doc.metadata.get('source', '未知')
                    formatted.append(f"[{i}] {content}\n来源：{source}")

                return "\n---\n".join(formatted)
            except Exception as e:
                return f"检索失败：{str(e)}"

        return search_knowledge_base

    def _create_history_tool(self):
        """创建对话历史工具"""

        @tool
        def get_conversation_history(n: int = 5) -> str:
            """
            获取最近的对话历史，用于理解上下文。
            
            当需要了解之前的对话内容时使用此工具。
            
            Args:
                n: 获取最近 N 轮对话，默认 5
            
            Returns:
                格式化的对话历史
            """
            try:
                history = self.rag.history_store.get_history(limit=n)
                if not history:
                    return "暂无对话历史。"

                formatted = []
                for msg in history:
                    role = "用户" if msg.get("role") == "user" else "助手"
                    content = msg.get("content", "")
                    # 截断长内容
                    if len(content) > 200:
                        content = content[:200] + "..."
                    formatted.append(f"{role}：{content}")

                return "\n".join(formatted)
            except Exception as e:
                return f"获取历史失败：{str(e)}"

        return get_conversation_history

    def _create_resume_analysis_tool(self):
        """创建简历分析工具"""
        from app.services.resume_service import (
            extract_skills, analyze_match, get_suggestions,
            optimize_project, generate_questions
        )

        @tool
        def analyze_resume(resume_text: str, jd_text: str = "") -> str:
            """
            分析简历，提供技能提取、匹配度分析、优化建议等。
            
            当用户需要简历相关分析时使用此工具。
            
            Args:
                resume_text: 简历文本
                jd_text: 岗位描述文本（可选）
            
            Returns:
                结构化分析结果
            """
            try:
                result = {}

                # 1. 提取技能
                skills = extract_skills(resume_text)
                result["skills"] = skills

                # 2. 如果有 JD，分析匹配度
                if jd_text:
                    match_result = analyze_match(resume_text, jd_text, skills)
                    result["match"] = match_result

                    # 3. 提供修改建议
                    suggestions = get_suggestions(resume_text, jd_text)
                    result["suggestions"] = suggestions

                return json.dumps(result, ensure_ascii=False, indent=2)
            except Exception as e:
                return f"简历分析失败：{str(e)}"

        return analyze_resume

    def _create_document_summary_tool(self):
        """创建文档摘要工具"""
        from app.services.office_service import get_office_service

        @tool
        def summarize_document(text: str, summary_type: str = "brief") -> str:
            """
            对文档进行智能总结。
            
            支持多种总结类型：
            - brief: 简短总结
            - meeting: 会议纪要
            - detailed: 详细总结
            
            Args:
                text: 文档文本
                summary_type: 总结类型
            
            Returns:
                结构化总结结果
            """
            try:
                service = get_office_service()

                if summary_type == "meeting":
                    result = service.generate_meeting_minutes(text)
                else:
                    result = service.summarize_document(text)

                return json.dumps(result, ensure_ascii=False, indent=2)
            except Exception as e:
                return f"文档总结失败：{str(e)}"

        return summarize_document

    def _create_agent(self):
        """创建 Agent（LangChain 1.x create_agent）"""
        system_prompt = """你是一个智能个人助手，可以访问以下工具：

1. search_knowledge_base: 在个人知识库中搜索信息
2. get_conversation_history: 获取对话历史
3. analyze_resume: 分析简历
4. summarize_document: 总结文档

请根据用户的问题，自主决定是否需要使用工具以及使用哪些工具。

使用规则：
1. 如果用户询问个人知识库中的内容（如简历、项目经历、技能），使用 search_knowledge_base
2. 如果需要了解之前的对话，使用 get_conversation_history
3. 如果用户需要简历分析，使用 analyze_resume
4. 如果用户需要文档总结，使用 summarize_document
5. 如果问题简单且不需要工具，直接回答

请以自然、专业的方式回答，并在使用工具时标注信息来源。"""

        return create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
        )

    def chat(self, user_input: str) -> dict:
        """
        Agent 对话接口
        """
        try:
            # create_agent 使用 messages 格式
            result = self.agent.invoke({
                "messages": [{"role": "user", "content": user_input}]
            })

            # 提取最后一条 AI 消息作为回答
            messages = result.get("messages", [])
            ai_messages = [m for m in messages if getattr(m, "type", None) == "ai" and hasattr(m, "content")]
            response_text = ai_messages[-1].content if ai_messages else ""

            # 提取工具调用步骤
            tool_steps = []
            for m in messages:
                if getattr(m, "type", None) == "tool":
                    tool_steps.append({
                        "tool": getattr(m, "name", "unknown"),
                        "result": getattr(m, "content", ""),
                    })

            return {
                "response": response_text,
                "tool_used": tool_steps,
                "is_agent": True
            }
        except Exception as e:
            print(f"Agent 执行失败，降级到 RAG: {e}")
            return self.rag.chat(user_input)


# 模块级单例
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """获取 Agent 服务单例"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
