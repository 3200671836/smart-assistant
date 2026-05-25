import sys
sys.path.insert(0, 'D:\\develop\\smart-assistant\\backend')

with open('app/RAG/rag.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查 _get_history_str 方法是否需要添加压缩
if 'compress_for_prompt' not in content:
    print('Need to add compression to _get_history_str')
    
    # 找到 _get_history_str 方法并修改
    old_method = '''    def _get_history_str(self):
        """获取格式化的历史对话"""
        history = self.history_store.get_history(limit=10)
        if not history:
            return "无历史对话"
        
        history_str = ""
        for msg in history:
            if msg["role"] == "user":
                history_str += f"用户：{msg['content']}\n"
            else:
                history_str += f"助手：{msg['content']}\n"
        return history_str'''
    
    new_method = '''    def _get_history_str(self):
        """获取格式化的历史对话（支持Token压缩）"""
        history = self.history_store.get_history(limit=10)
        if not history:
            return "无历史对话"
        
        history_str = ""
        for msg in history:
            if msg["role"] == "user":
                history_str += f"用户：{msg['content']}\n"
            else:
                history_str += f"助手：{msg['content']}\n"
        
        # Token 压缩
        compressor = get_compressor()
        return compressor.compress_for_prompt(history_str, "", max_history_tokens=2000)'''
    
    content = content.replace(old_method, new_method)
    
    with open('app/RAG/rag.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('Updated _get_history_str with compression')
else:
    print('Compression already added')
