import os

# 获取 config_data.py 所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# FAISS 索引文件保存路径
faiss_index_path = os.path.join(BASE_DIR, "faiss_index")
md5_path = os.path.join(BASE_DIR, "md5.txt")


# 文档分块优化配置
# 按段落/语义分块，提升检索质量

chunk_size = 500          # 减小块大小，提高信息密度
chunk_overlap = 50        # 适当重叠，保持上下文连贯

# 优化分隔符顺序：优先按段落和语义标点分割
# 中文语境下优先使用中文标点，再考虑英文标点
separators = [
    "\n\n",     # 段落分隔（最高优先级）
    "\n",       # 换行
    "。",       # 中文句号
    "？",       # 中文问号
    "！",       # 中文感叹号
    "；",       # 中文分号
    "...",      # 省略号
    "..",       # 双点
    ".",        # 英文句号
    "?",        # 英文问号
    "!",        # 英文感叹号
    ";",        # 英文分号
    "，",       # 中文逗号
    ",",        # 英文逗号
    " ",        # 空格
    ""          # 字符级分割（最后手段）
]

# 文本分割阈值：超过此长度才分块
# 设置为 chunk_size * 1.5，避免短文本强制分块
max_split_char_number = 750


similarity_threshold = 1        #检索返回匹配的文档数量

embedding_model_name = "text-embedding-v4"


chat_model_name = "qwen3-max"
