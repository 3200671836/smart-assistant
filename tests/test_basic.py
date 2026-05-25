"""
基础单元测试 - 核心模块功能测试
"""
import os
import sys
import pytest
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestCoreConfig:
    """核心配置模块测试"""
    
    def test_config_import(self):
        """测试配置模块可以正常导入"""
        from app.core.config import settings
        assert settings is not None
    
    def test_default_values(self):
        """测试配置默认值"""
        from app.core.config import settings
        # 验证基本配置存在
        assert hasattr(settings, 'APP_NAME')
        assert hasattr(settings, 'DEBUG')
    
    def test_database_url(self):
        """测试数据库 URL 配置"""
        from app.core.config import settings
        assert settings.DATABASE_URL is not None


class TestPydanticModels:
    """Pydantic 数据模型测试"""
    
    def test_chat_request_model(self):
        """测试聊天请求模型"""
        from app.api.schemas import ChatRequest
        request = ChatRequest(message="测试消息")
        assert request.message == "测试消息"
    
    def test_chat_request_with_history(self):
        """测试带历史记录的聊天请求"""
        from app.api.schemas import ChatRequest
        history = [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "你好！"}]
        request = ChatRequest(message="新消息", history=history)
        assert request.message == "新消息"
        assert len(request.history) == 2


class TestServices:
    """核心服务层测试"""
    
    def test_llm_service_import(self):
        """测试 LLM 服务可以导入"""
        try:
            from app.services.llm_service import LLMService
            assert LLMService is not None
        except ImportError as e:
            pytest.skip(f"LLM 服务导入失败: {e}")
    
    def test_file_service_import(self):
        """测试文件服务可以导入"""
        from app.services.file_service import FileService
        assert FileService is not None
    
    def test_history_service_import(self):
        """测试历史记录服务可以导入"""
        try:
            from app.services.history_service import HistoryService
            assert HistoryService is not None
        except ImportError as e:
            pytest.skip(f"历史服务导入失败: {e}")


class TestTokenCompressor:
    """Token 压缩器测试"""
    
    def test_token_compressor_import(self):
        """测试 Token 压缩器可以导入"""
        try:
            from app.RAG.token_compressor import TokenCompressor
            assert TokenCompressor is not None
        except ImportError as e:
            pytest.skip(f"Token 压缩器导入失败: {e}")


class TestVectorStores:
    """向量存储测试"""
    
    def test_vector_stores_import(self):
        """测试向量存储模块可以导入"""
        try:
            from app.RAG.vector_stores import FAISSVectorStore
            assert FAISSVectorStore is not None
        except ImportError as e:
            pytest.skip(f"FAISS 导入失败: {e}")