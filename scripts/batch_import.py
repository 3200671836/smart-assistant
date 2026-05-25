"""
批量导入测试简历到向量库
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.RAG.knowledge_base import KnowledgeBaseService


def import_resumes(resume_dir: str):
    """批量导入简历"""
    kb = KnowledgeBaseService()
    
    # 获取所有简历文件
    files = [f for f in os.listdir(resume_dir) if f.endswith('.txt')]
    files.sort()
    
    print(f"发现 {len(files)} 份简历，开始导入...")
    
    success = 0
    failed = 0
    
    for i, filename in enumerate(files, 1):
        filepath = os.path.join(resume_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加到知识库
            kb.upload_by_str(content, filename)
            
            success += 1
            print(f"OK [{i}/{len(files)}] {filename} - 导入成功")
            
        except Exception as e:
            failed += 1
            print(f"FAIL [{i}/{len(files)}] {filename} - 导入失败: {e}")
    
    print(f"\n导入完成!")
    print(f"成功: {success}")
    print(f"失败: {failed}")
    print(f"总计: {len(files)}")


if __name__ == "__main__":
    resume_dir = os.path.join(os.path.dirname(__file__), "..", "test_data", "resumes")
    import_resumes(resume_dir)
