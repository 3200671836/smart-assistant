"""
测试关键词召回功能
"""
import sys
sys.path.insert(0, "D:\\develop\\smart-assistant\\backend")

from app.RAG.retrievers.keyword_retriever import KeywordRetriever


def test_basic():
    """基础测试"""
    print("=" * 50)
    print("测试1: 基础关键词召回")
    print("=" * 50)
    
    retriever = KeywordRetriever()
    
    # 添加测试文档
    docs = [
        "何杰是一名Java开发工程师，熟悉Spring Boot和MySQL数据库",
        "张三擅长Python和机器学习，有3年深度学习经验",
        "李四精通前端开发，熟悉Vue、React和TypeScript",
        "王五是一名全栈工程师，掌握Java、Python和JavaScript",
        "何杰还熟悉Redis缓存和消息队列Kafka的使用",
    ]
    doc_ids = ["doc_1", "doc_2", "doc_3", "doc_4", "doc_5"]
    
    retriever.add_documents(docs, doc_ids)
    
    # 测试查询
    queries = [
        "何杰会什么技术",
        "Java开发",
        "Redis缓存",
        "机器学习",
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        results = retriever.search(query, k=3)
        for doc_id, content, score in results:
            print(f"  [{doc_id}] score={score:.4f}: {content[:50]}...")


def test_hybrid():
    """测试混合检索"""
    print("\n" + "=" * 50)
    print("测试2: 混合检索（向量 + 关键词）")
    print("=" * 50)
    
    try:
        from app.RAG.knowledge_base import KnowledgeBaseService
        
        kb = KnowledgeBaseService()
        
        # 测试查询
        queries = [
            "何杰的技术栈",
            "Java开发经验",
            "项目经历",
        ]
        
        for query in queries:
            print(f"\n查询: {query}")
            results = kb.search(query, k=3)
            for i, doc in enumerate(results):
                content = doc.page_content[:80].encode('ascii', 'ignore').decode('ascii')
                print(f"  [{i+1}] score={doc.metadata.get('score', 0):.4f}: {content}...")
                print(f"      source: {doc.metadata.get('retriever', 'unknown')}")
    
    except Exception as e:
        print(f"混合检索测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_basic()
    test_hybrid()
