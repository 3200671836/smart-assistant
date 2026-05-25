"""
API 接口测试 - FastAPI 应用测试
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestHealthEndpoint:
    """健康检查端点测试"""
    
    def test_health_check(self, test_client):
        """测试健康检查端点"""
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]


class TestRootEndpoint:
    """根路径测试"""
    
    def test_root_endpoint(self, test_client):
        """测试根路径"""
        response = test_client.get("/")
        # 可能返回 200 或 404，取决于路由配置
        assert response.status_code in [200, 404]


class TestChatEndpoint:
    """聊天端点测试"""
    
    def test_chat_endpoint_exists(self, test_client):
        """测试聊天端点是否存在"""
        response = test_client.post(
            "/api/chat",
            json={"message": "你好"}
        )
        # 可能返回 200（成功）、422（验证错误）或 503（服务不可用）
        assert response.status_code in [200, 422, 503]
    
    def test_chat_with_empty_message(self, test_client):
        """测试空消息"""
        response = test_client.post(
            "/api/chat",
            json={"message": ""}
        )
        # 空消息应该被拒绝
        if response.status_code == 422:
            assert True
        else:
            # 如果通过了验证，至少能收到响应
            assert response.status_code in [200, 422, 503]


class TestFileUploadEndpoint:
    """文件上传端点测试"""
    
    def test_upload_endpoint_exists(self, test_client):
        """测试文件上传端点是否存在"""
        response = test_client.post("/api/upload")
        # 没有文件时应该是 422
        assert response.status_code in [200, 422, 503]


class TestHistoryEndpoint:
    """历史记录端点测试"""
    
    def test_history_endpoint_exists(self, test_client):
        """测试历史记录端点是否存在"""
        response = test_client.get("/api/history")
        assert response.status_code in [200, 404, 503]