"""本地开发启动脚本。

用法::

    python run.py

默认监听 http://127.0.0.1:8000 ，开启热重载。
"""

from __future__ import annotations

import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.debug,
    )
