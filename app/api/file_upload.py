from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import get_db
from app.services.file_service import allowed_file, parse_file, save_upload
from app.services.history_service import HistoryService
from app.api.schemas import UploadResponse
from app.RAG.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/file", tags=["文件上传"])

# 模块级单例：避免每次请求都初始化 FAISS
_kb_service: KnowledgeBaseService | None = None

def get_kb_service() -> KnowledgeBaseService:
    global _kb_service
    if _kb_service is None:
        _kb_service = KnowledgeBaseService()
    return _kb_service


@router.post("/upload", response_model=UploadResponse)
async def upload_and_parse(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    上传简历文件 → 解析文本 → 向量化入库 → 返回纯文本内容。
    同时写入一条历史记录。
    """
    # 1. 校验文件类型
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，仅支持: {', '.join(settings.upload_dir)}"
        )

    # 2. 校验文件大小
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(status_code=400, detail="文件超过10MB限制")

    # 3. 重置文件指针（read后需要seek回开头才能再读）
    await file.seek(0)

    # 4. 解析文本
    try:
        text = await parse_file(file)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"文件解析失败: {str(e)}")

    # 5. 保存文件（可选，备用）
    await file.seek(0)
    stored_path = save_upload(file)

    # 6. RAG 向量化入库
    kb_service = get_kb_service()
    rag_result = kb_service.upload_by_str(text, file.filename)

    # 7. 写入历史记录
    history_svc = HistoryService(db)
    history_svc.create(
        tool_name="file_upload",
        input_summary=f"上传文件: {file.filename} ({len(content)} bytes)",
        result_json={"filename": file.filename, "size": len(content), "text_length": len(text), "rag_status": rag_result},
    )

    return UploadResponse(
        text=text[:5000],  # 截断防止响应过大，前端可分批请求
        filename=file.filename,
        file_size=len(content),
        rag_status=rag_result,
    )



