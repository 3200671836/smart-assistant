"""
关键词召回模块 - 基于 BM25 算法
用于精确匹配专业术语、人名、技术栈等
"""

import os
import json
import pickle
import jieba
import numpy as np
from typing import List, Tuple, Optional
from rank_bm25 import BM25Okapi


class KeywordRetriever:
    """BM25 关键词检索器"""
    
    def __init__(self, index_path: Optional[str] = None):
        """
        Args:
            index_path: BM25 索引保存路径，None 时不持久化
        """
        self.index_path = index_path
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self.bm25: Optional[BM25Okapi] = None
        self._tokenized_docs: List[List[str]] = []
        
        if index_path and os.path.exists(index_path):
            self._load_index()
    
    def _tokenize(self, text: str) -> List[str]:
        """中文分词"""
        # 使用 jieba 分词，保留长度大于1的词
        words = jieba.lcut(text)
        return [w.strip().lower() for w in words if len(w.strip()) > 1]
    
    def add_documents(self, documents: List[str], doc_ids: Optional[List[str]] = None):
        """
        添加文档到索引
        
        Args:
            documents: 文档内容列表
            doc_ids: 文档 ID 列表，None 时使用索引作为 ID
        """
        if doc_ids is None:
            doc_ids = [str(i) for i in range(len(documents))]
        
        self.documents.extend(documents)
        self.doc_ids.extend(doc_ids)
        
        # 重新构建索引
        self._rebuild_index()
        
        if self.index_path:
            self._save_index()
    
    def _rebuild_index(self):
        """重建 BM25 索引"""
        self._tokenized_docs = [self._tokenize(doc) for doc in self.documents]
        if len(self._tokenized_docs) > 0:
            self.bm25 = BM25Okapi(self._tokenized_docs)
        else:
            self.bm25 = None
    
    def search(self, query: str, k: int = 10) -> List[Tuple[str, str, float]]:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            [(doc_id, doc_content, score), ...]
        """
        if self.bm25 is None or len(self.documents) == 0:
            return []
        
        tokenized_query = self._tokenize(query)
        if len(tokenized_query) == 0:
            return []
        
        scores = self.bm25.get_scores(tokenized_query)
        
        # 获取 top-k 索引
        top_indices = np.argsort(scores)[-k:][::-1]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # 只返回有分数的结果
                results.append((
                    self.doc_ids[idx],
                    self.documents[idx],
                    float(scores[idx])
                ))
        
        return results
    
    def _save_index(self):
        """保存索引到磁盘"""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        data = {
            'documents': self.documents,
            'doc_ids': self.doc_ids,
            'tokenized_docs': self._tokenized_docs
        }
        with open(self.index_path, 'wb') as f:
            pickle.dump(data, f)
    
    def _load_index(self):
        """从磁盘加载索引"""
        with open(self.index_path, 'rb') as f:
            data = pickle.load(f)
        self.documents = data['documents']
        self.doc_ids = data['doc_ids']
        self._tokenized_docs = data['tokenized_docs']
        if len(self._tokenized_docs) > 0:
            self.bm25 = BM25Okapi(self._tokenized_docs)


class HybridRetriever:
    """混合检索器：向量召回 + 关键词召回"""
    
    def __init__(self, vector_store, keyword_retriever: KeywordRetriever):
        """
        Args:
            vector_store: FAISS 向量存储实例
            keyword_retriever: BM25 关键词检索器实例
        """
        self.vector_store = vector_store
        self.keyword = keyword_retriever
    
    def retrieve(
        self, 
        query: str, 
        vector_k: int = 10,
        keyword_k: int = 10,
        final_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        多路召回并融合
        
        Args:
            query: 查询文本
            vector_k: 向量召回数量
            keyword_k: 关键词召回数量
            final_k: 最终返回数量
            
        Returns:
            [(doc_content, fused_score), ...]
        """
        # 1. 向量召回
        vector_results = []
        if self.vector_store:
            try:
                docs = self.vector_store.similarity_search(query, k=vector_k)
                vector_results = [(doc.page_content, 1.0 / (i + 1)) 
                                  for i, doc in enumerate(docs)]
            except Exception as e:
                print(f"[Vector retrieval error] {e}")
        
        # 2. 关键词召回
        keyword_results = []
        kw_results = self.keyword.search(query, k=keyword_k)
        for rank, (doc_id, doc_content, score) in enumerate(kw_results):
            keyword_results.append((doc_content, 1.0 / (rank + 1)))
        
        # 3. RRF 融合
        fused = self._rrf_fuse(vector_results, keyword_results)
        
        return fused[:final_k]
    
    def _rrf_fuse(
        self, 
        vector_results: List[Tuple[str, float]], 
        keyword_results: List[Tuple[str, float]],
        k: int = 60
    ) -> List[Tuple[str, float]]:
        """
        Reciprocal Rank Fusion
        
        Args:
            vector_results: [(doc, rank_score), ...]
            keyword_results: [(doc, rank_score), ...]
            k: RRF 常数，默认 60
        """
        from collections import defaultdict
        
        scores = defaultdict(float)
        
        # 向量召回分数
        for rank, (doc, _) in enumerate(vector_results):
            scores[doc] += 1.0 / (k + rank + 1)
        
        # 关键词召回分数
        for rank, (doc, _) in enumerate(keyword_results):
            scores[doc] += 1.0 / (k + rank + 1)
        
        # 排序返回
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results


# ========== 便捷函数 ==========

def create_keyword_index_from_faiss(
    faiss_store, 
    save_path: Optional[str] = None
) -> KeywordRetriever:
    """
    从 FAISS 存储创建 BM25 索引
    
    Args:
        faiss_store: FAISS 向量存储
        save_path: 索引保存路径
        
    Returns:
        KeywordRetriever 实例
    """
    retriever = KeywordRetriever(index_path=save_path)
    
    # 从 FAISS 中提取文档
    if hasattr(faiss_store, 'docstore'):
        docs = []
        ids = []
        for doc_id in faiss_store.docstore._dict:
            doc = faiss_store.docstore._dict[doc_id]
            docs.append(doc.page_content)
            ids.append(str(doc_id))
        
        retriever.add_documents(docs, ids)
        print(f"[Keyword Index] Built from {len(docs)} documents")
    
    return retriever


# 单例模式
_keyword_retriever: Optional[KeywordRetriever] = None

def get_keyword_retriever(index_path: Optional[str] = None) -> KeywordRetriever:
    """获取关键词检索器单例"""
    global _keyword_retriever
    if _keyword_retriever is None:
        _keyword_retriever = KeywordRetriever(index_path=index_path)
    return _keyword_retriever
