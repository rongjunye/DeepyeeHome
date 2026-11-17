"""设计生成编排器：统一协调「多智能体 / 大模型 / 算法回退」三条路径。

设计思路（稳健优先）：
1. 先用**算法引擎**算出确定性的骨架（预算、材料、配色、图表），保证一定有产出；
2. 若配置了大模型（groq / ollama），再依次尝试 LangGraph 多阶段工作流、
   CrewAI 多智能体、单次大模型，用其文本结果**增强**骨架中的方案描述；
3. 任何一步失败都静默降级，绝不会因为没有模型而报错。
"""

from __future__ import annotations

from typing import Any

from app.ai.fallback import generate_fallback_design
from app.ai.llm_provider import get_provider, try_parse_json
from app.ai.prompts import SYSTEM_PROMPT, build_user_prompt

# 需要被大模型文本覆盖的字段
_TEXT_FIELDS = ("summary", "layout_plan", "style_recommendation")


def _normalize_palette(palette: Any) -> list[dict[str, str]]:
    """把模型返回的配色归一为 [{name, hex}]。"""
    if not isinstance(palette, list):
        return []
    normalized: list[dict[str, str]] = []
    for item in palette:
        if isinstance(item, dict) and item.get("hex"):
            normalized.append(
                {"name": str(item.get("name") or "色块"), "hex": str(item["hex"])}
            )
    return normalized


def _merge_text(base: dict[str, Any], parsed: dict[str, Any], engine_label: str) -> dict[str, Any]:
    """把大模型返回的文本/配色合并进算法骨架。"""
    merged = dict(base)
    used = False
    for key in _TEXT_FIELDS:
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            merged[key] = value.strip()
            used = True
    palette = _normalize_palette(parsed.get("color_palette"))
    if palette:
        merged["color_palette"] = palette
        used = True
    if used:
        merged["provider"] = engine_label
    return merged


def _llm_enrich(
    base: dict[str, Any],
    style: str,
    area: float | None,
    rooms: str | None,
    budget_level: str,
    requirements: str,
) -> dict[str, Any]:
    """尝试用大模型增强方案文本；失败则原样返回骨架。"""
    provider = get_provider()
    if not provider.available():
        # LLM_PROVIDER=none 或未配置 Key：直接使用算法骨架
        return base

    # 路径一：LangGraph 多阶段工作流
    try:
        from app.ai.graph import run_design_workflow

        parsed = run_design_workflow(style, area, rooms, budget_level, requirements)
        if parsed:
            return _merge_text(base, parsed, "LangGraph 多智能体")
    except Exception:  # noqa: BLE001
        pass

    # 路径二：CrewAI 多智能体协作
    try:
        from app.ai.agents import run_design_crew

        parsed = run_design_crew(style, area, rooms, budget_level, requirements)
        if parsed:
            return _merge_text(base, parsed, "CrewAI 多智能体")
    except Exception:  # noqa: BLE001
        pass

    # 路径三：单次大模型调用
    try:
        raw = provider.generate(
            SYSTEM_PROMPT, build_user_prompt(style, area, rooms, budget_level, requirements)
        )
        parsed = try_parse_json(raw)
        if parsed:
            label = "Groq 大模型" if provider.name == "groq" else "Ollama 本地模型"
            return _merge_text(base, parsed, label)
    except Exception:  # noqa: BLE001
        pass

    return base


def generate_design(
    *,
    style: str,
    area: float | None,
    rooms: str | None,
    budget_level: str,
    requirements: str = "",
) -> dict[str, Any]:
    """对外统一入口：生成一份完整设计方案。"""
    base = generate_fallback_design(style, area, rooms, budget_level, requirements)
    return _llm_enrich(base, style, area, rooms, budget_level, requirements)
