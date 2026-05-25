#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 Redis 中存储的数据"""

import redis
import json

r = redis.Redis(host='192.168.211.133', port=6379, decode_responses=True)

# 检查所有 chat_history 相关的 key
keys = r.keys('chat_history:*')
print(f'找到 {len(keys)} 个 chat_history key')

for key in keys:
    msgs = r.lrange(key, 0, -1)
    print(f'\nKey: {key}')
    print(f'消息数量: {len(msgs)}')
    for i, msg in enumerate(msgs[:3]):
        data = json.loads(msg)
        print(f'  {i+1}. [{data["role"]}] {data["content"][:60]}...')
    if len(msgs) > 3:
        print(f'  ... 还有 {len(msgs)-3} 条')

# 检查响应缓存
print('\n=== 响应缓存 ===')
cache_keys = r.keys('response_cache:*')
print(f'找到 {len(cache_keys)} 个缓存 key')
