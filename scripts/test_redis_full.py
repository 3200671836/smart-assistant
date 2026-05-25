#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 Redis 完整功能"""

import sys
sys.path.insert(0, 'D:\\develop\\smart-assistant\\backend')

from app.RAG.rag import RagService

def test_redis():
    r = RagService()
    
    # 测试非流式对话
    print('=== 测试非流式 ===')
    response = r.chat('你好，请介绍一下你自己')
    print('Response:', str(response)[:100] if response else 'None')
    
    history = r.history_store.get_history()
    print('History count:', len(history))
    
    # 测试流式对话
    print('\n=== 测试流式 ===')
    chunks = []
    for chunk in r.chat_stream('今天天气怎么样'):
        chunks.append(chunk)
    
    print('Chunks count:', len(chunks))
    
    history = r.history_store.get_history()
    print('History count after stream:', len(history))
    
    # 查看历史
    print('\n=== 历史记录 ===')
    for msg in history:
        print(f"{msg['role']}: {msg['content'][:80]}...")
    
    print('\n=== Redis 测试完成 ===')

if __name__ == '__main__':
    test_redis()
