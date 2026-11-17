"""设计方案路由：生成、查询、分享、删除。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import generate_design
from app.database import get_db
from app.deps import get_current_user
from app.models import Design, Project, User
from app.routers.projects import get_owned_project
from app.schemas import DesignGenerateRequest, DesignListItem, DesignOut, ShareUpdate
from app.services.report import build_design_report

router = APIRouter(tags=["设计方案"])

_PDF_MEDIA = "application/pdf"


def _pdf_response(pdf_bytes: bytes, design_id: int) -> Response:
    """把 PDF 字节流包装成可下载的响应。"""
    return Response(
        content=pdf_bytes,
        media_type=_PDF_MEDIA,
        headers={
            "Content-Disposition": f'attachment; filename="NeuroArchAI-design-{design_id}.pdf"'
        },
    )


def get_owned_design(db: Session, design_id: int, user: User) -> Design:
    """获取属于当前用户的方案，否则 404。"""
    design = db.get(Design, design_id)
    if design is None:
        raise HTTPException(status_code=404, detail="方案不存在或无权访问")
    project = db.get(Project, design.project_id)
    if project is None or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="方案不存在或无权访问")
    return design


@router.post(
    "/projects/{project_id}/designs",
    response_model=DesignOut,
    status_code=status.HTTP_201_CREATED,
)
def create_design(
    project_id: int,
    payload: DesignGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Design:
    """为指定项目生成一套 AI 设计方案。

    面积/房间等参数缺省时，自动回退到项目元信息。
    """
    project = get_owned_project(db, project_id, user)
    meta = project.meta_info or {}

    area = payload.area or meta.get("area")
    rooms = payload.rooms or meta.get("rooms")

    result = generate_design(
        style=payload.style,
        area=area,
        rooms=rooms,
        budget_level=payload.budget_level,
        requirements=payload.requirements,
    )

    design = Design(
        project_id=project.id,
        style=payload.style,
        provider=result["provider"],
        summary=result["summary"],
        layout_plan=result["layout_plan"],
        style_recommendation=result["style_recommendation"],
        color_palette=result["color_palette"],
        materials=result["materials"],
        budget=result["budget"],
        chart_spec=result["chart_spec"],
        layout3d=result.get("layout3d", {}),
    )
    db.add(design)
    db.commit()
    db.refresh(design)
    return design


@router.get("/projects/{project_id}/designs", response_model=list[DesignListItem])
def list_designs(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Design]:
    """列出某项目下的所有方案。"""
    project = get_owned_project(db, project_id, user)
    return list(
        db.scalars(
            select(Design)
            .where(Design.project_id == project.id)
            .order_by(Design.created_at.desc())
        ).all()
    )


@router.get("/designs/{design_id}", response_model=DesignOut)
def get_design(
    design_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Design:
    """获取方案详情。"""
    return get_owned_design(db, design_id, user)


@router.patch("/designs/{design_id}/share", response_model=DesignOut)
def update_share(
    design_id: int,
    payload: ShareUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Design:
    """开启 / 关闭方案的公开分享。"""
    design = get_owned_design(db, design_id, user)
    design.is_public = payload.is_public
    db.commit()
    db.refresh(design)
    return design


@router.delete("/designs/{design_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_design(
    design_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """删除方案。"""
    design = get_owned_design(db, design_id, user)
    db.delete(design)
    db.commit()


@router.get("/share/{share_token}", response_model=DesignOut)
def view_shared_design(share_token: str, db: Session = Depends(get_db)) -> Design:
    """公开访问分享的方案（无需登录，仅限已开启公开的）。"""
    design = db.scalar(select(Design).where(Design.share_token == share_token))
    if design is None or not design.is_public:
        raise HTTPException(status_code=404, detail="分享不存在或已关闭")
    return design


# --------------------------------------------------------------------------
# PDF 报告导出
# --------------------------------------------------------------------------
@router.get("/designs/{design_id}/report", response_class=Response)
def export_design_report(
    design_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    """导出方案 PDF 报告（需登录，仅限本人方案）。"""
    design = get_owned_design(db, design_id, user)
    project = db.get(Project, design.project_id)
    pdf_bytes = build_design_report(design, project)
    return _pdf_response(pdf_bytes, design.id)


@router.get("/share/{share_token}/report", response_class=Response)
def export_shared_report(share_token: str, db: Session = Depends(get_db)) -> Response:
    """导出已公开方案的 PDF 报告（无需登录）。"""
    design = db.scalar(select(Design).where(Design.share_token == share_token))
    if design is None or not design.is_public:
        raise HTTPException(status_code=404, detail="分享不存在或已关闭")
    project = db.get(Project, design.project_id)
    pdf_bytes = build_design_report(design, project)
    return _pdf_response(pdf_bytes, design.id)
