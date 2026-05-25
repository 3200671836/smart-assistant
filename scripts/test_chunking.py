"""
测试文档分块效果
对比 RecursiveCharacterTextSplitter 和 SemanticSplitter
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.RAG.semantic_splitter import SemanticSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json


def test_splitter(splitter, text, name):
    """测试分块器并返回统计信息"""
    chunks = splitter.split_text(text)
    
    stats = {
        "splitter": name,
        "chunk_count": len(chunks),
        "avg_chunk_size": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
        "min_chunk_size": min(len(c) for c in chunks) if chunks else 0,
        "max_chunk_size": max(len(c) for c in chunks) if chunks else 0,
        "chunks": chunks
    }
    return stats


def main():
    # 测试文本：模拟简历内容
    test_text = """
    个人信息
    
    姓名：王鸿博
    年龄：28岁
    电话：138-0000-0000
    邮箱：wanghongbo@example.com
    
    教育背景
    
    清华大学 | 计算机科学与技术 | 硕士 | 2018-2021
    主修课程：数据结构、算法设计、机器学习、深度学习、自然语言处理
    GPA：3.8/4.0
    
    北京大学 | 软件工程 | 本科 | 2014-2018
    主修课程：Java程序设计、数据库系统、操作系统、计算机网络
    
    工作经历
    
    阿里巴巴 | 高级Java开发工程师 | 2021-至今
    负责淘宝推荐系统的架构设计与开发，使用Spring Boot、Redis、Kafka等技术栈。
    优化推荐算法，提升CTR 15%，日均处理请求量超过10亿次。
    带领5人团队完成微服务架构迁移，系统可用性从99.9%提升至99.99%。
    
    字节跳动 | Python开发工程师 | 2019-2021
    负责抖音内容审核系统的后端开发，使用Django、Celery、Elasticsearch。
    设计并实现分布式任务调度系统，支持每日千万级视频审核。
    优化数据库查询性能，响应时间从200ms降低至50ms。
    
    专业技能
    
    编程语言：Java、Python、Go、JavaScript
    框架：Spring Boot、Django、Flask、Vue.js
    数据库：MySQL、Redis、MongoDB、Elasticsearch
    中间件：Kafka、RabbitMQ、Nginx
    工具：Docker、Kubernetes、Jenkins、Git
    
    项目经验
    
    智能客服系统
    基于NLP技术构建企业级智能客服平台，支持多轮对话、意图识别、情感分析。
    使用BERT模型进行意图分类，准确率达到92%。
    系统日均处理对话超过50万次，用户满意度提升30%。
    
    数据分析平台
    构建实时数据分析平台，支持海量数据的可视化展示和智能分析。
    使用Flink进行实时计算，延迟控制在100ms以内。
    支持PB级数据存储，查询响应时间在秒级。
    """
    
    print("=" * 80)
    print("文档分块效果对比测试")
    print("=" * 80)
    print(f"原始文本长度: {len(test_text)} 字符\n")
    
    # 测试 RecursiveCharacterTextSplitter（旧配置）
    old_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n","\n",".",",","，","，","？","！","？","！"," ",""],
        length_function=len
    )
    old_stats = test_splitter(old_splitter, test_text, "RecursiveCharacterTextSplitter (旧配置)")
    
    # 测试 RecursiveCharacterTextSplitter（新配置）
    new_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n","\n", "。","？","！","；","...","..",".","?","!",";","，",","," ",""],
        length_function=len
    )
    new_stats = test_splitter(new_splitter, test_text, "RecursiveCharacterTextSplitter (新配置)")
    
    # 测试 SemanticSplitter
    semantic_splitter = SemanticSplitter(chunk_size=500, chunk_overlap=50)
    semantic_stats = test_splitter(semantic_splitter, test_text, "SemanticSplitter")
    
    # 打印对比结果
    print("\n" + "=" * 80)
    print("分块效果对比")
    print("=" * 80)
    
    for stats in [old_stats, new_stats, semantic_stats]:
        print(f"\n【{stats['splitter']}】")
        print(f"  分块数量: {stats['chunk_count']}")
        print(f"  平均块大小: {stats['avg_chunk_size']:.1f} 字符")
        print(f"  最小块: {stats['min_chunk_size']} 字符")
        print(f"  最大块: {stats['max_chunk_size']} 字符")
        
        # 检查是否有句子被切断（简单检查：块末尾是否有结束标点）
        cut_count = 0
        for i, chunk in enumerate(stats['chunks']):
            if i < len(stats['chunks']) - 1:  # 不是最后一块
                last_char = chunk.strip()[-1] if chunk.strip() else ""
                if last_char not in "。！？.?!；;":
                    cut_count += 1
        print(f"  句子被切断数: {cut_count}")
    
    # 打印 SemanticSplitter 的分块详情
    print("\n" + "=" * 80)
    print("SemanticSplitter 分块详情")
    print("=" * 80)
    for i, chunk in enumerate(semantic_stats['chunks']):
        print(f"\n--- 块 {i+1} (长度: {len(chunk)}) ---")
        preview = chunk.replace('\n', ' ')[:100]
        print(f"{preview}...")
    
    # 保存结果
    result = {
        "test_time": "2026-05-17",
        "original_text_length": len(test_text),
        "results": [
            {
                "splitter": old_stats["splitter"],
                "chunk_count": old_stats["chunk_count"],
                "avg_chunk_size": old_stats["avg_chunk_size"],
                "min_chunk_size": old_stats["min_chunk_size"],
                "max_chunk_size": old_stats["max_chunk_size"]
            },
            {
                "splitter": new_stats["splitter"],
                "chunk_count": new_stats["chunk_count"],
                "avg_chunk_size": new_stats["avg_chunk_size"],
                "min_chunk_size": new_stats["min_chunk_size"],
                "max_chunk_size": new_stats["max_chunk_size"]
            },
            {
                "splitter": semantic_stats["splitter"],
                "chunk_count": semantic_stats["chunk_count"],
                "avg_chunk_size": semantic_stats["avg_chunk_size"],
                "min_chunk_size": semantic_stats["min_chunk_size"],
                "max_chunk_size": semantic_stats["max_chunk_size"]
            }
        ]
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "chunking_test_result.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] 测试结果已保存: {output_path}")


if __name__ == "__main__":
    main()
