"""3D 户型布局生成器。

根据建筑面积与房间构成，用「kd-tree 递归二分」算法把一块矩形地皮切分成
若干矩形房间，输出前端 Three.js 可直接挤压成三维户型图的数据结构。

输出结构::

    {
      "width": 12.5,          # 户型总宽（米，X 轴）
      "depth": 10.0,          # 户型总深（米，Z 轴）
      "wall_height": 2.8,     # 层高（米）
      "area": 125.0,
      "rooms": [
        {"name": "客厅", "x": 0, "z": 0, "w": 4.5, "d": 3.6,
         "area": 16.2, "color": "#C89F6D", "type": "living"}
      ]
    }
"""

from __future__ import annotations

import re
from typing import Any

# 房间类型 -> 基准权重（相对面积占比）
_ROOM_WEIGHTS = {
    "living": 1.70,
    "dining": 1.00,
    "kitchen": 0.85,
    "entry": 0.45,
    "master": 1.40,
    "bedroom": 1.00,
    "bath": 0.50,
    "balcony": 0.50,
}


def parse_room_counts(rooms: str | None) -> dict[str, int]:
    """从「3室2厅1卫」这类文本中解析房间数量，缺失时给合理默认值。"""

    text = rooms or ""

    def grab(keyword: str) -> int:
        match = re.search(rf"(\d+)\s*{keyword}", text)
        return int(match.group(1)) if match else 0

    bedrooms = grab("室") or grab("房")
    livings = grab("厅")
    baths = grab("卫")
    return {
        "bedrooms": bedrooms if bedrooms > 0 else 3,
        "livings": livings if livings > 0 else 2,
        "baths": baths if baths > 0 else 1,
    }


def _build_program(counts: dict[str, int]) -> list[dict[str, Any]]:
    """根据房间数量，生成「房间名 + 类型 + 权重」清单。"""
    program: list[dict[str, Any]] = [{"name": "客厅", "type": "living"}]

    if counts["livings"] >= 2:
        program.append({"name": "餐厅", "type": "dining"})
    program.append({"name": "厨房", "type": "kitchen"})
    program.append({"name": "玄关", "type": "entry"})

    for index in range(counts["bedrooms"]):
        if index == 0:
            program.append({"name": "主卧", "type": "master"})
        else:
            program.append({"name": f"次卧{index}", "type": "bedroom"})

    for index in range(counts["baths"]):
        program.append({"name": f"卫生间{index + 1}", "type": "bath"})

    program.append({"name": "阳台", "type": "balcony"})

    for item in program:
        item["weight"] = _ROOM_WEIGHTS[item["type"]]
    return program


def _split(
    items: list[dict[str, Any]],
    x: float,
    z: float,
    w: float,
    d: float,
    out: list[tuple[dict[str, Any], float, float, float, float]],
) -> None:
    """递归二分：每次沿长边把区域一分为二，直到每个区域只剩一个房间。"""
    if not items:
        return
    if len(items) == 1:
        out.append((items[0], x, z, w, d))
        return

    total = sum(item["weight"] for item in items)
    acc = 0.0
    split_at = 1
    for index, item in enumerate(items):
        acc += item["weight"]
        if acc >= total / 2:
            split_at = index + 1
            break
    split_at = max(1, min(split_at, len(items) - 1))

    head = items[:split_at]
    tail = items[split_at:]
    frac = sum(item["weight"] for item in head) / total
    frac = max(0.12, min(0.88, frac))  # 防止某个房间被压得过于狭长

    if w >= d:
        _split(head, x, z, w * frac, d, out)
        _split(tail, x + w * frac, z, w * (1 - frac), d, out)
    else:
        _split(head, x, z, w, d * frac, out)
        _split(tail, x, z + d * frac, w, d * (1 - frac), out)


def build_layout3d(
    area: float | None,
    rooms: str | None,
    palette: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """生成 3D 户型布局数据。"""
    area = float(area) if area and area > 0 else 100.0
    counts = parse_room_counts(rooms)
    program = _build_program(counts)

    # 户型整体尺寸：按 1.25 : 1 的长宽比，贴合常见住宅
    aspect = 1.25
    width = round((area * aspect) ** 0.5, 2)
    depth = round(area / width, 2)

    # 先按权重把「套内可用面积」分摊（扣掉墙体与公摊的 12%）
    usable = area * 0.88
    program.sort(key=lambda item: item["weight"], reverse=True)
    total_weight = sum(item["weight"] for item in program)
    for item in program:
        item["area"] = usable * item["weight"] / total_weight

    placed: list[tuple[dict[str, Any], float, float, float, float]] = []
    _split(program, 0.0, 0.0, width, depth, placed)

    # 配色：从方案配色循环取色
    hexes = [c.get("hex", "#CCCCCC") for c in (palette or [])] or [
        "#C89F6D",
        "#7FA6A0",
        "#B8BDC4",
        "#8C7BB0",
    ]

    rooms_out: list[dict[str, Any]] = []
    for index, (item, x, z, w, d) in enumerate(placed):
        rooms_out.append(
            {
                "name": item["name"],
                "type": item["type"],
                "x": round(x, 3),
                "z": round(z, 3),
                "w": round(w, 3),
                "d": round(d, 3),
                "area": round(w * d, 2),
                "color": hexes[index % len(hexes)],
            }
        )

    return {
        "width": width,
        "depth": depth,
        "wall_height": 2.8,
        "area": area,
        "rooms": rooms_out,
    }


def layout_from_stored(stored: dict[str, Any] | None) -> dict[str, Any] | None:
    """把用户确认 / AI 识别后保存的归一化布局换算成三维布局（单位：米）。

    ``stored`` 结构::

        {"rooms": [{"name","type","x","y","w","h","color"}],
         "total_width_m": 12.0, "image_aspect": 0.75, "source": "manual"}

    返回 ``None`` 表示没有可用布局（此时调用方应回退到算法推测）。
    """
    if not stored:
        return None

    raw_rooms = stored.get("rooms") or []
    if not raw_rooms:
        return None

    width_m = float(stored.get("total_width_m") or 12.0)
    aspect = float(stored.get("image_aspect") or 0.75)
    depth_m = width_m * aspect

    rooms_out: list[dict[str, Any]] = []
    for index, room in enumerate(raw_rooms):
        try:
            x = float(room["x"])
            y = float(room["y"])
            w = float(room["w"])
            h = float(room["h"])
        except (KeyError, TypeError, ValueError):
            continue
        if w <= 0 or h <= 0:
            continue
        rooms_out.append(
            {
                "name": str(room.get("name") or f"房间{index + 1}"),
                "type": str(room.get("type") or "other"),
                "x": round(x * width_m, 3),
                "z": round(y * depth_m, 3),
                "w": round(w * width_m, 3),
                "d": round(h * depth_m, 3),
                "area": round(w * width_m * h * depth_m, 2),
                "color": room.get("color") or "#C89F6D",
            }
        )

    if not rooms_out:
        return None

    return {
        "width": round(width_m, 2),
        "depth": round(depth_m, 2),
        "wall_height": 2.8,
        "area": round(width_m * depth_m, 2),
        "rooms": rooms_out,
        "source": str(stored.get("source") or "manual"),
    }
