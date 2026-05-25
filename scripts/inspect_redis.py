#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 Redis 中存储的历史记录格式"""

import redis
import json

r = redis.Redis(host='192.168.211.133', port=6379, decode_responses=True)

keys = r.keys('chat_history:*')
print(f'找到 {len(keys)} 个 chat_history key\n')

for key in keys:
    msgs = r.lrange(key, 0, -1)
    print(f'Key: {key}')
    print(f'消息数量: {len(msgs)}')
    
    for i, msg in enumerate(msgs):
        try:
            data = json.loads(msg)
            role = data.get('role', 'unknown')
            content = data.get('content', '')[:80]
            print(f'  {i+1}. [{role}] {content}...')
        except Exception as e:
            print(f'  {i+1}. [ERROR] {e}: {msg[:100]}')
    
    print()
