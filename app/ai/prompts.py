"""提示词模板：供 LangGraph 工作流、CrewAI 智能体与单模型调用共用。"""

from __future__ import annotations

import json

SYSTEM_PROMPT = (
    "你是一位拥有 15 年经验的资深室内建筑设计师与造价顾问，"
    "擅长把户型条件转化为可落地的空间方案，语言专业、具体、可执行，避免空话。"
)

# 期望模型返回的 JSON 结构说明
OUTPUT_SCHEMA_HINT = """请严格以如下 JSON 结构返回（不要输出多余文字或 Markdown 代码块围栏）：
{
  "summary": "一段方案总述（80-150字）",
  "layout_plan": "空间布局与动线建议，分点说明",
  "style_recommendation": "风格落地要点与配色说明，分点说明",
  "color_palette": [
    {"name": "主色名称", "hex": "#RRGGBB"}
  ]
}"""


def build_user_prompt(
    style: str,
    area: float | None,
    rooms: str | None,
    budget_level: str,
    requirements: str = "",
) -> str:
    """拼接面向大模型的用户提示词。"""
    level_cn = {"economy": "经济型", "standard": "标准型", "premium": "品质型"}.get(
        budget_level, "标准型"
    )
    context = {
        "设计风格": style,
        "建筑面积(㎡)": area or "未提供（按 100㎡ 估算）",
        "房间构成": rooms or "未提供（按 3室2厅1卫 估算）",
        "预算档位": level_cn,
        "额外需求": requirements or "无",
    }
    return (
        "请基于以下户型与需求信息，输出一套完整的装修设计方案。\n\n"
        f"【客户信息】\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        "【要求】\n"
        "1. 空间布局要贴合实际动线与采光通风；\n"
        "2. 风格要点要具体到材质、色彩与工艺；\n"
        "3. 配色给出 4 个色块及其名称与十六进制值。\n\n"
        + OUTPUT_SCHEMA_HINT
    )
