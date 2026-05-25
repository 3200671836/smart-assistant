"""
Agent API 路由
提供真正的 Agent 对话接口
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models import get_db
from app.services.history_service import HistoryService
from app.services.agent_service import get_agent_service

router = APIRouter(prefix="/agent", tags=["智能助手"])


class AgentChatRequest(BaseModel):
    """Agent 对话请求"""
    message: str
    use_agent: bool = True  # 是否使用 Agent 模式


class AgentChatResponse(BaseModel):
    """Agent 对话响应"""
    response: str
    tool_used: List[str] = []
    is_agent: bool = False
    sources: Optional[List[dict]] = None  # RAG 模式下的引用


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(req: AgentChatRequest, db: Session = Depends(get_db)):
    """
    Agent 对话接口
    
    支持两种模式：
    1. Agent 模式（默认）：使用工具调用和自主决策
    2. RAG 模式（降级）：直接使用 RAG 检索增强
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    try:
        agent_service = get_agent_service()
        
        if req.use_agent:
            # Agent 模式
            result = agent_service.chat(req.message)
            
            # 保存历史
            history_svc = HistoryService(db)
            history_svc.create(
                tool_name="agent_chat",
                input_summary=req.message[:200],
                result_json={
                    "response": result["response"][:500],
                    "tool_used": result.get("tool_used", []),
                    "is_agent": result.get("is_agent", False)
                },
                result_text=result["response"]
            )
            
            return AgentChatResponse(
                response=result["response"],
                tool_used=result.get("tool_used", []),
                is_agent=result.get("is_agent", False)
            )
        else:
            # RAG 模式（降级）
            from app.RAG.rag import RagService
            rag = RagService()
            result = rag.chat(req.message)
            
            # 保存历史
            history_svc = HistoryService(db)
            history_svc.create(
                tool_name="rag_chat",
                input_summary=req.message[:200],
                result_json={
                    "response": result["response"][:500],
                    "sources": result.get("sources", [])
                },
                result_text=result["response"]
            )
            
            return AgentChatResponse(
                response=result["response"],
                tool_used=["rag_retrieval"],
                is_agent=False,
                sources=result.get("sources", [])
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 服务异常: {str(e)}")


@router.get("/tools")
async def list_available_tools():
    """列出可用的 Agent 工具"""
    try:
        agent_service = get_agent_service()
        tools = []
        
        for tool in agent_service.tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "args": str(tool.args)
            })
        
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")


class ToolTestRequest(BaseModel):
    """工具测试请求"""
    tool_name: str
    tool_args: dict


@router.post("/test-tool")
async def test_tool(req: ToolTestRequest):
    """测试特定工具"""
    try:
        agent_service = get_agent_service()
        
        # 查找工具
        target_tool = None
        for tool in agent_service.tools:
            if tool.name == req.tool_name:
                target_tool = tool
                break
        
        if not target_tool:
            raise HTTPException(status_code=404, detail=f"工具 '{req.tool_name}' 不存在")
        
        # 执行工具
        result = target_tool(**req.tool_args)
        
        return {
            "tool_name": req.tool_name,
            "result": result,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工具执行失败: {str(e)}")