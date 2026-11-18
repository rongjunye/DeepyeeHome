"""管理后台路由：用户管理与全局统计（仅管理员可访问）。

设计原则：
* 只做「查看 / 启用停用 / 授予或取消管理员」这类可逆操作；
* 不提供删除用户接口，避免误删造成关联项目与方案一并消失。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin
from app.models import Design, Project, User
from app.schemas import AdminStatsOut, AdminUserOut, AdminUserUpdate

router = APIRouter(prefix="/admin", tags=["管理后台"])


def _to_admin_out(user: User) -> AdminUserOut:
    """ORM 用户 -> 后台条目（附带项目数 / 方案数）。"""
    design_count = sum(len(project.designs) for project in user.projects)
    return AdminUserOut(
        id=user.id,
        email=user.email,
        username=user.username,
        is_admin=user.is_admin,
        is_active=user.is_active,
        created_at=user.created_at,
        project_count=len(user.projects),
        design_count=design_count,
    )


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> list[AdminUserOut]:
    """列出全部注册用户（按注册时间倒序）。"""
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [_to_admin_out(user) for user in users]


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> AdminUserOut:
    """启用 / 停用账号，或授予 / 取消管理员权限。"""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 保护当前管理员自己，避免把自己锁在门外
    if user.id == admin.id:
        if payload.is_active is False:
            raise HTTPException(status_code=400, detail="不能停用当前登录的管理员账号")
        if payload.is_admin is False:
            raise HTTPException(status_code=400, detail="不能取消自己的管理员权限")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is not None:
            setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return _to_admin_out(user)


@router.get("/stats", response_model=AdminStatsOut)
def stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> AdminStatsOut:
    """全局统计：用户、项目、方案总量。"""
    return AdminStatsOut(
        total_users=db.scalar(select(func.count(User.id))) or 0,
        active_users=db.scalar(
            select(func.count(User.id)).where(User.is_active.is_(True))
        )
        or 0,
        admin_users=db.scalar(
            select(func.count(User.id)).where(User.is_admin.is_(True))
        )
        or 0,
        total_projects=db.scalar(select(func.count(Project.id))) or 0,
        total_designs=db.scalar(select(func.count(Design.id))) or 0,
    )
