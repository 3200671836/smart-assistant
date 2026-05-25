#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 /history API 返回的数据格式"""

import requests

# 测试 /history/chat API（前端实际使用的接口）
res = requests.get('http://127.0.0.1:8001/api/history/chat?limit=2')
print('URL: /api/history/chat')
print('Status:', res.status_code)

if res.status_code == 200:
    data = res.json()
    print('Items count:', len(data))
    
    if data:
        item = data[0]
        print('\n第一条记录:')
        print('  id:', item.get('id'))
        print('  tool_name:', item.get('tool_name'))
        print('  input_summary:', (item.get('input_summary') or '')[:50])
        print('  result_json:', item.get('result_json'))
        print('  result_text:', (item.get('result_text') or '')[:50])
        print('  has result_json:', 'result_json' in item)
        print('  has result_text:', 'result_text' in item)
else:
    print('Error:', res.text[:200])
