from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional


# ========== 通用 ==========
class MessageResponse(BaseModel):
    message: str


# ========== 文件上传 ==========
class UploadResponse(BaseModel):
    text: str
    filename: str
    file_size: int
    rag_status: str = ""  # "[成功]内容已载入向量库" 或 "[跳过]内容已存在"


# ========== 简历分析 ==========
class SkillsRequest(BaseModel):
    text: str


class SkillsResponse(BaseModel):
    skills: dict[str, list[str]]


class MatchRequest(BaseModel):
    text: str = Field(description="简历文本")
    jd_text: str = Field(description="JD文本")
    skills: Optional[dict[str, list[str]]] = Field(default=None, description="可选，预提取的技能")


class MatchResponse(BaseModel):
    match_level: str
    matched_skills: list[str]
    missing_skills: list[str]
    dimension_analysis: Optional[dict[str, str]] = None


class SuggestionsRequest(BaseModel):
    resume_text: str
    jd_requirements: str


class OptimizeRequest(BaseModel):
    desc: str = Field(description="简历中的项目描述")


class QuestionsRequest(BaseModel):
    highlights: str = Field(description="简历摘要（建议取前2000字符）")
    jd_requirements: str


# ========== 办公工具 ==========
class SummarizeRequest(BaseModel):
    text: str


class MeetingMinutesRequest(BaseModel):
    text: str


# ========== 历史记录 ==========
class HistoryItem(BaseModel):
    id: int
    tool_name: str
    input_summary: str
    result_json: Optional[dict] = Field(default_factory=dict)
    result_text: Optional[str] = Field(default="")
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    size: int
