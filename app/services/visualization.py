"""可视化服务：把预算等数据转换成 Plotly 图表 JSON。

优先使用 ``plotly`` 生成；若环境未安装 plotly，则退回手工构造等价的
plotly.js 图表规格，保证前端渲染逻辑无需改动。
"""

from __future__ import annotations

import json
from typing import Any, Sequence

# 统一的暗色极简主题（与前端风格一致）
_THEME = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#E8E6E1", "family": "Inter, system-ui, sans-serif", "size": 13},
    "margin": {"l": 40, "r": 24, "t": 48, "b": 40},
    "colorway": ["#C89F6D", "#7FA6A0", "#B8BDC4", "#8C7BB0", "#D98F6B", "#6B8DD6", "#C4A0A0"],
}

_PALETTE = _THEME["colorway"]


def _plotly_modules():
    """尝试导入 plotly，失败则返回 (None, None)。"""
    try:  # pragma: no cover - 取决于运行环境
        import plotly.graph_objects as go  # type: ignore
        import plotly.io as pio  # type: ignore

        return go, pio
    except Exception:
        return None, None


def _figure_dict(fig: Any) -> dict[str, Any]:
    """把 plotly Figure 序列化为纯 JSON 字典。"""
    _, pio = _plotly_modules()
    if pio is not None:
        return json.loads(pio.to_json(fig))
    return fig.to_dict()  # 理论上不会走到这里


def build_budget_pie(budget: dict[str, Any]) -> dict[str, Any]:
    """生成「预算构成」环形饼图规格。"""
    items: Sequence[dict[str, Any]] = budget.get("by_category", [])
    labels = [item["category"] for item in items]
    values = [item["amount"] for item in items]

    go, _ = _plotly_modules()
    if go is not None:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.48,
                    textinfo="label+percent",
                    marker={"line": {"color": "#111315", "width": 2}},
                )
            ]
        )
        fig.update_layout(title="预算构成", **_THEME)
        return _figure_dict(fig)

    # 回退方案：手工构造 plotly.js 兼容规格
    return {
        "data": [
            {
                "type": "pie",
                "labels": labels,
                "values": values,
                "hole": 0.48,
                "textinfo": "label+percent",
                "marker": {"line": {"color": "#111315", "width": 2}},
                "textfont": {"color": "#111315"},
            }
        ],
        "layout": {"title": {"text": "预算构成"}, "paper_bgcolor": "rgba(0,0,0,0)"},
    }


def build_material_bar(materials: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """生成「主要材料花费」横向条形图规格。"""
    items = sorted(materials, key=lambda m: m.get("estimated_cost", 0), reverse=True)[:7]
    names = [m["name"] for m in items]
    costs = [m.get("estimated_cost", 0) for m in items]

    go, _ = _plotly_modules()
    if go is not None:
        fig = go.Figure(
            data=[
                go.Bar(
                    x=costs,
                    y=names,
                    orientation="h",
                    marker={"color": _PALETTE[0]},
                    hovertemplate="%{y}：¥%{x:,.0f}<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            title="主要材料花费（元）",
            xaxis={"gridcolor": "rgba(255,255,255,0.06)"},
            **_THEME,
        )
        return _figure_dict(fig)

    return {
        "data": [
            {
                "type": "bar",
                "x": costs,
                "y": names,
                "orientation": "h",
                "marker": {"color": _PALETTE[0]},
            }
        ],
        "layout": {"title": {"text": "主要材料花费（元）"}, "paper_bgcolor": "rgba(0,0,0,0)"},
    }


def build_style_radar(scores: dict[str, float]) -> dict[str, Any]:
    """生成「风格契合度」雷达图规格。``scores`` 形如 {维度: 分值}。"""
    axes = list(scores.keys())
    values = list(scores.values())

    go, _ = _plotly_modules()
    if go is not None:
        fig = go.Figure(
            data=[
                go.Scatterpolar(
                    r=values + values[:1],
                    theta=axes + axes[:1],
                    fill="toself",
                    line={"color": _PALETTE[1]},
                    fillcolor="rgba(127,166,160,0.28)",
                )
            ]
        )
        fig.update_layout(
            title="风格契合度",
            polar={"bgcolor": "rgba(0,0,0,0)"},
            showlegend=False,
            **_THEME,
        )
        return _figure_dict(fig)

    return {
        "data": [
            {
                "type": "scatterpolar",
                "r": values + values[:1],
                "theta": axes + axes[:1],
                "fill": "toself",
                "line": {"color": _PALETTE[1]},
            }
        ],
        "layout": {"title": {"text": "风格契合度"}, "showlegend": False},
    }
