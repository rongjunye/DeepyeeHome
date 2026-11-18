"""户型图视觉识别（可选能力）。

把上传的户型图交给**支持图片输入**的大模型，让它输出每个房间的归一化矩形区域。
识别结果会交给前端编辑器，供用户手动微调后再保存。

启用条件（二选一）：
* ``LLM_PROVIDER=groq``   —— 配置 ``GROQ_API_KEY``，并确保 ``VISION_MODEL`` 是视觉模型
* ``LLM_PROVIDER=ollama`` —— 本地拉取视觉模型（如 ``qwen2.5vl`` / ``llava``），并设置 ``VISION_MODEL``

未配置时 ``recognize_layout`` 返回 ``None``，由前端提示改用手动标注。
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from app.ai.llm_provider import try_parse_json
from app.config import settings

_PROMPT = """请识别这张住宅户型图（平面图）。

要求：
1. 找出图中每一个房间 / 功能区，给出它的矩形区域；
2. 坐标以图片**左上角为原点**，宽、高分别**归一化到 0~1**；
3. type 只能取以下之一：living / dining / kitchen / master / bedroom / bath / balcony / entry / other

严格按如下 JSON 返回，不要输出任何多余文字：
{"rooms":[{"name":"客厅","type":"living","x":0.05,"y":0.35,"w":0.32,"h":0.28}],"total_width_m":12.5}

其中 x、y 是矩形左上角，w、h 是宽高（都是 0~1 的归一化值）；total_width_m 是你估算的户型总宽（米）。"""


def _default_vision_model(provider: str) -> str:
    """各提供商的默认视觉模型（可通过 VISION_MODEL 覆盖）。"""
    if provider == "groq":
        return "meta-llama/llama-4-scout-17b-16e-instruct"
    if provider == "ollama":
        return "qwen2.5vl:7b"
    return ""


def vision_available() -> bool:
    """当前配置是否具备视觉识别能力。"""
    provider = settings.llm_provider
    if provider == "groq":
        return bool(settings.groq_api_key.strip())
    if provider == "ollama":
        return bool(settings.ollama_base_url.strip())
    return False


def _sanitize_rooms(parsed: dict[str, Any]) -> dict[str, Any] | None:
    """校正模型返回的房间数据，剔除非法项并夹到 0~1 范围内。"""
    rooms = parsed.get("rooms")
    if not isinstance(rooms, list) or not rooms:
        return None

    cleaned: list[dict[str, Any]] = []
    for item in rooms:
        if not isinstance(item, dict):
            continue
        try:
            x = min(max(float(item["x"]), 0.0), 1.0)
            y = min(max(float(item["y"]), 0.0), 1.0)
            w = min(max(float(item["w"]), 0.0), 1.0)
            h = min(max(float(item["h"]), 0.0), 1.0)
        except (KeyError, TypeError, ValueError):
            continue
        if w <= 0.02 or h <= 0.02:
            continue
        # 保证不越界
        w = min(w, 1.0 - x)
        h = min(h, 1.0 - y)
        cleaned.append(
            {
                "name": str(item.get("name") or "房间")[:32],
                "type": str(item.get("type") or "other")[:32],
                "x": round(x, 4),
                "y": round(y, 4),
                "w": round(w, 4),
                "h": round(h, 4),
            }
        )

    if not cleaned:
        return None

    try:
        width_m = float(parsed.get("total_width_m") or 12.0)
    except (TypeError, ValueError):
        width_m = 12.0
    width_m = min(max(width_m, 2.0), 100.0)

    return {"rooms": cleaned, "total_width_m": round(width_m, 2), "source": "vision"}


def recognize_layout(image_bytes: bytes, mime: str) -> dict[str, Any] | None:
    """调用视觉模型识别户型图；不可用或失败时返回 ``None``。"""
    if not vision_available():
        return None

    model = settings.vision_model.strip() or _default_vision_model(settings.llm_provider)
    if not model:
        return None

    encoded = base64.b64encode(image_bytes).decode()

    try:
        if settings.llm_provider == "groq":
            text = _call_groq(encoded, mime, model)
        else:
            text = _call_ollama(encoded, model)
    except Exception:  # noqa: BLE001 - 网络 / 权限 / 模型不支持等一律降级
        return None

    parsed = try_parse_json(text)
    if not parsed:
        return None
    return _sanitize_rooms(parsed)


def _call_groq(encoded: str, mime: str, model: str) -> str | None:
    """Groq（OpenAI 兼容）视觉调用。"""
    url = f"{settings.groq_base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{encoded}"},
                    },
                ],
            }
        ],
        "temperature": 0,
        "max_tokens": 2048,
    }
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=settings.llm_timeout) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    return data["choices"][0]["message"]["content"]


def _call_ollama(encoded: str, model: str) -> str | None:
    """Ollama 视觉调用（images 字段传 base64）。"""
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": _PROMPT, "images": [encoded]}],
        "stream": False,
        "options": {"temperature": 0},
    }
    with httpx.Client(timeout=settings.llm_timeout) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    return data.get("message", {}).get("content")