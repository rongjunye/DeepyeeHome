"""路由包：聚合所有 API 子路由。"""

from fastapi import APIRouter

from app.routers import admin, auth, designs, projects

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(designs.router)
api_router.include_router(admin.router)

__all__ = ["api_router"]
