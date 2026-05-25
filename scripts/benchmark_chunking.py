"""
对比压测：旧配置 vs 新配置（语义分块）
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import shutil
import time
import json
from concurrent.futures import ThreadPoolExecutor


def benchmark_with_config(config_name, chunk_size, chunk_overlap, separators, max_split):
    """使用指定配置运行压测"""
    
    # 动态修改配置
    from app.RAG import config_data as config
    config.chunk_size = chunk_size
    config.chunk_overlap = chunk_overlap
    config.separators = separators
    config.max_split_char_number = max_split
    
    # 清除旧索引
    if os.path.exists(config.faiss_index_path):
        shutil.rmtree(config.faiss_index_path)
    if os.path.exists(config.md5_path):
        os.remove(config.md5_path)
    
    # 重新导入以应用新配置
    from app.RAG.knowledge_base import KnowledgeBaseService
    
    kb = KnowledgeBaseService()
    
    # 入库50份简历
    resumes_dir = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'resumes')
    resume_files = sorted([f for f in os.listdir(resumes_dir) if f.endswith('.txt')])[:50]
    
    total_chars = 0
    for filename in resume_files:
        with open(os.path.join(resumes_dir, filename), 'r', encoding='utf-8') as f:
            content = f.read()
        total_chars += len(content)
        kb.upload_by_str(content, filename)
    
    # 获取分块统计
    total_chunks = len(kb.faiss.docstore._dict)
    
    # 测试查询
    test_queries = [
        "Python developer",
        "machine learning",
        "Java backend",
        "frontend developer",
        "data analysis",
        "product manager",
        "UI designer",
        "DevOps engineer",
        "test engineer",
        "software architect"
    ]
    
    # 检索延迟测试
    latencies = []
    retriever = kb.faiss.as_retriever(search_kwargs={"k": 3})
    
    for query in test_queries:
        start = time.time()
        results = retriever.invoke(query)
        latency = (time.time() - start) * 1000
        latencies.append({
            "query": query,
            "latency_ms": round(latency, 2),
            "results_count": len(results)
        })
    
    avg_latency = sum(l["latency_ms"] for l in latencies) / len(latencies)
    min_latency = min(l["latency_ms"] for l in latencies)
    max_latency = max(l["latency_ms"] for l in latencies)
    
    # 并发QPS测试
    def query_task(q):
        start = time.time()
        try:
            retriever.invoke(q)
            return (time.time() - start) * 1000, True
        except:
            return (time.time() - start) * 1000, False
    
    concurrent_queries = test_queries * 5  # 50 queries
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(query_task, concurrent_queries))
    
    total_time = time.time() - start_time
    success_count = sum(1 for _, success in results if success)
    qps = len(concurrent_queries) / total_time
    
    return {
        "config": config_name,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "document_count": len(resume_files),
        "total_chars": total_chars,
        "total_chunks": total_chunks,
        "avg_chars_per_chunk": round(total_chars / total_chunks, 1) if total_chunks > 0 else 0,
        "retrieval_latency": {
            "avg_ms": round(avg_latency, 2),
            "min_ms": round(min_latency, 2),
            "max_ms": round(max_latency, 2)
        },
        "concurrent": {
            "concurrency": 10,
            "total_queries": len(concurrent_queries),
            "success_rate": f"{success_count/len(concurrent_queries)*100:.1f}%",
            "qps": round(qps, 2),
            "total_time_sec": round(total_time, 2)
        }
    }


def main():
    print("=" * 80)
    print("文档分块策略对比压测")
    print("=" * 80)
    
    # 旧配置
    old_config = (
        "旧配置 (chunk_size=1000)",
        1000, 100,
        ["\n\n", "\n", ".", ",", "，", "。", "?", "!", "？", "！", " ", ""],
        1000
    )
    
    # 新配置
    new_config = (
        "新配置 (chunk_size=500, 优化separators)",
        500, 50,
        ["\n\n", "\n", "。", "？", "！", "；", "...", "..", ".", "?", "!", ";", "，", ",", " ", ""],
        750
    )
    
    results = []
    
    for config_params in [old_config, new_config]:
        name = config_params[0]
        print(f"\n>>> 测试: {name}")
        print("-" * 40)
        
        result = benchmark_with_config(*config_params)
        results.append(result)
        
        print(f"文档数: {result['document_count']}")
        print(f"总字符: {result['total_chars']}")
        print(f"分块数: {result['total_chunks']}")
        print(f"平均每块: {result['avg_chars_per_chunk']} 字符")
        print(f"检索延迟: avg={result['retrieval_latency']['avg_ms']}ms")
        print(f"并发QPS: {result['concurrent']['qps']}")
        print(f"成功率: {result['concurrent']['success_rate']}")
    
    # 对比结果
    print("\n" + "=" * 80)
    print("对比结果")
    print("=" * 80)
    
    old = results[0]
    new = results[1]
    
    print(f"\n{'指标':<30} {'旧配置':<15} {'新配置':<15} {'变化':<15}")
    print("-" * 80)
    print(f"{'分块数量':<30} {old['total_chunks']:<15} {new['total_chunks']:<15} {'+' + str(new['total_chunks'] - old['total_chunks']) if new['total_chunks'] > old['total_chunks'] else str(new['total_chunks'] - old['total_chunks']):<15}")
    print(f"{'平均每块大小':<30} {old['avg_chars_per_chunk']:<15} {new['avg_chars_per_chunk']:<15} {str(round(new['avg_chars_per_chunk'] - old['avg_chars_per_chunk'], 1)):<15}")
    print(f"{'检索延迟(ms)':<30} {old['retrieval_latency']['avg_ms']:<15} {new['retrieval_latency']['avg_ms']:<15} {str(round(new['retrieval_latency']['avg_ms'] - old['retrieval_latency']['avg_ms'], 2)):<15}")
    print(f"{'并发QPS':<30} {old['concurrent']['qps']:<15} {new['concurrent']['qps']:<15} {str(round(new['concurrent']['qps'] - old['concurrent']['qps'], 2)):<15}")
    
    # 保存结果
    output = {
        "test_time": "2026-05-17",
        "results": results
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "benchmark_chunking_result.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] 结果已保存: {output_path}")


if __name__ == "__main__":
    main()
