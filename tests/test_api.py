"""基础单元 / 接口测试。

运行：
    pytest -q

测试前会切换到独立的测试数据库，避免污染开发数据。
"""

from __future__ import annotations

# 环境变量已由 tests/conftest.py 统一设置（独立测试数据库）

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    """提供带生命周期的测试客户端（启动时自动建表）。"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    """注册一个测试用户并返回带令牌的请求头。"""
    resp = client.post(
        "/api/auth/register",
        json={"email": "tester@example.com", "username": "测试员", "password": "secret123"},
    )
    # 若重复运行导致已存在，则改为登录
    if resp.status_code != 201:
        resp = client.post(
            "/api/auth/login",
            json={"email": "tester@example.com", "password": "secret123"},
        )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------
# 基础接口
# --------------------------------------------------------------------------
def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_me(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "tester@example.com"


def test_login_wrong_password(client):
    resp = client.post(
        "/api/auth/login",
        json={"email": "tester@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_unauthorized_project_access(client):
    assert client.get("/api/projects").status_code == 401


# --------------------------------------------------------------------------
# 完整业务闭环：建项目 -> 生成方案 -> 查看 -> 分享
# --------------------------------------------------------------------------
def test_full_design_flow(client, auth_headers):
    # 1) 创建项目
    resp = client.post(
        "/api/projects",
        headers=auth_headers,
        json={
            "title": "测试三居室",
            "description": "南北通透",
            "meta_info": {"area": 110, "rooms": "3室2厅1卫"},
        },
    )
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    # 2) 生成设计方案（LLM_PROVIDER=none -> 走算法引擎）
    resp = client.post(
        f"/api/projects/{project_id}/designs",
        headers=auth_headers,
        json={"style": "北欧", "budget_level": "standard", "requirements": "想要独立书房"},
    )
    assert resp.status_code == 201
    design = resp.json()
    assert design["style"] == "北欧"
    assert design["budget"]["total"] == pytest.approx(110 * 2000)
    assert len(design["color_palette"]) >= 4
    assert "budget_pie" in design["chart_spec"]

    design_id = design["id"]
    token = design["share_token"]

    # 3) 未公开时分享链接不可访问
    assert client.get(f"/api/share/{token}").status_code == 404

    # 4) 开启分享后（无需登录）可访问
    resp = client.patch(
        f"/api/designs/{design_id}/share", headers=auth_headers, json={"is_public": True}
    )
    assert resp.status_code == 200
    assert resp.json()["is_public"] is True

    resp = client.get(f"/api/share/{token}")
    assert resp.status_code == 200
    assert resp.json()["id"] == design_id

    # 5) 方案列表
    resp = client.get(f"/api/projects/{project_id}/designs", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# --------------------------------------------------------------------------
# 算法引擎单测
# --------------------------------------------------------------------------
def test_fallback_engine_budget():
    from app.ai.fallback import generate_fallback_design

    result = generate_fallback_design("新中式", 80, "2室1厅", "premium", "")
    assert result["budget"]["total"] == pytest.approx(80 * 3500)
    assert result["provider"] == "算法回退"
    assert sum(c["ratio"] for c in result["budget"]["by_category"]) == pytest.approx(1.0, abs=0.01)


def test_fallback_engine_unknown_style_defaults():
    from app.ai.fallback import generate_fallback_design

    result = generate_fallback_design("不存在的风格", 100, None, "standard", "")
    # 未知风格回退到默认（现代简约）
    assert "现代简约" in result["summary"]


# --------------------------------------------------------------------------
# 3D 布局 + PDF 报告
# --------------------------------------------------------------------------
def test_layout3d_structure():
    from app.ai.layout3d import build_layout3d

    layout = build_layout3d(120, "3室2厅2卫", [{"name": "主", "hex": "#C89F6D"}])
    assert layout["wall_height"] > 0
    assert len(layout["rooms"]) >= 5
    # 所有房间都应落在户型范围内
    for room in layout["rooms"]:
        assert 0 <= room["x"] <= layout["width"] + 0.01
        assert 0 <= room["z"] <= layout["depth"] + 0.01
        assert room["w"] > 0 and room["d"] > 0


def test_export_pdf_report(client, auth_headers):
    project = client.post(
        "/api/projects",
        headers=auth_headers,
        json={"title": "报告测试", "meta_info": {"area": 90, "rooms": "2室1厅1卫"}},
    ).json()
    design = client.post(
        f"/api/projects/{project['id']}/designs",
        headers=auth_headers,
        json={"style": "奶油风", "budget_level": "premium"},
    ).json()

    # 方案应带 3D 布局数据
    assert design["layout3d"]["rooms"]
    assert design["layout3d"]["wall_height"] == pytest.approx(2.8)

    # 私有报告：需登录
    resp = client.get(f"/api/designs/{design['id']}/report", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content[:4] == b"%PDF"
    assert len(resp.content) > 3000  # 内容不应为空壳

    # 未公开时，公开报告接口不可访问
    assert client.get(f"/api/share/{design['share_token']}/report").status_code == 404

    # 公开后可访问
    client.patch(
        f"/api/designs/{design['id']}/share", headers=auth_headers, json={"is_public": True}
    )
    resp = client.get(f"/api/share/{design['share_token']}/report")
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"
