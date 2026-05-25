import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import faulthandler
faulthandler.enable()

import os.path

from app.RAG import config_data as config
import hashlib
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime

# 尝试导入语义分块器，失败则回退到 RecursiveCharacterTextSplitter
try:
    from app.RAG.semantic_splitter import SemanticSplitter
    USE_SEMANTIC_SPLITTER = True
except ImportError:
    USE_SEMANTIC_SPLITTER = False

# 关键词召回
from app.RAG.retrievers.keyword_retriever import KeywordRetriever, HybridRetriever


def check_md5(md5_str: str):
    # 检查传入的md5字符串是否被处理过
    # return False(未被处理过）  |  True（已被处理，有记录）
    if not os.path.exists(config.md5_path):
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip()  # 处理字符串前后的空格和回车
            if line == md5_str:
                return True  # 已处理过
        return False


def save_md5(md5_str: str):
    # 记录传入的md5字符串
    with open(config.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')


def get_string_md5(input_str: str, encoding='utf-8'):
    # 将字符串转换为md5字符串

    # 将字符串转换为bytes字节数组
    str_bytes = input_str.encode(encoding=encoding)

    # 创建md5对象
    md5_obj = hashlib.md5()  # 得到md5对象
    md5_obj.update(str_bytes)  # 更新内容
    md5_hex = md5_obj.hexdigest()  # 得到md5的十六进制字符串
    return md5_hex


class KnowledgeBaseService(object):
    def __init__(self):
        self.embedding = DashScopeEmbeddings(model="text-embedding-v4")
        # 优先使用语义分块器，回退到 RecursiveCharacterTextSplitter
        if USE_SEMANTIC_SPLITTER:
            self.spliter = SemanticSplitter(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap
            )
        else:
            self.spliter = RecursiveCharacterTextSplitter(
                chunk_size=config.chunk_size,  # 分割后的文本块最大长度
                chunk_overlap=config.chunk_overlap,  # 连续的文本块运行的重叠数量
                separators=config.separators,  # 自然段落划分的符号
                length_function=len,  # 使用Python自动的
            )  # 文本分割器对象

        # FAISS：尝试加载已有索引，不存在则延迟初始化（避免启动时调用 embedding API）
        os.makedirs(config.faiss_index_path, exist_ok=True)
        index_file = os.path.join(config.faiss_index_path, "index.faiss")
        if os.path.exists(index_file):
            # 加载已有 FAISS 索引
            self.faiss = FAISS.load_local(
                config.faiss_index_path,
                self.embedding,
                allow_dangerous_deserialization=True
            )
        else:
            # 延迟初始化：没有索引时先设为 None，等第一次 add_texts 时再创建
            self.faiss = None
        
        # 初始化关键词检索器
        self.keyword_index_path = os.path.join(config.faiss_index_path, "bm25_index.pkl")
        self.keyword_retriever = KeywordRetriever(index_path=self.keyword_index_path)
        
        # 如果 FAISS 有数据但 BM25 没有，自动构建
        if self.faiss is not None and len(self.keyword_retriever.documents) == 0:
            self._rebuild_keyword_index()
        
        # 混合检索器（懒加载，需要时创建）
        self._hybrid_retriever = None

    def _rebuild_keyword_index(self):
        """从 FAISS 重建关键词索引"""
        if self.faiss is None:
            return
        
        try:
            docs = []
            ids = []
            # 从 FAISS docstore 提取文档
            if hasattr(self.faiss, 'docstore') and hasattr(self.faiss.docstore, '_dict'):
                for doc_id in self.faiss.docstore._dict:
                    doc = self.faiss.docstore._dict[doc_id]
                    docs.append(doc.page_content)
                    ids.append(str(doc_id))
            
            if docs:
                self.keyword_retriever.add_documents(docs, ids)
                print(f"[Keyword Index] Rebuilt with {len(docs)} documents")
        except Exception as e:
            print(f"[Keyword Index] Rebuild failed: {e}")

    def upload_by_str(self, data: str, filename):
        # 将传入的字符串，进行向量化，存入向量数据库中
        # 先得到传入字符串的md5值

        md5_hex = get_string_md5(data)
        if check_md5(md5_hex):
            return "[跳过]内容已存在"

        if len(data) > config.max_split_char_number:
            knowledge_chunks = self.spliter.split_text(data)
        else:
            knowledge_chunks = [data]

        metadata = {
            "source": filename,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "jjj"
        }

        # FAISS 延迟初始化：第一次添加文本时创建索引
        if self.faiss is None:
            self.faiss = FAISS.from_texts(knowledge_chunks, self.embedding, metadatas=[metadata for _ in knowledge_chunks])
        else:
            self.faiss.add_texts(knowledge_chunks, metadatas=[metadata for _ in knowledge_chunks])
        
        # FAISS 需要显式保存索引
        self.faiss.save_local(config.faiss_index_path)
        
        # 同步更新关键词索引
        doc_ids = [f"{filename}_{i}" for i in range(len(knowledge_chunks))]
        self.keyword_retriever.add_documents(knowledge_chunks, doc_ids)

        save_md5(md5_hex)
        return "[成功]内容已载入向量库"
    
    def search(self, query: str, k: int = 3) -> list:
        """
        混合检索：向量召回 + 关键词召回 + RRF 融合
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            文档列表
        """
        if self._hybrid_retriever is None:
            self._hybrid_retriever = HybridRetriever(
                vector_store=self.faiss,
                keyword_retriever=self.keyword_retriever
            )
        
        results = self._hybrid_retriever.retrieve(
            query=query,
            vector_k=10,
            keyword_k=10,
            final_k=k
        )
        
        # 转换为 LangChain Document 格式
        try:
            from langchain.schema import Document
        except ImportError:
            from langchain_core.documents import Document
        documents = []
        for content, score in results:
            documents.append(Document(
                page_content=content,
                metadata={"score": score, "retriever": "hybrid"}
            ))
        
        return documents
