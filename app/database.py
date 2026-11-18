"""数据库连接与会话管理（基于 SQLAlchemy 2.x）。

默认使用 SQLite（文件位于 ``data/neuroarchai.db``）；若把 ``DATABASE_URL``
换成 PostgreSQL/MySQL 连接串，无需改动其余代码。
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# SQLite 在多线程（FastAPI 线程池）下需要关闭 same-thread 检查
_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


class Base(DeclarativeBase):
    """所有 ORM 模型的公共基类。"""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：为每个请求提供独立数据库会话，请求结束后关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_columns() -> None:
    """轻量迁移：给已存在的旧表补齐后续版本新增的列。

    避免升级代码后出现 "no such column"（SQLite 的 create_all 不会改已有表）。
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    statements: list[str] = []

    if "users" in tables:
        existing = {column["name"] for column in inspector.get_columns("users")}
        if "is_admin" not in existing:
            statements.append(
                "ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"
            )
        if "is_active" not in existing:
            statements.append(
                "ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"
            )

    if "projects" in tables:
        existing = {column["name"] for column in inspector.get_columns("projects")}
        if "layout_json" not in existing:
            statements.append("ALTER TABLE projects ADD COLUMN layout_json JSON")

    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def init_db() -> None:
    """建表 + 补齐新增列：应用启动时调用一次（幂等）。"""
    # 延迟导入，确保所有模型都已注册到 Base.metadata
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_columns()
