"""FastAPI 应用入口。

负责：初始化数据库、注册 CORS、挂载 API 路由，并托管前端页面。

前端托管策略（自动择优）：
1. 若存在 React 构建产物 ``frontend/dist``，则以 SPA 方式托管它（推荐）；
2. 否则回退到免构建的原生静态页 ``static/``，保证不装 Node 也能跑。
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import BASE_DIR, settings
from app.database import init_db
from app.routers import api_router

STATIC_DIR = BASE_DIR / "static"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表。"""
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="AI 驱动的户型图装修设计助手 —— 上传户型图，生成空间布局、风格方案、3D 预览与预算报告。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- API 路由 ----------------
app.include_router(api_router, prefix="/api")


@app.get("/api/health", tags=["系统"])
def health() -> dict:
    """健康检查，同时返回当前 AI 驱动方式与前端形态，便于排错。"""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": __version__,
        "llm_provider": settings.llm_provider,
        "frontend": "react" if FRONTEND_DIST.is_dir() else "static",
    }


# ---------------- 静态资源 ----------------
# 上传的户型图（只读暴露）
settings.upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")


def _mount_frontend() -> str:
    """挂载前端页面，返回实际使用的形态（react / static / none）。"""
    # 方案一：React 构建产物（SPA），支持前端路由的 history 模式
    if FRONTEND_DIST.is_dir():
        assets_dir = FRONTEND_DIST / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        index_file = FRONTEND_DIST / "index.html"

        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa_fallback(full_path: str) -> FileResponse:
            """静态资源直接返回；其余路径一律交给前端路由。"""
            candidate = FRONTEND_DIST / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(index_file)

        return "react"

    # 方案二：免构建的原生静态页
    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
        return "static"

    return "none"


FRONTEND_MODE = _mount_frontend()
