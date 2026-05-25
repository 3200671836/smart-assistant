with open('redis_cache.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """获取对话历史"""
        if not self.is_available():
            return []
        try:
            key = f"chat_history:{session_id}"
            messages = self.client.lrange(key, 0, limit - 1)
            return [json.loads(m) for m in messages]
        except Exception:
            return []'''

new = '''    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """获取对话历史，按时间顺序返回（最早的在前）"""
        if not self.is_available():
            return []
        try:
            key = f"chat_history:{session_id}"
            # LRANGE 返回的是从 newest 到 oldest（因为 LPUSH）
            # 需要反转以获得 chronological order
            messages = self.client.lrange(key, 0, limit - 1)
            parsed = [json.loads(m) for m in messages]
            return list(reversed(parsed))  # 反转回时间顺序
        except Exception:
            return []'''

if old in content:
    content = content.replace(old, new)
    with open('redis_cache.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: fixed get_chat_history order')
else:
    print('Pattern not found')
