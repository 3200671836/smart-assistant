"""
Pytest 配置文件 - 提供共享 fixtures
"""
import pytest
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def test_app():
    """创建测试用的 FastAPI 应用实例"""
    from app.main import app
    return app


@pytest.fixture(scope="session")
def test_client(test_app):
    """创建测试用的 HTTP 客户端"""
    from fastapi.testclient import TestClient
    return TestClient(test_app)