import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库
    database_url: str = "sqlite:///./data.db"

    # 阿里云 DashScope（LLM + Embedding）
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "sk-2a3a0d17cd964a16b124e7bbf2af5e25")
    dashscope_base_url: str = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    llm_model: str = "qwen3-max"
    embedding_model: str = "text-embedding-v4"

    # 上传文件
    upload_dir: str = "./uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
