#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查数据库中的历史记录"""

import sys
sys.path.insert(0, 'D:\\develop\\smart-assistant\\backend')

from app.db.models import SessionLocal
from app.db.models import HistoryRecord

db = SessionLocal()
records = db.query(HistoryRecord).order_by(HistoryRecord.created_at.desc()).limit(10).all()

print(f'数据库中有 {db.query(HistoryRecord).count()} 条历史记录')
print(f'最近 {len(records)} 条:\n')

for r in records:
    print(f'{r.id}. [{r.tool_name}]')
    print(f'   输入: {r.input_summary[:60] if r.input_summary else "无"}')
    text = r.result_text or "无"
    print(f'   结果: {text[:80]}')
    print()
