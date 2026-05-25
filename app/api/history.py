from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.models import get_db
from app.services.history_service import HistoryService
from app.api.schemas import HistoryListResponse, HistoryItem, MessageResponse

router = APIRouter(prefix="/history", tags=["历史记录"])


@router.get("", response_model=HistoryListResponse)
def list_history(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    tool_name: str | None = None,
    db: Session = Depends(get_db),
):
    """分页查询历史记录"""
    service = HistoryService(db)
    records, total = service.list(page=page, size=size, tool_name=tool_name)
    return HistoryListResponse(
        items=[HistoryItem.model_validate(r, from_attributes=True) for r in records],
        total=total,
        page=page,
        size=size,
    )


@router.get("/chat", response_model=List[HistoryItem])
def list_chat_history(
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """查询最近的对话历史（用于聊天界面初始化）"""
    service = HistoryService(db)
    records, _ = service.list(page=1, size=limit, tool_name="chat")
    # 反转顺序，让最早的在前
    records.reverse()
    return [HistoryItem.model_validate(r, from_attributes=True) for r in records]


@router.get("/{record_id}")
def get_history_detail(record_id: int, db: Session = Depends(get_db)):
    """获取单条记录详情"""
    service = HistoryService(db)
    record = service.get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {
        "id": record.id,
        "tool_name": record.tool_name,
        "input_summary": record.input_summary,
        "result_json": record.result_json,
        "result_text": record.result_text,
        "created_at": record.created_at.isoformat(),
    }


@router.delete("/{record_id}", response_model=MessageResponse)
def delete_history(record_id: int, db: Session = Depends(get_db)):
    """删除一条记录"""
    service = HistoryService(db)
    ok = service.delete(record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="记录不存在")
    return MessageResponse(message="删除成功")
