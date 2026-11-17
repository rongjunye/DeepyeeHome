"""PDF 报告生成服务。

使用 reportlab 生成「设计方案报告」PDF。中文通过内置 CID 字体
``STSong-Light`` 渲染，无需额外字体文件或系统依赖。
"""

from __future__ import annotations

import io
from typing import Any
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# 主题色（与前端保持一致的暖金 + 墨色）
_GOLD = colors.HexColor("#C89F6D")
_INK = colors.HexColor("#1F1F1F")
_BODY = colors.HexColor("#3A3A3A")
_MUTED = colors.HexColor("#7A7A7A")
_LINE = colors.HexColor("#DCDCDC")

_FONT = "STSong-Light"
_font_ready = False


def _ensure_font() -> None:
    """注册中文 CID 字体（幂等）。"""
    global _font_ready
    if _font_ready:
        return
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(_FONT))
    except Exception:  # noqa: BLE001 - 极端环境下退回 Helvetica
        pass
    _font_ready = True


def _style(font: str) -> dict[str, ParagraphStyle]:
    """构建排版样式表。"""
    getSampleStyleSheet()  # 确保默认样式已初始化
    return {
        "title": ParagraphStyle(
            "title", fontName=font, fontSize=22, leading=30, textColor=_INK, spaceAfter=4
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName=font, fontSize=10, leading=16, textColor=_MUTED
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName=font,
            fontSize=13.5,
            leading=20,
            textColor=colors.HexColor("#8A6B3F"),
            spaceBefore=14,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", fontName=font, fontSize=10.5, leading=17, textColor=_BODY
        ),
        "small": ParagraphStyle(
            "small", fontName=font, fontSize=9, leading=14, textColor=_MUTED
        ),
        "cellhead": ParagraphStyle(
            "cellhead", fontName=font, fontSize=9.5, leading=14, textColor=colors.white
        ),
        "cell": ParagraphStyle("cell", fontName=font, fontSize=9.5, leading=14, textColor=_BODY),
    }


def _para(text: Any, style: ParagraphStyle) -> Paragraph:
    """安全地把文本包装成 Paragraph（转义 XML、换行转 <br/>）。"""
    safe = escape(str(text if text is not None else "")).replace("\n", "<br/>")
    return Paragraph(safe, style)


def _budget_chart(budget: dict[str, Any], width: float = 470, height: float = 150) -> Drawing:
    """用 reportlab 图形原语手绘「预算构成」横向条形图。"""
    drawing = Drawing(width, height)
    items = budget.get("by_category", []) or []
    if not items:
        return drawing

    max_amount = max((float(item.get("amount", 0)) for item in items), default=1.0) or 1.0
    label_w = 82.0
    value_w = 62.0
    bar_area = width - label_w - value_w
    row_h = height / len(items)

    for index, item in enumerate(items):
        y = height - (index + 1) * row_h + row_h * 0.28
        amount = float(item.get("amount", 0))
        bar_w = max(bar_area * (amount / max_amount), 1.0)
        drawing.add(
            String(
                0,
                y + 1,
                str(item.get("category", "")),
                fontName=_FONT,
                fontSize=8.5,
                fillColor=_BODY,
            )
        )
        drawing.add(
            Rect(
                label_w,
                y,
                bar_w,
                row_h * 0.5,
                fillColor=_GOLD,
                strokeColor=None,
            )
        )
        drawing.add(
            String(
                label_w + bar_w + 5,
                y + 1,
                f"{amount:,.0f}",
                fontName=_FONT,
                fontSize=8.5,
                fillColor=_MUTED,
            )
        )
    return drawing


def _palette_table(palette: list[dict[str, str]], styles: dict[str, ParagraphStyle]) -> Table:
    """绘制配色色块表。"""
    swatches = ["" for _ in palette]
    names = [_para(f"{c.get('name','')}<br/>{c.get('hex','')}", styles["small"]) for c in palette]
    col_width = 470 / max(len(palette), 1)
    table = Table([swatches, names], colWidths=[col_width] * len(palette))
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, 0), 16),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 16),
    ]
    for index, color_item in enumerate(palette):
        style.append(("BACKGROUND", (index, 0), (index, 0), colors.HexColor(color_item.get("hex", "#CCCCCC"))))
        style.append(("BOX", (index, 0), (index, 0), 0.6, _LINE))
    table.setStyle(TableStyle(style))
    return table


def build_design_report(design: Any, project: Any) -> bytes:
    """生成设计方案 PDF，返回字节流。"""
    _ensure_font()
    styles = _style(_FONT)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"设计方案报告 #{design.id}",
        author="NeuroArchAI Platform",
    )

    meta = getattr(project, "meta_info", None) or {}
    budget = design.budget or {}
    materials = design.materials or []
    palette = design.color_palette or []

    flow: list[Any] = []

    # ---------- 页眉 ----------
    flow.append(_para("设计方案报告", styles["title"]))
    flow.append(
        _para(
            f"NeuroArchAI Platform · 报告编号 #{design.id} · 生成于 {design.created_at}",
            styles["subtitle"],
        )
    )
    flow.append(Spacer(1, 10))

    # ---------- 项目概览 ----------
    overview = [
        ["项目名称", getattr(project, "title", "-"), "设计风格", design.style or "-"],
        [
            "建筑面积",
            f"{meta.get('area', budget.get('area', '-'))} ㎡",
            "房间构成",
            meta.get("rooms", "-"),
        ],
        [
            "预算档位",
            budget.get("level_label", "-"),
            "预估总价",
            f"¥{float(budget.get('total', 0)):,.0f}",
        ],
        ["生成引擎", design.provider or "-", "方案编号", f"#{design.id}"],
    ]
    overview_table = Table(overview, colWidths=[65, 170, 65, 170])
    overview_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), _FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("TEXTCOLOR", (0, 0), (0, -1), _MUTED),
                ("TEXTCOLOR", (2, 0), (2, -1), _MUTED),
                ("TEXTCOLOR", (1, 0), (1, -1), _BODY),
                ("TEXTCOLOR", (3, 0), (3, -1), _BODY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, _LINE),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAF8F5")),
                ("BOX", (0, 0), (-1, -1), 0.6, _LINE),
            ]
        )
    )
    flow.append(overview_table)

    # ---------- 方案总述 ----------
    flow.append(_para("方案总述", styles["h2"]))
    flow.append(_para(design.summary, styles["body"]))

    # ---------- 空间布局 ----------
    flow.append(_para("空间布局与动线", styles["h2"]))
    flow.append(_para(design.layout_plan, styles["body"]))

    # ---------- 风格要点 ----------
    flow.append(_para("风格落地要点", styles["h2"]))
    flow.append(_para(design.style_recommendation, styles["body"]))

    # ---------- 配色 ----------
    if palette:
        flow.append(_para("配色方案", styles["h2"]))
        flow.append(_palette_table(palette, styles))
        flow.append(Spacer(1, 6))

    # ---------- 预算 ----------
    flow.append(_para("预算估算", styles["h2"]))
    flow.append(_para(budget.get("note", ""), styles["small"]))
    flow.append(Spacer(1, 8))
    flow.append(_budget_chart(budget))

    budget_rows = [["费用类别", "金额（元）", "占比"]]
    for item in budget.get("by_category", []):
        budget_rows.append(
            [
                str(item.get("category", "")),
                f"{float(item.get('amount', 0)):,.0f}",
                f"{float(item.get('ratio', 0)) * 100:.1f}%",
            ]
        )
    budget_rows.append(["合计", f"{float(budget.get('total', 0)):,.0f}", "100.0%"])
    budget_table = Table(budget_rows, colWidths=[220, 130, 120])
    budget_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), _FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("BACKGROUND", (0, 0), (-1, 0), _INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, _LINE),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F3EEE7")),
                ("FONTNAME", (0, -1), (-1, -1), _FONT),
            ]
        )
    )
    flow.append(Spacer(1, 10))
    flow.append(budget_table)

    # ---------- 材料清单 ----------
    if materials:
        flow.append(_para("材料清单", styles["h2"]))
        material_rows = [["类别", "材料 / 工艺", "规格", "预估费用"]]
        for item in materials:
            material_rows.append(
                [
                    str(item.get("category", "")),
                    str(item.get("name", "")),
                    str(item.get("specification", "")),
                    f"{float(item.get('estimated_cost', 0)):,.0f}",
                ]
            )
        material_table = Table(material_rows, colWidths=[70, 170, 150, 80])
        material_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), _FONT),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), _INK),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.4, _LINE),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAF8F5")]),
                ]
            )
        )
        flow.append(material_table)

    # ---------- 户型图 ----------
    floorplan_path = getattr(project, "floorplan_path", None)
    if floorplan_path:
        from app.config import settings
        from PIL import Image as PILImage

        image_path = settings.upload_dir / floorplan_path
        if image_path.exists():
            try:
                with PILImage.open(image_path) as image:
                    ratio = image.height / image.width if image.width else 0.6
                width = 380.0
                flow.append(_para("原始户型图", styles["h2"]))
                flow.append(Image(str(image_path), width=width, height=width * ratio))
            except Exception:  # noqa: BLE001 - 图片异常不影响报告生成
                pass

    flow.append(Spacer(1, 16))
    flow.append(
        _para(
            "本报告由 NeuroArchAI Platform 自动生成，预算与材料数据为算法估算，"
            "仅供装修决策参考，实际以现场测量与品牌报价为准。",
            styles["small"],
        )
    )

    doc.build(flow)
    return buffer.getvalue()
