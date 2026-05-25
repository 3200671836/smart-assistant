#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证历史记录顺序"""

import sys
sys.path.insert(0, 'D:\\develop\\smart-assistant\\backend')

from app.RAG.history_store_factory import get_history_store

store = get_history_store(use_redis=True)

print('=== 从 Redis 获取历史（应该按时间顺序）===')
history = store.get_history(limit=5)
for i, msg in enumerate(history):
    role = msg['role']
    content = msg['content'][:60]
    print(f'{i+1}. [{role}] {content}...')
