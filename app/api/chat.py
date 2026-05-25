from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.RAG.rag import RagService
from app.db.models import get_db
from app.services.history_service import HistoryService

router = APIRouter(prefix="/chat", tags=["AI对话"])

# 模块级单例
_rag_service: RagService | None = None


def get_rag_service() -> RagService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RagService()
    return _rag_service


class Source(BaseModel):
    id: int
    doc: str
    text: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    sources: List[Source]


@router.post("/send", response_model=ChatResponse)
async def chat_send(req: ChatRequest, db: Session = Depends(get_db)):
    """非流式对话（带引用溯源）"""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    rag = get_rag_service()
    result = rag.chat(req.message)
    
    # 保存对话历史到数据库
    history_svc = HistoryService(db)
    history_svc.create(
        tool_name="chat",
        input_summary=req.message[:200],
        result_json={
            "response": result["response"][:500],
            "sources": result["sources"]
        },
        result_text=result["response"]
    )
    
    return ChatResponse(
        response=result["response"],
        sources=[Source(**s) for s in result["sources"]]
    )


@router.post("/stream")
async def chat_stream(req: ChatRequest, db: Session = Depends(get_db)):
    """流式对话（SSE，带引用溯源）"""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    rag = get_rag_service()
    
    # 用于收集完整响应
    full_response = ""
    sources_data = []

    async def event_generator():
        nonlocal full_response, sources_data
        for chunk in rag.chat_stream(req.message):
            if isinstance(chunk, dict) and chunk.get("done"):
                # 最后一条是引用信息
                sources_data = chunk.get("sources", [])
                # 发送引用信息作为特殊事件
                import json
                yield f"event: sources\ndata: {json.dumps(sources_data, ensure_ascii=False)}\n\n"
            else:
                # 普通文本块
                full_response += chunk
                yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
        
        # 流结束后保存到数据库
        try:
            history_svc = HistoryService(db)
            history_svc.create(
                tool_name="chat",
                input_summary=req.message[:200],
                result_json={
                    "response": full_response[:500],
                    "sources": sources_data
                },
                result_text=full_response
            )
        except Exception as e:
            print(f"保存对话历史失败: {e}")

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
