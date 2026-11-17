"""Pydantic 数据模型：请求体与响应体的结构与校验规则。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ==========================================================================
# 认证相关
# ==========================================================================
class UserRegister(BaseModel):
    """注册请求体。"""

    email: EmailStr
    username: str = Field(min_length=2, max_length=32, description="昵称")
    password: str = Field(min_length=6, max_length=128, description="密码")


class UserLogin(BaseModel):
    """登录请求体。"""

    email: EmailStr
    password: str


class UserOut(BaseModel):
    """用户信息响应体（不含密码）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    created_at: datetime


class Token(BaseModel):
    """登录成功后返回的令牌。"""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ==========================================================================
# 项目相关
# ==========================================================================
class ProjectCreate(BaseModel):
    """创建项目请求体。"""

    title: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)
    # 户型元信息：{"area": 120, "rooms": 3, "orientation": "南北通透"}
    meta_info: dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """更新项目请求体（字段均可选）。"""

    title: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = Field(default=None, max_length=2000)
    meta_info: Optional[dict[str, Any]] = None


class ProjectOut(BaseModel):
    """项目响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    floorplan_path: Optional[str] = None
    meta_info: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    design_count: int = 0


# ==========================================================================
# 设计方案相关
# ==========================================================================
class DesignGenerateRequest(BaseModel):
    """生成设计方案请求体。"""

    style: str = Field(default="现代简约", max_length=64, description="设计风格")
    rooms: Optional[str] = Field(default=None, max_length=128, description="房间构成，如 3室2厅")
    area: Optional[float] = Field(default=None, ge=10, le=2000, description="建筑面积（㎡）")
    budget_level: str = Field(default="standard", description="预算档位：economy/standard/premium")
    requirements: str = Field(default="", max_length=2000, description="额外需求描述")


class ColorSwatch(BaseModel):
    """配色色块。"""

    name: str
    hex: str


class MaterialItem(BaseModel):
    """材料清单条目。"""

    category: str
    name: str
    specification: str = ""
    estimated_cost: float = 0.0


class DesignOut(BaseModel):
    """设计方案完整响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    style: str
    provider: str
    summary: str
    layout_plan: str
    style_recommendation: str
    color_palette: List[ColorSwatch] = Field(default_factory=list)
    materials: List[MaterialItem] = Field(default_factory=list)
    budget: dict[str, Any] = Field(default_factory=dict)
    chart_spec: dict[str, Any] = Field(default_factory=dict)
    layout3d: dict[str, Any] = Field(default_factory=dict)
    share_token: str
    is_public: bool
    created_at: datetime


class DesignListItem(BaseModel):
    """设计方案列表项（精简版）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    style: str
    provider: str
    summary: str
    is_public: bool
    share_token: str
    created_at: datetime


class ShareUpdate(BaseModel):
    """分享设置请求体。"""

    is_public: bool
