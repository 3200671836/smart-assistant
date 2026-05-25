#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 /history API 返回的数据格式"""

import requests

res = requests.get('http://127.0.0.1:8001/api/history?limit=2')
print('Status:', res.status_code)

if res.status_code == 200:
    data = res.json()
    print(f'Total: {data.get("total")}')
    print(f'Items count: {len(data.get("items", []))}\n')
    
    for i, item in enumerate(data.get('items', [])[:2]):
        print(f'--- 记录 {i+1} ---')
        print(f'  id: {item.get("id")}')
        print(f'  input_summary: {item.get("input_summary", "")[:40]}')
        print(f'  created_at: {item.get("created_at")}')
        print(f'  has result_json: {"result_json" in item}')
        print(f'  has result_text: {"result_text" in item}')
        print()
