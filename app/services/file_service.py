import os
import uuid
import pdfplumber
from docx import Document
from fastapi import UploadFile

from app.core.config import settings


ALLOWED_EXTS = {".pdf", ".docx", ".doc", ".txt"}


def allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[-1].lower()
    return ext in ALLOWED_EXTS


async def parse_file(file: UploadFile) -> str:
    """根据文件类型调用对应解析器，返回纯文本"""
    ext = os.path.splitext(file.filename)[-1].lower()

    if ext == ".pdf":
        return await _parse_pdf(file)
    elif ext in {".docx", ".doc"}:
        return await _parse_docx(file)
    elif ext == ".txt":
        return await _parse_txt(file)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


async def _parse_pdf(file: UploadFile) -> str:
    """从上传的PDF文件对象中提取文本"""
    contents = await file.read()

    # 写入临时文件，pdfplumber需要文件路径
    temp_path = os.path.join(settings.upload_dir, f"_temp_{uuid.uuid4().hex}.pdf")
    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        text_parts = []
        with pdfplumber.open(temp_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
        return "\n".join(text_parts)
    finally:
        os.remove(temp_path)


async def _parse_docx(file: UploadFile) -> str:
    """从上传的DOCX文件对象中提取文本"""
    contents = await file.read()

    temp_path = os.path.join(settings.upload_dir, f"_temp_{uuid.uuid4().hex}.docx")
    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        doc = Document(temp_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    finally:
        os.remove(temp_path)


async def _parse_txt(file: UploadFile) -> str:
    """直接读取文本文件内容"""
    contents = await file.read()
    # 尝试 UTF-8，失败则 fallback 到 GBK
    try:
        return contents.decode("utf-8")
    except UnicodeDecodeError:
        return contents.decode("gbk", errors="replace")


def save_upload(file: UploadFile) -> str:
    """保存上传文件到本地目录，返回存储路径"""
    ext = os.path.splitext(file.filename)[-1].lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(settings.upload_dir, stored_name)

    # 文件已由 FastAPI 流式写入到这里，直接读取即可
    with open(stored_path, "wb") as f:
        for chunk in iter(lambda: file.file.read(8192), b""):
            f.write(chunk)

    return stored_path
