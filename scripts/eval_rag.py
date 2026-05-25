"""
RAG 系统评测基准脚本
用于评估向量检索的 Top-K 命中率、延迟、QPS 等指标
"""

import os
import sys
import json
import time
import asyncio
from typing import List, Dict, Tuple
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.RAG.knowledge_base import KnowledgeBaseService


class RAGEvaluator:
    """RAG 系统评测器"""
    
    def __init__(self, eval_data_path: str = None):
        """
        Args:
            eval_data_path: 评测数据 JSON 文件路径
        """
        self.kb = KnowledgeBaseService()
        self.eval_data = self._load_eval_data(eval_data_path)
    
    def _load_eval_data(self, path: str = None) -> List[Dict]:
        """加载评测数据（标注好的问题-期望回答映射）"""
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # 默认使用内置评测数据
        return self._get_builtin_eval_data()
    
    def _get_builtin_eval_data(self) -> List[Dict]:
        """内置评测数据集（需要用户根据实际文档调整）"""
        return [
            {
                "question": "我的Python技能水平如何？",
                "expected_keywords": ["Python", "开发", "编程"],
                "expected_chunk_count": 3
            },
            {
                "question": "简历中的项目经历有哪些？",
                "expected_keywords": ["项目", "经历", "开发"],
                "expected_chunk_count": 3
            },
            {
                "question": "我有哪些证书和资质？",
                "expected_keywords": ["证书", "资质", "认证"],
                "expected_chunk_count": 2
            },
            {
                "question": "我的教育背景是什么？",
                "expected_keywords": ["大学", "学历", "专业", "毕业"],
                "expected_chunk_count": 2
            },
            {
                "question": "我使用过哪些技术框架？",
                "expected_keywords": ["FastAPI", "Python", "SQLAlchemy", "Docker"],
                "expected_chunk_count": 3
            },
            {
                "question": "我有什么软技能？",
                "expected_keywords": ["沟通", "协作", "团队"],
                "expected_chunk_count": 2
            },
            {
                "question": "RAG系统是如何实现的？",
                "expected_keywords": ["RAG", "向量", "检索", "Embedding"],
                "expected_chunk_count": 3
            },
        ]
    
    def evaluate_top_k_hit_rate(self, k: int = 3) -> Dict:
        """
        评估 Top-K 命中率
        
        命中率 = 检索结果中包含期望关键词的问题数 / 总问题数
        
        Args:
            k: Top-K 中的 K
        
        Returns:
            评估结果字典
        """
        total = len(self.eval_data)
        hits = 0
        
        results = []
        
        for item in self.eval_data:
            question = item["question"]
            expected_keywords = item["expected_keywords"]
            
            # 执行检索
            retrieved_docs = self.kb.search(question, k=k)
            
            # 检查是否包含期望关键词
            retrieved_text = " ".join([doc.page_content for doc in retrieved_docs])
            
            hit = False
            matched_keywords = []
            for keyword in expected_keywords:
                if keyword.lower() in retrieved_text.lower():
                    matched_keywords.append(keyword)
            
            if len(matched_keywords) > 0:
                hit = True
                hits += 1
            
            results.append({
                "question": question,
                "expected_keywords": expected_keywords,
                "matched_keywords": matched_keywords,
                "hit": hit,
                "retrieved_docs": [doc.page_content[:100] for doc in retrieved_docs]
            })
        
        hit_rate = hits / total if total > 0 else 0
        
        return {
            "k": k,
            "total_questions": total,
            "hits": hits,
            "hit_rate": round(hit_rate * 100, 2),
            "results": results
        }
    
    def evaluate_latency(self, k: int = 3, iterations: int = 30) -> Dict:
        """
        评估检索延迟
        
        Args:
            k: 检索返回数量
            iterations: 测试迭代次数
        
        Returns:
            延迟统计
        """
        if not self.eval_data:
            return {"error": "无评测数据"}
        
        question = self.eval_data[0]["question"]
        latencies = []
        
        # 预热
        for _ in range(3):
            self.kb.search("预热查询", k=k)
        
        # 正式测试
        for _ in range(iterations):
            start = time.perf_counter()
            self.kb.search(question, k=k)
            elapsed = (time.perf_counter() - start) * 1000  # 转换为毫秒
            latencies.append(elapsed)
        
        latencies.sort()
        
        # 计算统计指标
        avg = sum(latencies) / len(latencies)
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        min_latency = latencies[0]
        max_latency = latencies[-1]
        
        return {
            "iterations": iterations,
            "k": k,
            "avg_ms": round(avg, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "min_ms": round(min_latency, 2),
            "max_ms": round(max_latency, 2),
            "qps": round(1000 / avg, 2)  # 纯检索 QPS
        }
    
    def evaluate_qps_concurrent(self, k: int = 3, concurrent: int = 10, total_requests: int = 100) -> Dict:
        """
        并发 QPS 测试
        
        Args:
            k: 检索返回数量
            concurrent: 并发数
            total_requests: 总请求数
        
        Returns:
            QPS 统计
        """
        if not self.eval_data:
            return {"error": "无评测数据"}
        
        questions = []
        for i in range(total_requests):
            questions.append(self.eval_data[i % len(self.eval_data)]["question"])
        
        latencies = []
        start_time = time.perf_counter()
        
        # 同步方式逐个执行（简单实现）
        for question in questions:
            req_start = time.perf_counter()
            self.kb.search(question, k=k)
            req_elapsed = (time.perf_counter() - req_start) * 1000
            latencies.append(req_elapsed)
        
        total_time = time.perf_counter() - start_time
        qps = total_requests / total_time
        
        latencies.sort()
        
        return {
            "total_requests": total_requests,
            "total_time_s": round(total_time, 3),
            "qps": round(qps, 2),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "p95_latency_ms": round(latencies[int(len(latencies) * 0.95)], 2),
        }
    
    def run_full_benchmark(self) -> Dict:
        """运行完整评测"""
        print("=" * 60)
        print("RAG 系统完整评测")
        print("=" * 60)
        
        # 1. Top-K 命中率
        print("\n[1/3] 评估 Top-K 命中率...")
        hit_rate_result = self.evaluate_top_k_hit_rate(k=3)
        print(f"  Top-3 命中率: {hit_rate_result['hit_rate']}% ({hit_rate_result['hits']}/{hit_rate_result['total_questions']})")
        
        # 2. 检索延迟
        print("\n[2/3] 评估检索延迟...")
        latency_result = self.evaluate_latency(k=3, iterations=30)
        print(f"  平均延迟: {latency_result['avg_ms']}ms")
        print(f"  P95 延迟: {latency_result['p95_ms']}ms")
        print(f"  纯检索 QPS: {latency_result['qps']}")
        
        # 3. 并发 QPS
        print("\n[3/3] 评估并发 QPS...")
        qps_result = self.evaluate_qps_concurrent(k=3, total_requests=100)
        print(f"  QPS: {qps_result['qps']}")
        print(f"  平均延迟: {qps_result['avg_latency_ms']}ms")
        
        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "top_k_hit_rate": hit_rate_result,
            "latency": latency_result,
            "qps": qps_result,
            "summary": {
                "top_3_hit_rate": f"{hit_rate_result['hit_rate']}%",
                "avg_latency_ms": latency_result['avg_ms'],
                "p95_latency_ms": latency_result['p95_ms'],
                "retrieval_qps": latency_result['qps'],
                "retrieval_note": "纯向量检索 QPS，不含 LLM 生成"
            }
        }
        
        return report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG 系统评测")
    parser.add_argument("--eval-data", type=str, help="自定义评测数据 JSON 文件路径")
    parser.add_argument("--output", type=str, default="benchmark_report.json", help="输出报告路径")
    parser.add_argument("--top-k", type=int, default=3, help="Top-K 评估")
    parser.add_argument("--iterations", type=int, default=30, help="延迟测试迭代次数")
    
    args = parser.parse_args()
    
    evaluator = RAGEvaluator(eval_data_path=args.eval_data)
    report = evaluator.run_full_benchmark()
    
    # 保存报告
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.join(os.path.dirname(__file__), output_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {output_path}")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("评测摘要")
    print("=" * 60)
    print(f"Top-3 命中率: {report['summary']['top_3_hit_rate']}")
    print(f"平均延迟: {report['summary']['avg_latency_ms']}ms")
    print(f"P95 延迟: {report['summary']['p95_latency_ms']}ms")
    print(f"纯检索 QPS: {report['summary']['retrieval_qps']}")
    print(f"\n注意: {report['summary']['retrieval_note']}")


if __name__ == "__main__":
    main()