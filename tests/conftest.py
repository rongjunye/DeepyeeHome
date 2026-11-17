"""pytest 全局配置。

在**任何测试模块导入之前**设置环境变量，确保 app.config 读取到测试配置。
"""

from __future__ import annotations

import os

os.environ["LLM_PROVIDER"] = "none"
os.environ["DATABASE_URL"] = "sqlite:///./data/test_neuroarchai.db"
os.environ["SECRET_KEY"] = "test-secret-key-0123456789-abcdefghij-32bytes"
