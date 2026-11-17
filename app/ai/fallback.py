"""算法回退引擎：不依赖任何大模型，用内置规则产出一套完整设计方案。

触发条件：
* ``LLM_PROVIDER=none``（用户主动选择零配置）
* 或大模型调用异常 / 超时

它的存在保证平台「开箱即用」，也作为大模型结果的兜底。
"""

from __future__ import annotations

from typing import Any

from app.services.visualization import (
    build_budget_pie,
    build_material_bar,
    build_style_radar,
)
from app.ai.layout3d import build_layout3d

# ---------------------------------------------------------------------------
# 风格预设库
# ---------------------------------------------------------------------------
# 每种风格包含：定位语、配色、材料清单、设计要点、契合度雷达分。
STYLE_PRESETS: dict[str, dict[str, Any]] = {
    "现代简约": {
        "tagline": "少即是多，让空间回归秩序与留白",
        "palette": [
            {"name": "主色 · 雾霾灰", "hex": "#B8BDC4"},
            {"name": "底色 · 米白", "hex": "#F2EFEA"},
            {"name": "点缀 · 原木色", "hex": "#C89F6D"},
            {"name": "压色 · 墨黑", "hex": "#2B2B2B"},
        ],
        "materials": {
            "地面": ("大板哑光砖 / 岩板", "750×1500，柔光面"),
            "墙面": ("哑光乳胶漆", "低饱和乳白，耐擦洗"),
            "顶面": ("无主灯吊顶", "磁吸轨道 + 筒灯"),
            "水电改造": ("标准强电 + 弱电", "国标铜芯线，PPR 水管"),
            "定制柜体": ("隐形收纳柜", "E0 级颗粒板，无拉手门"),
            "门窗": ("极窄边框推拉门", "双层中空玻璃"),
            "软装灯具": ("几何线性灯具", "暖白 3000K"),
        },
        "design_points": [
            "用大面留白与整墙收纳，弱化视觉噪音",
            "地面与墙面同色系铺陈，拉长空间纵深",
            "以原木与金属做少量点缀，避免单调",
        ],
        "radar": {"简洁度": 95, "收纳力": 85, "温馨感": 60, "造价友好": 78, "个性化": 55},
    },
    "北欧": {
        "tagline": "明亮通透，原木与柔光营造松弛感",
        "palette": [
            {"name": "主色 · 云白", "hex": "#F7F5F0"},
            {"name": "辅色 · 浅灰", "hex": "#D6D3CD"},
            {"name": "点缀 · 浅橡木", "hex": "#D8B98A"},
            {"name": "点缀 · 莫兰迪绿", "hex": "#8FA98F"},
        ],
        "materials": {
            "地面": ("浅色橡木地板", "三层实木，哑光"),
            "墙面": ("环保乳胶漆", "云白 / 浅灰"),
            "顶面": ("平顶 + 局部木饰面", "原木吊顶条"),
            "水电改造": ("标准水电", "回路分区控制"),
            "定制柜体": ("白橡木收纳柜", "示木纹饰面"),
            "门窗": ("白框木门", "通透玻璃隔断"),
            "软装灯具": ("纸质 / 布艺吊灯", "暖白 2700K"),
        },
        "design_points": [
            "最大化自然采光，窗帘选用轻薄纱料",
            "原木家具 + 织物软装提升温度",
            "绿植与莫兰迪色做视觉呼吸点",
        ],
        "radar": {"简洁度": 82, "收纳力": 70, "温馨感": 92, "造价友好": 80, "个性化": 62},
    },
    "新中式": {
        "tagline": "以简驭繁，东方气韵与现代居住的平衡",
        "palette": [
            {"name": "主色 · 月白", "hex": "#EDE9E2"},
            {"name": "辅色 · 胡桃木", "hex": "#5C4436"},
            {"name": "点缀 · 黛青", "hex": "#3E5B63"},
            {"name": "点缀 · 黄铜", "hex": "#B08D57"},
        ],
        "materials": {
            "地面": ("浅色石材 / 木纹砖", "哑光，回纹拼花收边"),
            "墙面": ("艺术漆 + 木格栅", "宣纸质感艺术漆"),
            "顶面": ("跌级吊顶 + 木线条", "回字纹收口"),
            "水电改造": ("标准水电", "暗藏线路"),
            "定制柜体": ("胡桃木博古收纳柜", "榫卯工艺饰面"),
            "门窗": ("月洞门 / 格栅门", "实木复合"),
            "软装灯具": ("宫灯造型灯", "暖黄光"),
        },
        "design_points": [
            "用格栅、屏风做空间的若隐若现",
            "胡桃木与黄铜搭配，厚重中见精致",
            "留白与水景、盆景呼应东方意境",
        ],
        "radar": {"简洁度": 68, "收纳力": 75, "温馨感": 78, "造价友好": 55, "个性化": 88},
    },
    "日式侘寂": {
        "tagline": "粗粝质感与留白，安放安静的日常",
        "palette": [
            {"name": "主色 · 米砂", "hex": "#E4DDD0"},
            {"name": "辅色 · 亚麻", "hex": "#CBBFA8"},
            {"name": "点缀 · 炭褐", "hex": "#4A4038"},
            {"name": "点缀 · 苔绿", "hex": "#7C8471"},
        ],
        "materials": {
            "地面": ("哑光微水泥 / 草编地垫", "无缝微水泥"),
            "墙面": ("肌理艺术涂料", "手工刮砂质感"),
            "顶面": ("裸露木梁 + 平顶", "原木本色"),
            "水电改造": ("标准水电", "地暖 + 新风预留"),
            "定制柜体": ("原木低矮收纳柜", "白蜡木本色"),
            "门窗": ("原木格栅推拉门", "和纸 / 亚麻帘"),
            "软装灯具": ("和纸灯 / 陶土灯", "暖黄柔光"),
        },
        "design_points": [
            "保留材质原始肌理，拒绝过度装饰",
            "低矮家具降低重心，放大空间层高",
            "以一抹苔绿与陶器点缀，呼应自然",
        ],
        "radar": {"简洁度": 80, "收纳力": 65, "温馨感": 88, "造价友好": 62, "个性化": 85},
    },
    "工业风": {
        "tagline": "粗犷结构之美，冷峻而有力量感",
        "palette": [
            {"name": "主色 · 水泥灰", "hex": "#8A8D8F"},
            {"name": "辅色 · 铁黑", "hex": "#2E2E30"},
            {"name": "点缀 · 锈红", "hex": "#9C4A3C"},
            {"name": "点缀 · 黄铜", "hex": "#B08D57"},
        ],
        "materials": {
            "地面": ("自流平 / 微水泥", "哑光水泥面"),
            "墙面": ("裸露砖墙 + 水泥漆", "局部清水砖"),
            "顶面": ("裸露管线 + 金属网", "黑铁喷漆"),
            "水电改造": ("明装管线", "镀锌钢管走顶"),
            "定制柜体": ("黑铁 + 原木组合柜", "工业五金件"),
            "门窗": ("黑框玻璃隔断", "钢化玻璃"),
            "软装灯具": ("爱迪生灯泡 / 轨道灯", "暖黄"),
        },
        "design_points": [
            "保留结构与管线，化繁为简地做展示",
            "黑铁、水泥与原木形成质感碰撞",
            "皮革沙发与金属家具强化硬朗气质",
        ],
        "radar": {"简洁度": 72, "收纳力": 68, "温馨感": 52, "造价友好": 70, "个性化": 86},
    },
    "轻奢": {
        "tagline": "克制的高级感，细节处见精致",
        "palette": [
            {"name": "主色 · 珍珠白", "hex": "#F0ECE6"},
            {"name": "辅色 · 香槟金", "hex": "#C9A96A"},
            {"name": "点缀 · 岩板灰", "hex": "#5B5D60"},
            {"name": "点缀 · 莫兰迪蓝", "hex": "#6E7F97"},
        ],
        "materials": {
            "地面": ("大规格岩板 / 大理石纹砖", "900×1800 亮面"),
            "墙面": ("护墙板 + 岩板背景墙", "香槟金线条收边"),
            "顶面": ("叠级吊顶 + 金属线条", "无主灯"),
            "水电改造": ("标准水电 + 智能预留", "全屋智能面板"),
            "定制柜体": ("高光 UV 板定制柜", "隐形拉手"),
            "门窗": ("极窄金属框门", "长虹玻璃"),
            "软装灯具": ("水晶 / 金属艺术吊灯", "三色温"),
        },
        "design_points": [
            "以岩板与金属线条勾勒精致轮廓",
            "大面积软包提升触感与档次",
            "灯光分层设计，营造通透镜面感",
        ],
        "radar": {"简洁度": 66, "收纳力": 72, "温馨感": 70, "造价友好": 42, "个性化": 80},
    },
    "奶油风": {
        "tagline": "柔软治愈，松弛而有安全感的家",
        "palette": [
            {"name": "主色 · 奶油白", "hex": "#F5EEE4"},
            {"name": "辅色 · 燕麦色", "hex": "#E3D5C3"},
            {"name": "点缀 · 浅咖", "hex": "#B79B7E"},
            {"name": "点缀 · 暖木色", "hex": "#C89F6D"},
        ],
        "materials": {
            "地面": ("奶油色柔光砖", "600×1200 哑光"),
            "墙面": ("奶油色艺术漆", "圆弧阳角收边"),
            "顶面": ("圆弧无主灯吊顶", "隐藏灯带"),
            "水电改造": ("标准水电", "柔光预留"),
            "定制柜体": ("弧形奶油柜体", "肤感膜门板"),
            "门窗": ("奶白圆弧拱门", "长虹玻璃"),
            "软装灯具": ("奶油布艺壁灯", "暖白 3000K"),
        },
        "design_points": [
            "以圆弧与奶白色弱化空间的硬朗感",
            "布艺、藤编、亚麻营造柔软触感",
            "低饱和配色让家更治愈放松",
        ],
        "radar": {"简洁度": 78, "收纳力": 70, "温馨感": 95, "造价友好": 68, "个性化": 72},
    },
}

DEFAULT_STYLE = "现代简约"

# 预算档位：每平米综合单价（元）与标签
BUDGET_LEVELS: dict[str, dict[str, Any]] = {
    "economy": {"label": "经济型", "per_sqm": 1200},
    "standard": {"label": "标准型", "per_sqm": 2000},
    "premium": {"label": "品质型", "per_sqm": 3500},
}

# 费用构成拆分（占比之和应为 1）
COST_SPLIT: list[tuple[str, float]] = [
    ("地面工程", 0.18),
    ("墙面工程", 0.13),
    ("顶面工程", 0.07),
    ("水电改造", 0.14),
    ("定制柜体", 0.20),
    ("门窗工程", 0.10),
    ("家具软装", 0.12),
    ("灯具家电", 0.06),
]


def _resolve_style(style: str | None) -> str:
    """把用户输入的风格归一到预设库中的键；未命中则回退默认风格。"""
    if style and style in STYLE_PRESETS:
        return style
    return DEFAULT_STYLE


def _split_values(text: str | None, fallback: str) -> str:
    """规范化房间构成等自由文本。"""
    text = (text or "").strip()
    return text or fallback


def generate_fallback_design(
    style: str | None,
    area: float | None,
    rooms: str | None,
    budget_level: str,
    requirements: str = "",
) -> dict[str, Any]:
    """核心算法：根据输入产出完整设计方案字典。

    返回字段与 ``Design`` 模型一致，便于直接入库。
    """
    style_key = _resolve_style(style)
    preset = STYLE_PRESETS[style_key]

    # ---- 1. 基础参数归一 ----
    area = float(area) if area and area > 0 else 100.0
    rooms = _split_values(rooms, "3室2厅1卫")
    level = budget_level if budget_level in BUDGET_LEVELS else "standard"
    level_info = BUDGET_LEVELS[level]

    # ---- 2. 预算估算 ----
    total = round(area * level_info["per_sqm"], 2)
    by_category = [
        {
            "category": name,
            "amount": round(total * ratio, 2),
            "ratio": ratio,
        }
        for name, ratio in COST_SPLIT
    ]

    budget = {
        "currency": "CNY",
        "level": level,
        "level_label": level_info["label"],
        "area": area,
        "per_sqm": level_info["per_sqm"],
        "total": total,
        "by_category": by_category,
        "note": f"按建筑面积 {area:.0f}㎡、{level_info['label']}（约 {level_info['per_sqm']} 元/㎡）综合估算，"
        "实际造价随地区、品牌与工艺浮动，仅供参考。",
    }

    # ---- 3. 材料清单 ----
    materials: list[dict[str, Any]] = []
    material_ratio = {
        "地面": 0.18,
        "墙面": 0.13,
        "顶面": 0.07,
        "水电改造": 0.14,
        "定制柜体": 0.20,
        "门窗": 0.10,
        "软装灯具": 0.12,
    }
    for category, (name, spec) in preset["materials"].items():
        materials.append(
            {
                "category": category,
                "name": name,
                "specification": spec,
                "estimated_cost": round(total * material_ratio.get(category, 0.08), 2),
            }
        )

    # ---- 4. 文字方案 ----
    points = preset["design_points"]
    req_line = f"并结合你的额外需求「{requirements.strip()}」做了针对性调整" if requirements.strip() else ""

    summary = (
        f"本方案为 {area:.0f}㎡ 的 {rooms} 户型，采用「{style_key}」风格。"
        f"{preset['tagline']}。整体预算约 {total:,.0f} 元（{level_info['label']}）。"
    )

    layout_plan = (
        f"一、空间动线：以「{rooms}」为基础，主入口设置过渡玄关，客厅与餐厨保持连通，"
        f"形成明确的公区与私区分界{req_line}。\n"
        f"二、功能分区：客餐厅一体化布置，主卧配套衣帽区；次卧/书房采用可变家具兼顾未来需求。\n"
        f"三、收纳系统：沿墙布置通顶收纳，弱化尺度；玄关、走廊等零散空间做嵌入式利用。\n"
        f"四、采光与通风：保留南北通透的优势，尽量少做隔断，让光线纵深贯穿。"
    )

    style_recommendation = (
        f"围绕「{style_key}」的核心理念，落地要点如下：\n"
        + "\n".join(f"• {p}" for p in points)
        + f"\n\n配色建议：以 {preset['palette'][0]['name']} 为主调，"
        f"{preset['palette'][1]['name']} 铺陈大面积，"
        f"{preset['palette'][2]['name']} 与 {preset['palette'][3]['name']} 做点睛之笔。"
    )

    # ---- 5. 图表规格 ----
    chart_spec = {
        "budget_pie": build_budget_pie(budget),
        "material_bar": build_material_bar(materials),
        "style_radar": build_style_radar(preset["radar"]),
    }

    # ---- 6. 3D 户型布局（供前端 Three.js 渲染）----
    layout3d = build_layout3d(area, rooms, preset["palette"])

    return {
        "provider": "算法回退",
        "summary": summary,
        "layout_plan": layout_plan,
        "style_recommendation": style_recommendation,
        "color_palette": preset["palette"],
        "materials": materials,
        "budget": budget,
        "chart_spec": chart_spec,
        "layout3d": layout3d,
    }
