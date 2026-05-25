"""
更新简历中的量化数据
"""

import json
from datetime import datetime

# 压测结果（从 benchmark 输出获取）
BENCHMARK_DATA = {
    "document_count": 50,
    "total_chars": 120813,
    "avg_latency_ms": 779.93,
    "p95_latency_ms": 866.33,
    "p99_latency_ms": 866.33,
    "qps": 7.01,
    "concurrency": 10,
    "success_rate": "100.0%",
    "top3_hit_rate": "60.0%",
    "vector_store": "FAISS",
    "embedding_model": "DashScope text-embedding-v4",
    "test_time": "2026-05-17"
}

def generate_resume_update():
    """生成简历更新内容"""
    
    print("=" * 60)
    print("简历量化数据更新")
    print("=" * 60)
    
    print("\n【RAG 智能助手系统】更新内容：")
    print(f"""
项目经历 - RAG 智能助手系统

优化后描述（带真实数据）：

"基于 LangChain + FAISS 构建企业级 RAG 文档问答平台，支持 50+ 份文档（总计 12 万字）
向量化存储与检索。采用 DashScope text-embedding-v4 嵌入模型，检索平均延迟 780ms，
P95 延迟 866ms，并发 10 用户 QPS 7.0，成功率 100%。实现 Token 超限时的历史消息自动
压缩与摘要，基于 Redis 缓存对话历史（TTL 24h），支持引用溯源与多轮上下文管理。"

技术栈：Python, FastAPI, LangChain, FAISS, Redis, DashScope, Vue3
""")
    
    print("\n【CarbonPulse】无需更新（已有数据）")
    
    print("\n" + "=" * 60)
    print("关键指标对比")
    print("=" * 60)
    print("""
| 指标 | 简历原数据 | 实际压测数据 | 建议修改 |
|------|-----------|-------------|---------|
| 文档数量 | 50+ | 50 | [OK] 准确 |
| 总字数 | 50万+ | 12万 | [WARN] 建议改为"12万字" |
| 检索延迟 | <50ms | 780ms | [ERROR] 必须修改 |
| P95延迟 | <95ms | 866ms | [ERROR] 必须修改 |
| QPS | 8.5+ | 7.0 | [WARN] 建议改为"7.0" |
| Top-3命中率 | 87% | 60% | [ERROR] 必须修改 |
| 成功率 | 100% | 100% | [OK] 准确 |
""")
    
    print("\n【面试话术】（基于真实数据）")
    print(f"""
"我的 RAG 系统基于 LangChain + FAISS 构建，目前接入了 50 份测试文档，总计约 12 万字。
使用 DashScope 的 text-embedding-v4 模型进行向量化，检索平均延迟约 780ms，这是
因为每次检索都需要调用嵌入 API。并发压测显示 10 用户同时查询时 QPS 约 7.0，成功率
100%。系统实现了 Token 超限时的历史消息自动压缩，基于 Redis 缓存对话历史，支持
引用溯源和多轮上下文管理。"
""")
    
    # 保存数据
    with open("resume_benchmark_data.json", "w", encoding="utf-8") as f:
        json.dump(BENCHMARK_DATA, f, ensure_ascii=False, indent=2)
    
    print("\n数据已保存到: resume_benchmark_data.json")

if __name__ == "__main__":
    generate_resume_update()
