from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite专用：允许多线程访问
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class HistoryRecord(Base):
    """历史记录：保存每一次工具调用的输入输出"""
    __tablename__ = "history_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tool_name = Column(String(64), nullable=False, index=True)
    input_summary = Column(Text, nullable=False)
    result_json = Column(JSON, nullable=True)          # 结构化结果
    result_text = Column(Text, nullable=True)          # 流式/文本结果备用
    created_at = Column(DateTime, default=datetime.now, index=True)

    # 预留字段（将来扩展多用户）
    user_id = Column(Integer, nullable=True, index=True)


def get_db():
    """FastAPI依赖：每次请求获取一个session，用完自动close"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """启动时创建所有表"""
    Base.metadata.create_all(bind=engine)
