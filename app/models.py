"""ORM 数据模型定义。

三张核心表：
* ``User``    —— 用户
* ``Project`` —— 项目（一套户型）
* ``Design``  —— 由 AI 生成的设计方案
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    """统一的 UTC 时间戳。"""
    return datetime.now(timezone.utc)


def _uuid() -> str:
    """生成分享用短令牌。"""
    return uuid.uuid4().hex


class User(Base):
    """用户表。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Project(Base):
    """项目表：一个用户可拥有多个项目（多套户型）。"""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    # 户型图在 uploads/ 中的相对路径
    floorplan_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # 户型元信息：面积、房间数、朝向等（前端表单可填）
    meta_info: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    owner: Mapped["User"] = relationship(back_populates="projects")
    designs: Mapped[list["Design"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Design(Base):
    """设计方案表：一次 AI 生成对应一条记录。"""

    __tablename__ = "designs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)

    # 设计风格，如「现代简约」「北欧」「新中式」
    style: Mapped[str] = mapped_column(String(64), default="现代简约")
    # 实际使用的 AI 引擎：groq / ollama / langgraph / 算法回退
    provider: Mapped[str] = mapped_column(String(32), default="none")

    summary: Mapped[str] = mapped_column(Text, default="")
    layout_plan: Mapped[str] = mapped_column(Text, default="")           # 空间布局建议
    style_recommendation: Mapped[str] = mapped_column(Text, default="")  # 风格设计说明
    color_palette: Mapped[list] = mapped_column(JSON, default=list)      # 配色方案
    materials: Mapped[list] = mapped_column(JSON, default=list)          # 材料清单
    budget: Mapped[dict] = mapped_column(JSON, default=dict)             # 预算估算
    chart_spec: Mapped[dict] = mapped_column(JSON, default=dict)         # Plotly 图表 JSON
    layout3d: Mapped[dict] = mapped_column(JSON, default=dict)           # 3D 户型布局数据

    # 分享
    share_token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=_uuid
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    project: Mapped["Project"] = relationship(back_populates="designs")
