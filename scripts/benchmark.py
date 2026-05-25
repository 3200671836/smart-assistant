"""
RAG 系统压测脚本
测试检索延迟、并发 QPS、准确率
"""

import time
import asyncio
import aiohttp
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
sys.path.insert(0, 'D:\\develop\\smart-assistant\\backend')
from app.RAG.knowledge_base import KnowledgeBaseService

# 测试查询
TEST_QUERIES = [
    "王鸿博是谁",
    "Python开发工程师",
    "有机器学习经验的人",
    "Java后端开发",
    "前端开发工程师",
    "数据分析",
    "产品经理",
    "UI设计师",
    "运维工程师",
    "测试工程师",
    "算法工程师",
    "全栈开发",
    "DevOps工程师",
    "数据工程师",
    "安全工程师",
    "区块链开发",
    "嵌入式开发",
    "游戏开发",
    "云计算工程师",
    "AI工程师",
]

def test_retrieval_latency(kb: KnowledgeBaseService, queries: list, top_k: int = 3):
    """测试检索延迟"""
    latencies = []
    results = []
    
    for query in queries:
        start = time.time()
        # 使用 FAISS 的 similarity_search
        if kb.faiss is not None:
            docs = kb.faiss.similarity_search(query, k=top_k)
        else:
            docs = []
        latency = (time.time() - start) * 1000  # ms
        latencies.append(latency)
        results.append({
            "query": query,
            "latency_ms": round(latency, 2),
            "results_count": len(docs)
        })
    
    return {
        "avg_latency_ms": round(statistics.mean(latencies), 2),
        "min_latency_ms": round(min(latencies), 2),
        "max_latency_ms": round(max(latencies), 2),
        "p95_latency_ms": round(sorted(latencies)[int(len(latencies)*0.95)], 2),
        "p99_latency_ms": round(sorted(latencies)[int(len(latencies)*0.99)], 2),
        "details": results
    }

def test_concurrent_qps(kb: KnowledgeBaseService, queries: list, concurrency: int = 10):
    """测试并发 QPS"""
    start_time = time.time()
    success_count = 0
    error_count = 0
    latencies = []
    
    def worker(query):
        try:
            s = time.time()
            if kb.faiss is not None:
                docs = kb.faiss.similarity_search(query, k=3)
            else:
                docs = []
            lat = (time.time() - s) * 1000
            return {"success": True, "latency_ms": lat, "count": len(docs)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        # 每个并发线程执行多个查询
        for i in range(concurrency):
            for q in queries[:5]:  # 每个线程5个查询
                futures.append(executor.submit(worker, q))
        
        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                success_count += 1
                latencies.append(result["latency_ms"])
            else:
                error_count += 1
    
    total_time = time.time() - start_time
    total_queries = len(futures)
    qps = total_queries / total_time if total_time > 0 else 0
    
    return {
        "concurrency": concurrency,
        "total_queries": total_queries,
        "success_rate": f"{success_count/total_queries*100:.1f}%",
        "qps": round(qps, 2),
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
        "total_time_sec": round(total_time, 2)
    }

def test_accuracy(kb: KnowledgeBaseService, test_cases: list):
    """测试检索准确率"""
    # 简化的准确率测试：检查返回结果是否包含关键词
    hit_count = 0
    total = len(test_cases)
    
    for case in test_cases:
        query = case["query"]
        expected_keywords = case.get("expected_keywords", [])
        
        if kb.faiss is not None:
            docs = kb.faiss.similarity_search(query, k=3)
        else:
            docs = []
        
        # 检查 Top-3 是否包含预期关键词
        found = False
        for doc in docs:
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            if any(kw in content for kw in expected_keywords):
                found = True
                break
        
        if found:
            hit_count += 1
    
    return {
        "top3_hit_rate": f"{hit_count/total*100:.1f}%",
        "hit_count": hit_count,
        "total_queries": total
    }

def run_benchmark():
    """运行完整压测"""
    print("=" * 60)
    print("RAG 系统性能压测")
    print("=" * 60)
    
    kb = KnowledgeBaseService()
    
    # 1. 检索延迟测试
    print("\n[1/3] 检索延迟测试...")
    latency_result = test_retrieval_latency(kb, TEST_QUERIES[:10])
    print(f"  平均延迟: {latency_result['avg_latency_ms']} ms")
    print(f"  P95延迟: {latency_result['p95_latency_ms']} ms")
    print(f"  P99延迟: {latency_result['p99_latency_ms']} ms")
    
    # 2. 并发 QPS 测试
    print("\n[2/3] 并发 QPS 测试...")
    qps_result = test_concurrent_qps(kb, TEST_QUERIES, concurrency=10)
    print(f"  并发数: {qps_result['concurrency']}")
    print(f"  总查询数: {qps_result['total_queries']}")
    print(f"  成功率: {qps_result['success_rate']}")
    print(f"  QPS: {qps_result['qps']}")
    print(f"  平均延迟: {qps_result['avg_latency_ms']} ms")
    
    # 3. 准确率测试
    print("\n[3/3] 检索准确率测试...")
    accuracy_cases = [
        {"query": "王鸿博", "expected_keywords": ["王鸿博"]},
        {"query": "Python", "expected_keywords": ["Python"]},
        {"query": "机器学习", "expected_keywords": ["机器学习"]},
        {"query": "Java", "expected_keywords": ["Java"]},
        {"query": "前端", "expected_keywords": ["前端", "Vue", "React"]},
    ]
    accuracy_result = test_accuracy(kb, accuracy_cases)
    print(f"  Top-3 命中率: {accuracy_result['top3_hit_rate']}")
    
    # 汇总报告
    print("\n" + "=" * 60)
    print("压测报告")
    print("=" * 60)
    report = {
        "retrieval_latency": latency_result,
        "concurrent_qps": qps_result,
        "accuracy": accuracy_result,
        "vector_store": "FAISS",
        "embedding_model": "DashScope",
        "document_count": 50
    }
    
    # 保存报告
    import json
    from datetime import datetime
    report_file = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {report_file}")
    print("\n关键指标:")
    print(f"  - 检索平均延迟: {latency_result['avg_latency_ms']} ms")
    print(f"  - P95延迟: {latency_result['p95_latency_ms']} ms")
    print(f"  - 并发 QPS: {qps_result['qps']}")
    print(f"  - Top-3 命中率: {accuracy_result['top3_hit_rate']}")
    
    return report

if __name__ == "__main__":
    run_benchmark()
