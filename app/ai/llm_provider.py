"""LLM 提供商抽象层。

统一封装三种驱动方式，对上层暴露一致的 ``generate()`` 接口：

* ``GroqProvider``   —— Groq 云端 OpenAI 兼容接口
* ``OllamaProvider`` —— 本地 Ollama 服务
* ``NullProvider``   —— 不调用大模型（触发算法回退）

任何调用异常都会被吞掉并返回 ``None``，由上层决定是否回退，
从而保证平台不会因为外部服务不可用而崩掉。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

import httpx

from app.config import settings


class BaseLLMProvider(ABC):
    """LLM 提供商基类。"""

    name: str = "base"

    @abstractmethod
    def available(self) -> bool:
        """当前提供商是否已就绪（如 API Key 是否配置）。"""

    @abstractmethod
    def _chat(self, system: str, prompt: str) -> str | None:
        """底层单轮对话实现，返回文本或 None。"""

    def generate(self, system: str, prompt: str) -> str | None:
        """对外统一入口：带异常兜底的单轮对话。"""
        try:
            return self._chat(system, prompt)
        except Exception:  # noqa: BLE001 - 故意吞掉所有异常以触发回退
            return None


class GroqProvider(BaseLLMProvider):
    """Groq 云端提供商（OpenAI 兼容的 /chat/completions）。"""

    name = "groq"

    def available(self) -> bool:
        return bool(settings.groq_api_key.strip())

    def _chat(self, system: str, prompt: str) -> str | None:
        url = f"{settings.groq_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.groq_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": settings.llm_max_tokens,
        }
        with httpx.Client(timeout=settings.llm_timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]


class OllamaProvider(BaseLLMProvider):
    """本地 Ollama 提供商（/api/chat）。"""

    name = "ollama"

    def available(self) -> bool:
        return bool(settings.ollama_base_url.strip())

    def _chat(self, system: str, prompt: str) -> str | None:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.7},
        }
        with httpx.Client(timeout=settings.llm_timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data.get("message", {}).get("content")


class NullProvider(BaseLLMProvider):
    """空提供商：显式表示「不调用大模型」。"""

    name = "none"

    def available(self) -> bool:
        return False

    def _chat(self, system: str, prompt: str) -> str | None:
        return None


_PROVIDERS: dict[str, type[BaseLLMProvider]] = {
    "groq": GroqProvider,
    "ollama": OllamaProvider,
    "none": NullProvider,
}


def get_provider() -> BaseLLMProvider:
    """根据配置实例化对应的提供商。"""
    provider_cls = _PROVIDERS.get(settings.llm_provider, NullProvider)
    return provider_cls()


def try_parse_json(text: str | None) -> dict | None:
    """尽最大努力从模型输出中解析出 JSON 对象。

    兼容模型习惯性包裹 ```json ... ``` 代码块的情况。
    """
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # 去掉首尾的 ``` 围栏
        cleaned = cleaned.split("```", 2)[1] if cleaned.count("```") >= 2 else cleaned
        cleaned = cleaned.removeprefix("json").strip()
    try:
        result = json.loads(cleaned)
        return result if isinstance(result, dict) else None
    except json.JSONDecodeError:
        # 退一步：截取第一个 { 到最后一个 } 之间的内容
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                result = json.loads(cleaned[start : end + 1])
                return result if isinstance(result, dict) else None
            except json.JSONDecodeError:
                return None
        return None
