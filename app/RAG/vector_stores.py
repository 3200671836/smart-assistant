import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import faulthandler
faulthandler.enable()

from langchain_community.vectorstores import FAISS
from app.RAG import config_data as config


class VectorStoreService(object):

    def __init__(self, embedding):
        self.embedding = embedding
        # FAISS：加载已有索引，不存在则报错（需先运行 knowledge_base 入库）
        index_file = os.path.join(config.faiss_index_path, "index.faiss")
        if os.path.exists(index_file):
            self.vector_store = FAISS.load_local(
                config.faiss_index_path,
                self.embedding,
                allow_dangerous_deserialization=True
            )
        else:
            # 没有索引文件，创建空索引避免报错
            self.vector_store = FAISS.from_texts([""], self.embedding)
        
        # 初始化 KnowledgeBaseService 用于混合检索
        self.kb = None
        try:
            from app.RAG.knowledge_base import KnowledgeBaseService
            self.kb = KnowledgeBaseService()
        except Exception as e:
            print(f"[VectorStoreService] KnowledgeBaseService init failed: {e}")

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": config.similarity_threshold})


if __name__ == '__main__':
    from langchain_community.embeddings import DashScopeEmbeddings
    retriever = VectorStoreService(DashScopeEmbeddings(model="text-embedding-v4")).get_retriever()
    res = retriever.invoke("我想买一部玩游戏好的手机，有什么推荐吗")
    print(res)