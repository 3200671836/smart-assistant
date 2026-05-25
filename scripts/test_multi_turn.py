"""
多轮对话测试脚本
测试对话历史是否正确保存和加载
"""

import sys
sys.path.insert(0, "D:\\develop\\smart-assistant\\backend")

from app.RAG.rag import RagService

def test_multi_turn():
    """测试多轮对话"""
    print("="*50)
    print("多轮对话测试")
    print("="*50)
    
    # 创建服务实例（使用默认 session_id）
    rag = RagService()
    
    # 测试对话
    conversations = [
        "你好，我是新来的实习生",
        "我想了解一下公司的技术栈",
        "后端主要用什么语言？",
        "数据库方面呢？",
        "有使用缓存吗？",
    ]
    
    for i, user_input in enumerate(conversations, 1):
        print(f"\n--- 第 {i} 轮 ---")
        print(f"用户: {user_input}")
        
        # 使用非流式接口
        result = rag.chat(user_input)
        print(f"助手: {result['response'][:100]}...")
        
        # 检查历史记录
        history = rag.history_store.get_history(limit=10)
        print(f"历史记录数: {len(history)}")
        
        if history:
            last_msg = history[-1]
            print(f"最后一条: {last_msg['role']} - {last_msg['content'][:50]}...")
    
    print("\n" + "="*50)
    print("测试完成！")
    print("="*50)
    
    # 打印完整历史
    print("\n完整历史记录:")
    history = rag.history_store.get_history(limit=10)
    for msg in history:
        role = "用户" if msg['role'] == 'user' else "助手"
        print(f"  {role}: {msg['content'][:80]}...")

if __name__ == "__main__":
    test_multi_turn()
