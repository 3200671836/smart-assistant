"""
Redis 测试接口
用于验证 Redis 连接和缓存功能
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Optional
from app.core.redis_client import get_cache, get_redis_client

router = APIRouter(prefix="/redis", tags=["Redis测试"])


class CacheRequest(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = 3600


class CacheResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


@router.get("/ping")
async def redis_ping():
    """测试 Redis 连接"""
    try:
        client = get_redis_client()
        client.ping()
        info = client.info()
        return {
            "success": True,
            "message": "Redis 连接正常",
            "version": info.get("redis_version", "unknown"),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Redis 连接失败: {str(e)}"
        }


@router.post("/set")
async def redis_set(req: CacheRequest):
    """设置缓存"""
    try:
        cache = get_cache()
        cache.set(req.key, req.value, ttl=req.ttl)
        return CacheResponse(
            success=True,
            message=f"缓存设置成功 (TTL: {req.ttl}s)",
            data={"key": req.key, "value": req.value}
        )
    except Exception as e:
        return CacheResponse(
            success=False,
            message=f"缓存设置失败: {str(e)}"
        )


@router.get("/get/{key}")
async def redis_get(key: str):
    """获取缓存"""
    try:
        cache = get_cache()
        value = cache.get(key)
        return CacheResponse(
            success=True,
            message="缓存获取成功" if value is not None else "缓存未命中",
            data=value
        )
    except Exception as e:
        return CacheResponse(
            success=False,
            message=f"缓存获取失败: {str(e)}"
        )


@router.delete("/delete/{key}")
async def redis_delete(key: str):
    """删除缓存"""
    try:
        cache = get_cache()
        cache.delete(key)
        return CacheResponse(
            success=True,
            message=f"缓存删除成功: {key}"
        )
    except Exception as e:
        return CacheResponse(
            success=False,
            message=f"缓存删除失败: {str(e)}"
        )


@router.get("/stats")
async def redis_stats():
    """Redis 统计信息"""
    try:
        client = get_redis_client()
        info = client.info()
        
        # 获取 RAG 相关的键
        rag_keys = client.keys("rag:*")
        chat_keys = client.keys("chat_history:*")
        
        return {
            "success": True,
            "redis_version": info.get("redis_version"),
            "used_memory": info.get("used_memory_human"),
            "total_keys": client.dbsize(),
            "rag_keys_count": len(rag_keys),
            "chat_keys_count": len(chat_keys),
            "connected_clients": info.get("connected_clients"),
            "uptime_in_seconds": info.get("uptime_in_seconds")
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取统计失败: {str(e)}"
        }
