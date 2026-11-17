"""基于 LangGraph 的多阶段设计工作流（可选组件）。

工作流结构：``analyze（需求分析） -> design（方案设计） -> review（方案评审）``。

若运行环境未安装 ``langgraph``，本模块的 ``run_design_workflow`` 会返回
``None``，由上层自动降级到单模型或算法回退，不影响平台可用性。
"""

from __future__ import annotations

from typing import Any, TypedDict

from app.ai.llm_provider import get_provider, try_parse_json
from app.ai.prompts import SYSTEM_PROMPT, build_user_prompt


class DesignState(TypedDict, total=False):
    """工作流在各节点间传递的状态。"""

    style: str
    area: float | None
    rooms: str | None
    budget_level: str
    requirements: str
    analysis: str
    draft: str
    final: dict[str, Any]


def _node_analyze(state: DesignState) -> DesignState:
    """节点一：需求与户型分析。"""
    provider = get_provider()
    prompt = (
        f"客户户型：{state.get('rooms') or '3室2厅'}，面积约 {state.get('area') or 100}㎡，"
        f"希望风格为「{state.get('style')}」，预算档位 {state.get('budget_level')}，"
        f"额外需求：{state.get('requirements') or '无'}。\n"
        "请用 3-5 条要点分析该户型的优劣势、改造重点与设计策略。"
    )
    text = provider.generate("你是一位户型分析专家。", prompt)
    if not text:
        raise RuntimeError("analyze 节点未获得模型输出")
    return {**state, "analysis": text}


def _node_design(state: DesignState) -> DesignState:
    """节点二：生成方案草稿（JSON）。"""
    provider = get_provider()
    prompt = (
        f"已知户型分析：\n{state.get('analysis')}\n\n"
        + build_user_prompt(
            state.get("style", "现代简约"),
            state.get("area"),
            state.get("rooms"),
            state.get("budget_level", "standard"),
            state.get("requirements", ""),
        )
    )
    text = provider.generate(SYSTEM_PROMPT, prompt)
    if not text:
        raise RuntimeError("design 节点未获得模型输出")
    return {**state, "draft": text}


def _node_review(state: DesignState) -> DesignState:
    """节点三：评审并结构化输出。"""
    provider = get_provider()
    prompt = (
        "请审阅以下设计方案，修正不合理之处，并严格按要求返回 JSON：\n\n"
        f"{state.get('draft')}"
    )
    text = provider.generate(SYSTEM_PROMPT, prompt)
    parsed = try_parse_json(text) or try_parse_json(state.get("draft"))
    if not parsed:
        raise RuntimeError("review 节点未能解析出 JSON")
    return {**state, "final": parsed}


def run_design_workflow(
    style: str,
    area: float | None,
    rooms: str | None,
    budget_level: str,
    requirements: str = "",
) -> dict[str, Any] | None:
    """执行 LangGraph 工作流；不可用时返回 ``None``。"""
    try:
        from langgraph.graph import END, StateGraph  # type: ignore
    except Exception:
        return None

    try:
        graph = StateGraph(DesignState)
        graph.add_node("analyze", _node_analyze)
        graph.add_node("design", _node_design)
        graph.add_node("review", _node_review)
        graph.set_entry_point("analyze")
        graph.add_edge("analyze", "design")
        graph.add_edge("design", "review")
        graph.add_edge("review", END)
        app = graph.compile()

        initial: DesignState = {
            "style": style,
            "area": area,
            "rooms": rooms,
            "budget_level": budget_level,
            "requirements": requirements,
        }
        result = app.invoke(initial)
        return result.get("final")
    except Exception:  # noqa: BLE001 - 任何节点异常都降级
        return None
