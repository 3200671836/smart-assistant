import json
import dashscope
from dashscope import Generation
from typing import Any

from app.core.config import settings


dashscope.api_key = settings.dashscope_api_key


class LLMService:
    """通用LLM调用封装"""

    def __init__(self, model: str | None = None):
        self.model = model or settings.llm_model

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        structured: bool = False,
        max_retries: int = 2,
    ) -> str:
        """
        同步调用 LLM，支持结构化输出。

        structured=True 时，要求模型返回纯 JSON（不带markdown块）。
        失败时自动降级返回原文。
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(max_retries):
            try:
                response = Generation.call(
                    model=self.model,
                    messages=messages,
                    result_format="message",
                    temperature=0.3,  # 低随机性，保证结构化输出稳定
                )

                if response.status_code != 200:
                    # 阿里云欠费等错误，打日志后抛异常
                    raise RuntimeError(
                        f"DashScope API error: {response.code} - {response.message}"
                    )

                content: str = response.output.choices[0].message.content or ""

                if structured:
                    # 去掉可能的 markdown 代码块包裹（支持 ```json 和 ```）
                    cleaned = content.strip()
                    # 尝试提取 ``` 代码块中的内容
                    if cleaned.startswith("```"):
                        # 去掉首行的 ```json 或 ```
                        first_newline = cleaned.find("\n")
                        if first_newline != -1:
                            cleaned = cleaned[first_newline + 1:]
                        # 去掉尾行的 ```
                        end_marker = cleaned.rfind("\n```")
                        if end_marker != -1:
                            cleaned = cleaned[:end_marker].strip()
                        else:
                            # 没找到结尾，去掉末尾的 ```
                            if cleaned.endswith("\n```"):
                                cleaned = cleaned[:-4].strip()
                    # 如果清理后以 ``` 开头（没处理干净），再试一次
                    if cleaned.startswith("```"):
                        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
                        if "\n```" in cleaned:
                            cleaned = cleaned[:cleaned.rfind("\n```")].strip()
                    try:
                        json.loads(cleaned)  # 验证是合法 JSON
                        return cleaned
                    except json.JSONDecodeError:
                        # 尝试直接解析原始 content（可能模型没加代码块）
                        try:
                            json.loads(content.strip())
                            return content.strip()
                        except json.JSONDecodeError:
                            raise ValueError(f"LLM returned non-JSON: {cleaned[:200]}")

                return content

            except (RuntimeError, ValueError) as e:
                if attempt < max_retries - 1:
                    continue
                # 最后一次失败，返回错误文本（让调用方决定如何处理）
                return f"[LLM调用失败] {type(e).__name__}: {str(e)}"

    def extract_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
        """返回解析后的 dict，失败返回 None"""
        raw = self.chat(system_prompt, user_prompt, structured=True)
        if raw.startswith("[LLM调用失败]"):
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
