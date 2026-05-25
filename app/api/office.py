"""
办公工具 API 路由
提供文档总结、会议纪要生成接口
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import get_db
from app.services.history_service import HistoryService
from app.services.office_service import get_office_service
from app.api.schemas import SummarizeRequest, MeetingMinutesRequest

router = APIRouter(prefix="/office", tags=["办公工具"])


def _save_history(db: Session, tool_name: str, input_summary: str, result: dict):
    """统一记录历史"""
    svc = HistoryService(db)
    svc.create(tool_name=tool_name, input_summary=input_summary, result_json=result)


@router.post("/summarize")
def api_summarize(req: SummarizeRequest, db: Session = Depends(get_db)):
    """文档智能总结：输入长文本，返回一句话总结 + 关键要点"""
    service = get_office_service()
    result = service.summarize_document(req.text)
    _save_history(
        db, "summarize",
        f"文档总结（{len(req.text)}字）",
        result,
    )
    return result


@router.post("/meeting-minutes")
def api_meeting_minutes(req: MeetingMinutesRequest, db: Session = Depends(get_db)):
    """会议纪要生成：输入会议记录，返回结构化议题与待办事项"""
    service = get_office_service()
    result = service.generate_meeting_minutes(req.text)
    _save_history(
        db, "meeting_minutes",
        f"会议纪要（{len(req.text)}字）",
        result,
    )
    return result
