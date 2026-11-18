"""项目路由：项目的增删改查、户型图上传、真实户型标注。"""

from __future__ import annotations

import math

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.layout3d import layout_from_stored
from app.ai.vision import recognize_layout, vision_available
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Project, User
from app.schemas import ProjectCreate, ProjectLayout, ProjectOut, ProjectUpdate
from app.services.storage import delete_upload, save_upload

router = APIRouter(prefix="/projects", tags=["项目"])


def _to_out(project: Project) -> ProjectOut:
    """ORM -> 响应模型，附带方案数量与是否已标注户型。"""
    stored = project.layout_json or {}
    return ProjectOut(
        id=project.id,
        title=project.title,
        description=project.description or "",
        floorplan_path=project.floorplan_path,
        meta_info=project.meta_info or {},
        created_at=project.created_at,
        design_count=len(project.designs),
        has_layout=bool(stored.get("rooms")),
    )


def get_owned_project(db: Session, project_id: int, user: User) -> Project:
    """获取属于当前用户的项目，否则 404（不泄露存在性）。"""
    project = db.get(Project, project_id)
    if project is None or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="项目不存在或无权访问")
    return project


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectOut:
    """新建项目。"""
    project = Project(
        owner_id=user.id,
        title=payload.title,
        description=payload.description,
        meta_info=payload.meta_info,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _to_out(project)


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProjectOut]:
    """列出当前用户的所有项目（按创建时间倒序）。"""
    projects = db.scalars(
        select(Project).where(Project.owner_id == user.id).order_by(Project.created_at.desc())
    ).all()
    return [_to_out(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectOut:
    """获取项目详情。"""
    return _to_out(get_owned_project(db, project_id, user))


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectOut:
    """局部更新项目信息。"""
    project = get_owned_project(db, project_id, user)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is not None:
            setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return _to_out(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """删除项目及其所有方案与户型图。"""
    project = get_owned_project(db, project_id, user)
    delete_upload(project.floorplan_path)
    db.delete(project)
    db.commit()


@router.post("/{project_id}/floorplan", response_model=ProjectOut)
def upload_floorplan(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectOut:
    """上传/替换项目户型图。"""
    project = get_owned_project(db, project_id, user)
    old_path = project.floorplan_path
    project.floorplan_path = save_upload(file)
    db.commit()
    db.refresh(project)
    delete_upload(old_path)  # 换图后清理旧文件
    return _to_out(project)


# --------------------------------------------------------------------------
# 真实户型布局：读取 / 保存 / 清除 / AI 识别
# --------------------------------------------------------------------------
_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


@router.get("/{project_id}/layout", response_model=ProjectLayout)
def get_layout(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectLayout:
    """读取项目已保存的户型标注（未标注时返回空布局）。"""
    project = get_owned_project(db, project_id, user)
    stored = project.layout_json or {}
    if not stored.get("rooms"):
        return ProjectLayout()
    return ProjectLayout(**stored)


@router.put("/{project_id}/layout", response_model=ProjectOut)
def save_layout(
    project_id: int,
    payload: ProjectLayout,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectOut:
    """保存用户确认后的户型标注。"""
    project = get_owned_project(db, project_id, user)
    project.layout_json = payload.model_dump()
    db.commit()
    db.refresh(project)
    return _to_out(project)


@router.delete("/{project_id}/layout", status_code=status.HTTP_204_NO_CONTENT)
def clear_layout(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """清除户型标注（之后生成的方案会回退到算法推测）。"""
    project = get_owned_project(db, project_id, user)
    project.layout_json = {}
    db.commit()


@router.post("/{project_id}/recognize", response_model=ProjectLayout)
def recognize_floorplan(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectLayout:
    """用视觉模型识别户型图，返回建议布局（不自动保存，等用户微调后 PUT 保存）。"""
    project = get_owned_project(db, project_id, user)

    if not project.floorplan_path:
        raise HTTPException(status_code=400, detail="请先上传户型图")

    image_path = settings.upload_dir / project.floorplan_path
    if not image_path.exists():
        raise HTTPException(status_code=400, detail="户型图文件不存在，请重新上传")

    if not vision_available():
        raise HTTPException(
            status_code=400,
            detail="当前未配置视觉模型（LLM_PROVIDER=none 或缺少 API Key），请改用手动标注",
        )

    from PIL import Image

    try:
        with Image.open(image_path) as image:
            aspect = image.height / image.width if image.width else 0.75
    except Exception:  # noqa: BLE001
        aspect = 0.75
    aspect = min(max(aspect, 0.1), 10.0)

    mime = _MIME_BY_SUFFIX.get(image_path.suffix.lower(), "image/png")
    result = recognize_layout(image_path.read_bytes(), mime)
    if not result:
        raise HTTPException(
            status_code=502,
            detail="识别失败：模型未返回可用结果，请手动标注",
        )

    # 用项目面积反推真实总宽，让米制尺寸更贴近实际
    raw_area = (project.meta_info or {}).get("area")
    if raw_area:
        try:
            width_m = math.sqrt(float(raw_area) / aspect)
            result["total_width_m"] = round(min(max(width_m, 2.0), 100.0), 2)
        except (TypeError, ValueError):
            pass

    result["image_aspect"] = round(aspect, 4)
    return ProjectLayout(**result)
