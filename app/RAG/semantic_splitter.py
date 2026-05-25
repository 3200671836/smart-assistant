"""
语义分块器 - 基于句子边界和主题连贯性的智能分块

相比 RecursiveCharacterTextSplitter，本实现：
1. 优先按段落分割（保持主题完整性）
2. 段落过长时按句子分割（保持语义连贯）
3. 避免在句子中间切断
4. 支持中文和英文句子边界检测
"""

import re
from typing import List


class SemanticSplitter:
    """语义分块器"""
    
    # 句子结束标点（中文+英文）
    SENTENCE_ENDINGS = r'[。！？.?!；;]'
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def split_text(self, text: str) -> List[str]:
        """
        按语义分块文本
        
        策略：
        1. 先按段落分割
        2. 段落过长时按句子分割
        3. 句子仍过长时按字符分割（最后手段）
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        # 第一步：按段落分割
        paragraphs = self._split_by_paragraphs(text)
        
        # 第二步：处理过长的段落
        chunks = []
        for para in paragraphs:
            if len(para) <= self.chunk_size:
                chunks.append(para)
            else:
                # 段落过长，按句子分割
                sentence_chunks = self._split_by_sentences(para)
                chunks.extend(sentence_chunks)
        
        # 第三步：合并小块（如果相邻块总长度不超过 chunk_size）
        chunks = self._merge_small_chunks(chunks)
        
        return chunks
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割（双换行符）"""
        # 标准化换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # 按双换行分割
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        return paragraphs
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """按句子分割，保持句子完整性"""
        # 使用正则表达式匹配句子结束位置
        sentences = re.split(f'({self.SENTENCE_ENDINGS})', text)
        
        # 重新组合句子和结束标点
        combined = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and re.match(self.SENTENCE_ENDINGS, sentences[i + 1]):
                combined.append(sentences[i] + sentences[i + 1])
                i += 2
            else:
                if sentences[i].strip():
                    combined.append(sentences[i])
                i += 1
        
        # 合并句子成块
        chunks = []
        current_chunk = ""
        
        for sentence in combined:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果单个句子就超过 chunk_size，强制分割
            if len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                # 强制按字符分割长句子
                for i in range(0, len(sentence), self.chunk_size):
                    chunks.append(sentence[i:i + self.chunk_size])
                continue
            
            # 尝试添加到当前块
            if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                # 当前块已满，保存并开始新块
                if current_chunk:
                    chunks.append(current_chunk)
                # 新块包含上一块的结尾（重叠）
                current_chunk = sentence
        
        # 保存最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """合并过小的相邻块"""
        if not chunks:
            return chunks
        
        merged = []
        current = chunks[0]
        
        for chunk in chunks[1:]:
            # 如果合并后不超过 chunk_size，则合并
            if len(current) + len(chunk) + 1 <= self.chunk_size:
                current += "\n\n" + chunk
            else:
                merged.append(current)
                current = chunk
        
        merged.append(current)
        return merged


# 兼容 LangChain 接口的包装器
class LangChainCompatibleSplitter:
    """兼容 LangChain 接口的语义分块器"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, **kwargs):
        self.splitter = SemanticSplitter(chunk_size, chunk_overlap)
    
    def split_text(self, text: str) -> List[str]:
        return self.splitter.split_text(text)
    
    def split_documents(self, documents):
        """兼容 LangChain Document 对象"""
        from langchain.schema import Document
        result = []
        for doc in documents:
            chunks = self.split_text(doc.page_content)
            for chunk in chunks:
                result.append(Document(page_content=chunk, metadata=doc.metadata))
        return result


if __name__ == "__main__":
    # 测试
    test_text = """
    王鸿博是一名优秀的Python开发工程师。他拥有5年的开发经验。

    在技术方面，他精通Python、Java和Go语言。他熟悉Django、Flask等Web框架。
    此外，他还具备丰富的人工智能和机器学习经验。

    在工作中，王鸿博负责过多个大型项目的架构设计。他善于团队协作，能够带领团队高效完成任务。
    他的代码质量很高，注重代码的可读性和可维护性。

    教育背景方面，王鸿博毕业于清华大学计算机科学与技术专业。他在校期间成绩优异，多次获得奖学金。
    """
    
    splitter = SemanticSplitter(chunk_size=100, chunk_overlap=20)
    chunks = splitter.split_text(test_text)
    
    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\n--- 块 {i+1} (长度: {len(chunk)}) ---")
        print(chunk[:100] + "..." if len(chunk) > 100 else chunk)
