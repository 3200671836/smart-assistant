from app.RAG.token_compressor import get_compressor
import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import faulthandler
faulthandler.enable()

from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from app.RAG import config_data as config
from langchain_community.embeddings import DashScopeEmbeddings
from app.RAG.vector_stores import VectorStoreService
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
from app.RAG.history_store_factory import get_history_store
from app.core.redis_cache import get_cache

def print_prompt(prompt):
    try:
        print("="*20)
        print(prompt.to_string())
        print("="*20)
        print("="*20)
    except UnicodeEncodeError:
        pass
    return prompt

class RagService(object):
    def __init__(self, history_file: str = "./chat_history.json"):
        self.vector_service = VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model_name),
        )
        
        # 初始化历史记录存储（Redis + 数据库混合存储）
        self.history_store = get_history_store(use_redis=True)
        
        # 初始化 Redis 缓存
        self.cache = get_cache()

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "以我提供的参考资料为主,简洁和专业的回答用户问题。\n"
                           "历史对话记录：{history}\n"
                           "参考资料：{context}。"),
                ("user", "{input}")
            ]
        )

        self.chat_model = ChatTongyi(model=config.chat_model_name)

        self.chain = self.__get_chain()

    def _get_history_str(self, use_compression: bool = True):
        """获取格式化后的历史对话，支持Token压缩"""
        history = self.history_store.get_history(limit=10)
        if not history:
            return "无历史对话"
        
        # 使用 TokenCompressor 压缩历史
        if use_compression:
            try:
                from app.RAG.token_compressor import get_compressor
                compressor = get_compressor()
                
                # 转换为压缩器需要的格式
                messages = []
                for msg in history:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
                
                # 压缩历史
                compressed = compressor.compress_history(messages, keep_first=1, keep_last=5)
                
                # 转换回字符串格式
                history_str = ""
                for msg in compressed:
                    if msg.get("is_summary"):
                        history_str += f"[摘要] {msg['content']}\n"
                    elif msg["role"] == "user":
                        history_str += f"用户：{msg['content']}\n"
                    else:
                        history_str += f"助手：{msg['content']}\n"
                return history_str
            except Exception as e:
                print(f"[RagService] Token compression failed: {e}")
                # 降级：返回原始历史
                pass
        
        # 原始历史（不压缩或压缩失败）
        history_str = ""
        for msg in history:
            if msg["role"] == "user":
                history_str += f"用户：{msg['content']}\n"
            else:
                history_str += f"助手：{msg['content']}\n"
        return history_str

    def __get_chain(self):
        retriever = self.vector_service.get_retriever()
        
        def format_dacument(docs: list[Document]):
            if not docs:
                return "无相关参考资料"

            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段：{doc.page_content}\n文档元数据：{doc.metadata}\n\n"
            return formatted_str
        
        def get_history_str():
            """获取格式化后的历史对话（用于链式调用）"""
            return self._get_history_str(use_compression=True)

        chain = (
            {
                "input": RunnablePassthrough(),
                "context": retriever | RunnableLambda(format_dacument),
                "history": RunnableLambda(lambda x: get_history_str())
            } | self.prompt_template | RunnableLambda(print_prompt) | self.chat_model | StrOutputParser()
        )

        return chain
    
    def _get_cached_response(self, query: str) -> dict:
        """从 Redis 缓存获取响应"""
        cache_key = f"response:{hash(query) & 0xFFFFFFFF}"
        cached = self.cache.get(cache_key)
        if cached:
            try:
                import json
                data = json.loads(cached) if isinstance(cached, str) else cached
                print(f"[Redis] Cache hit: {query[:30]}...")
                return data
            except Exception:
                return None
        return None
    
    def _cache_response(self, query: str, response: dict, ttl: int = 3600):
        """缓存响应到 Redis"""
        import json
        cache_key = f"response:{hash(query) & 0xFFFFFFFF}"
        try:
            self.cache.set(cache_key, json.dumps(response, ensure_ascii=False), ttl=ttl)
        except Exception:
            pass
    
    def _build_prompt(self, user_input: str, retrieved_docs: list) -> str:
        """统一构建 Prompt（chat 和 chat_stream 共用）"""
        context_with_refs = ""
        for i, doc in enumerate(retrieved_docs):
            context_with_refs += f"[{i+1}] {doc.page_content}\n来源：{doc.metadata.get('source', '未知')}\n\n"
        
        history_str = self._get_history_str()
        
        return f"""以我提供的参考资料为主，简洁和专业的回答用户问题。
历史对话记录：{history_str}
参考资料：
{context_with_refs}

要求：
- 回答要准确，优先使用参考资料
- 关键事实后标注引用，如"根据文档[1]..."
- 如果参考资料不足，明确说明

用户问题：{user_input}"""
    
    def _build_sources(self, retrieved_docs: list) -> list:
        """构建引用信息"""
        sources = []
        for i, doc in enumerate(retrieved_docs):
            sources.append({
                "id": i + 1,
                "doc": doc.metadata.get('source', '未知'),
                "text": doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
            })
        return sources

    def chat_stream(self, user_input: str):
        """流式对话接口，带引用溯源"""

        # 保存用户消息
        self.history_store.add_message("user", user_input)
        
        # 1. 先检索相关文档（用于引用溯源）
        # 优先使用混合检索（向量 + 关键词）
        if hasattr(self.vector_service, 'kb') and self.vector_service.kb:
            retrieved_docs = self.vector_service.kb.search(user_input, k=3)
        else:
            retriever = self.vector_service.get_retriever()
            retrieved_docs = retriever.invoke(user_input)
        
        # 2. 构建 Prompt
        prompt_text = self._build_prompt(user_input, retrieved_docs)
        
        # 3. 流式生成
        full_response = ""
        for chunk in self.chat_model.stream(prompt_text):
            content = chunk.content if hasattr(chunk, 'content') else str(chunk)
            full_response += content
            yield content
        
        # 4. 保存助手消息
        self.history_store.add_message("assistant", full_response)
        
        # 5. 返回引用信息（最后一次 yield）
        sources = self._build_sources(retrieved_docs)
        
        # 缓存结果
        result = {"response": full_response, "sources": sources}
        self._cache_response(user_input, result)
        
        yield {"sources": sources, "done": True}

    def chat(self, user_input: str) -> dict:
        """对话接口：保存用户消息 -> 调用链 -> 保存助手消息 -> 返回结果（带引用）"""
        # 检查缓存
        cached = self._get_cached_response(user_input)
        if cached:
            return cached
        
        # 保存用户消息
        self.history_store.add_message("user", user_input)
        
        # 1. 检索相关文档
        # 优先使用混合检索（向量 + 关键词）
        if hasattr(self.vector_service, 'kb') and self.vector_service.kb:
            retrieved_docs = self.vector_service.kb.search(user_input, k=3)
        else:
            retriever = self.vector_service.get_retriever()
            retrieved_docs = retriever.invoke(user_input)
        
        # 2. 构建 Prompt
        prompt_text = self._build_prompt(user_input, retrieved_docs)
        
        # 3. 调用模型
        response = self.chat_model.invoke(prompt_text)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # 4. 保存助手消息
        self.history_store.add_message("assistant", content)
        
        # 5. 构建结果
        sources = self._build_sources(retrieved_docs)
        result = {
            "response": content,
            "sources": sources
        }
        
        # 缓存结果
        self._cache_response(user_input, result)
        
        return result
