"""真实户型布局相关测试（标注保存 / 3D 采用 / AI 识别降级）。"""

from __future__ import annotations

import io

import pytest
from PIL import Image


def _auth(client, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "username": "layout_tester", "password": "secret123"},
    )
    if resp.status_code != 201:
        resp = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _project(client, headers) -> dict:
    return client.post(
        "/api/projects",
        headers=headers,
        json={"title": "布局测试", "meta_info": {"area": 100, "rooms": "3室2厅1卫"}},
    ).json()


def _png_bytes() -> io.BytesIO:
    buffer = io.BytesIO()
    Image.new("RGB", (200, 160), "white").save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def test_layout_roundtrip(client):
    headers = _auth(client, "layout-user@example.com")
    project = _project(client, headers)
    pid = project["id"]
    assert project["has_layout"] is False

    payload = {
        "rooms": [
            {"name": "客厅", "type": "living", "x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5},
            {"name": "主卧", "type": "master", "x": 0.5, "y": 0.0, "w": 0.5, "h": 0.5},
        ],
        "total_width_m": 10,
        "image_aspect": 0.8,
        "source": "manual",
    }
    resp = client.put(f"/api/projects/{pid}/layout", headers=headers, json=payload)
    assert resp.status_code == 200
    assert resp.json()["has_layout"] is True

    got = client.get(f"/api/projects/{pid}/layout", headers=headers).json()
    assert len(got["rooms"]) == 2
    assert got["rooms"][0]["name"] == "客厅"
    assert got["total_width_m"] == 10

    # 清除后回到未标注
    assert client.delete(f"/api/projects/{pid}/layout", headers=headers).status_code == 204
    assert client.get(f"/api/projects/{pid}/layout", headers=headers).json()["rooms"] == []


def test_design_uses_stored_layout(client):
    headers = _auth(client, "layout-design@example.com")
    pid = _project(client, headers)["id"]

    client.put(
        f"/api/projects/{pid}/layout",
        headers=headers,
        json={
            "rooms": [
                {"name": "客厅", "type": "living", "x": 0.0, "y": 0.0, "w": 0.5, "h": 1.0},
                {"name": "卧室", "type": "bedroom", "x": 0.5, "y": 0.0, "w": 0.5, "h": 1.0},
            ],
            "total_width_m": 8,
            "image_aspect": 1.0,
            "source": "manual",
        },
    )

    design = client.post(
        f"/api/projects/{pid}/designs",
        headers=headers,
        json={"style": "北欧", "budget_level": "standard"},
    ).json()

    layout = design["layout3d"]
    assert layout["source"] == "manual"
    assert len(layout["rooms"]) == 2
    assert layout["width"] == pytest.approx(8)
    assert layout["depth"] == pytest.approx(8)
    # 左右各占一半：宽 4 米，第二个房间从 x=4 开始
    assert layout["rooms"][0]["w"] == pytest.approx(4.0)
    assert layout["rooms"][1]["x"] == pytest.approx(4.0)


def test_design_falls_back_without_layout(client):
    """没有标注时仍应正常生成（回退到算法推测）。"""
    headers = _auth(client, "layout-fallback@example.com")
    pid = _project(client, headers)["id"]

    design = client.post(
        f"/api/projects/{pid}/designs",
        headers=headers,
        json={"style": "现代简约", "budget_level": "standard"},
    ).json()

    assert design["layout3d"]["rooms"], "应回退到算法生成的房间"
    assert design["layout3d"].get("source") != "manual"


def test_recognize_without_floorplan(client):
    headers = _auth(client, "layout-noplan@example.com")
    pid = _project(client, headers)["id"]
    resp = client.post(f"/api/projects/{pid}/recognize", headers=headers)
    assert resp.status_code == 400
    assert "户型图" in resp.json()["detail"]


def test_recognize_without_vision_config(client):
    """未配置视觉模型时应给出明确提示，而不是 500。"""
    headers = _auth(client, "layout-novision@example.com")
    pid = _project(client, headers)["id"]

    upload = client.post(
        f"/api/projects/{pid}/floorplan",
        headers=headers,
        files={"file": ("plan.png", _png_bytes(), "image/png")},
    )
    assert upload.status_code == 200

    resp = client.post(f"/api/projects/{pid}/recognize", headers=headers)
    assert resp.status_code == 400
    assert "视觉模型" in resp.json()["detail"]