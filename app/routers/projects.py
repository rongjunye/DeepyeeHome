"""项目路由：项目的增删改查与户型图上传。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Project, User
from app.schemas import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.storage import delete_upload, save_upload

router = APIRouter(prefix="/projects", tags=["项目"])


def _to_out(project: Project) -> ProjectOut:
    """ORM -> 响应模型，附带方案数量。"""
    return ProjectOut(
        id=project.id,
        title=project.title,
        description=project.description or "",
        floorplan_path=project.floorplan_path,
        meta_info=project.meta_info or {},
        created_at=project.created_at,
        design_count=len(project.designs),
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
