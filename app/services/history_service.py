from sqlalchemy.orm import Session
from app.db.models import HistoryRecord


class HistoryService:
    """历史记录的CRUD操作"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        tool_name: str,
        input_summary: str,
        result_json: dict | None = None,
        result_text: str | None = None,
    ) -> HistoryRecord:
        """新增一条记录"""
        record = HistoryRecord(
            tool_name=tool_name,
            input_summary=input_summary,
            result_json=result_json if result_json is not None else {},
            result_text=result_text if result_text is not None else "",
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list(self, page: int = 1, size: int = 10, tool_name: str | None = None) -> tuple[list[HistoryRecord], int]:
        """分页查询记录"""
        query = self.db.query(HistoryRecord)
        if tool_name:
            query = query.filter(HistoryRecord.tool_name == tool_name)
        total = query.count()
        records = (
            query
            .order_by(HistoryRecord.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return records, total

    def get(self, record_id: int) -> HistoryRecord | None:
        return self.db.query(HistoryRecord).filter(HistoryRecord.id == record_id).first()

    def delete(self, record_id: int) -> bool:
        record = self.get(record_id)
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True
