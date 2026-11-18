"""管理后台与账号安全相关测试。"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.models import User


def _auth(client, email: str, password: str = "secret123") -> dict[str, str]:
    """注册（或已存在则登录）并返回带令牌的请求头。"""
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "username": email.split("@")[0], "password": password},
    )
    if resp.status_code != 201:
        resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code in (200, 201), resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _promote(email: str) -> None:
    """直接把某个用户标记为管理员（模拟后台授权）。"""
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None, f"用户 {email} 不存在"
        user.is_admin = True
        db.commit()
    finally:
        db.close()


# --------------------------------------------------------------------------
# 权限边界
# --------------------------------------------------------------------------
def test_admin_endpoints_reject_normal_user(client):
    headers = _auth(client, "normal-user@example.com")
    assert client.get("/api/admin/users", headers=headers).status_code == 403
    assert client.get("/api/admin/stats", headers=headers).status_code == 403


def test_admin_endpoints_reject_anonymous(client):
    assert client.get("/api/admin/users").status_code == 401


def test_me_reports_role(client):
    headers = _auth(client, "role-check@example.com")
    body = client.get("/api/auth/me", headers=headers).json()
    assert body["is_admin"] is False
    assert body["is_active"] is True


# --------------------------------------------------------------------------
# 管理员功能
# --------------------------------------------------------------------------
def test_admin_list_users_and_stats(client):
    headers = _auth(client, "boss@example.com")
    _promote("boss@example.com")

    resp = client.get("/api/admin/users", headers=headers)
    assert resp.status_code == 200
    users = resp.json()
    assert any(u["email"] == "boss@example.com" and u["is_admin"] for u in users)

    stats = client.get("/api/admin/stats", headers=headers).json()
    assert stats["total_users"] >= 1
    assert stats["admin_users"] >= 1
    assert stats["active_users"] >= 1


def test_admin_can_disable_and_reenable_user(client):
    admin = _auth(client, "boss2@example.com")
    _promote("boss2@example.com")

    victim = _auth(client, "victim@example.com")
    victim_id = client.get("/api/auth/me", headers=victim).json()["id"]

    # 停用
    resp = client.patch(
        f"/api/admin/users/{victim_id}", headers=admin, json={"is_active": False}
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # 停用后无法登录
    resp = client.post(
        "/api/auth/login", json={"email": "victim@example.com", "password": "secret123"}
    )
    assert resp.status_code == 403

    # 停用后，旧令牌也应立即失效
    assert client.get("/api/auth/me", headers=victim).status_code == 403

    # 恢复
    resp = client.patch(
        f"/api/admin/users/{victim_id}", headers=admin, json={"is_active": True}
    )
    assert resp.json()["is_active"] is True
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "victim@example.com", "password": "secret123"},
        ).status_code
        == 200
    )


def test_admin_cannot_lock_self_out(client):
    headers = _auth(client, "boss3@example.com")
    _promote("boss3@example.com")
    my_id = client.get("/api/auth/me", headers=headers).json()["id"]

    assert (
        client.patch(
            f"/api/admin/users/{my_id}", headers=headers, json={"is_active": False}
        ).status_code
        == 400
    )
    assert (
        client.patch(
            f"/api/admin/users/{my_id}", headers=headers, json={"is_admin": False}
        ).status_code
        == 400
    )


def test_admin_update_missing_user(client):
    headers = _auth(client, "boss4@example.com")
    _promote("boss4@example.com")
    assert (
        client.patch(
            "/api/admin/users/999999", headers=headers, json={"is_active": False}
        ).status_code
        == 404
    )


# --------------------------------------------------------------------------
# 修改密码
# --------------------------------------------------------------------------
def test_change_password_flow(client):
    email = "pw-user@example.com"
    headers = _auth(client, email, password="secret123")

    # 原密码错误
    assert (
        client.post(
            "/api/auth/change-password",
            headers=headers,
            json={"old_password": "wrong", "new_password": "another123"},
        ).status_code
        == 400
    )

    # 正常修改
    resp = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"old_password": "secret123", "new_password": "brandnew123"},
    )
    assert resp.status_code == 204

    # 旧密码失效、新密码可用
    assert (
        client.post(
            "/api/auth/login", json={"email": email, "password": "secret123"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login", json={"email": email, "password": "brandnew123"}
        ).status_code
        == 200
    )
