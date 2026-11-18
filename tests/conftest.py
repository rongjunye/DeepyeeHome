"""pytest 全局配置与公共 fixture。

在**任何测试模块导入之前**：
1. 删除旧的测试数据库，保证每次运行都是干净环境；
2. 设置环境变量，让 app.config 读取到测试配置。
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _PROJECT_ROOT / "data" / "test_neuroarchai.db"
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# 每次测试从空库开始，避免残留数据导致断言不稳定
if _DB_PATH.exists():
    _DB_PATH.unlink()

os.environ["LLM_PROVIDER"] = "none"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key-0123456789-abcdefghij-32bytes"


@pytest.fixture(scope="module")
def client():
    """带生命周期的测试客户端（启动时自动建表）。"""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
