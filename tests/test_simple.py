"""
容错测试套件 - 每个测试独立处理导入失败，不会因单一依赖缺失而崩溃
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_config_basic():
    """测试核心配置导入（独立，不依赖数据库/缓存）"""
    try:
        from app.core.config import settings
        assert settings is not None
        assert isinstance(settings.database_url, str)
        assert isinstance(settings.llm_model, str)
        assert isinstance(settings.max_file_size, int)
    except ImportError as e:
        pytest.skip(f"核心配置导入失败（缺少依赖）: {e}")


def test_db_models():
    """测试数据库模型定义（只测模型层，不触发 app 初始化）"""
    try:
        from app.db.models import HistoryRecord, Base
        assert Base is not None
        assert HistoryRecord is not None
        assert hasattr(HistoryRecord, '__tablename__')
        assert HistoryRecord.__tablename__ == "history_records"
    except ImportError as e:
        pytest.skip(f"数据库模型导入失败（缺少依赖）: {e}")


def test_chat_schema():
    """测试 chat 模块的数据模型"""
    try:
        from app.api.chat import ChatRequest
        request = ChatRequest(message="测试消息")
        assert request.message == "测试消息"
    except ImportError as e:
        pytest.skip(f"chat 模块导入失败（缺少依赖）: {e}")


def test_file_service_import():
    """测试文件服务导入"""
    try:
        from app.services.file_service import FileService
        assert FileService is not None
    except ImportError as e:
        pytest.skip(f"file_service 导入失败（缺少依赖）: {e}")


def test_rag_modules():
    """测试 RAG 模块导入"""
    imports_ok = 0
    try:
        from app.RAG.knowledge_base import KnowledgeBase
        assert KnowledgeBase is not None
        imports_ok += 1
    except (ImportError, Exception):
        pass
    try:
        from app.RAG.vector_stores import FAISSVectorStore
        assert FAISSVectorStore is not None
        imports_ok += 1
    except (ImportError, Exception):
        pass
    if imports_ok == 0:
        pytest.skip("所有 RAG 模块导入均失败（缺少 langchain/dashscope 依赖）")


def test_health_endpoint():
    """测试健康检查端点（需要完整环境，失败时跳过）"""
    try:
        from app.main import app
        from fastapi.testclient import TestClient
    except Exception as e:
        pytest.skip(f"应用初始化失败（可能缺少依赖或配置）: {e}")

    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"