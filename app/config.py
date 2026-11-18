"""全局配置模块。

配置来源优先级：环境变量 > .env 文件 > 代码默认值。
支持三种 LLM 驱动方式（通过 ``LLM_PROVIDER`` 切换）：

* ``groq``   —— 调用 Groq 云端 API（免费额度、速度快，推荐新手）
* ``ollama`` —— 调用本地 Ollama 服务（数据不出本机，隐私性最好）
* ``none``   —— 不调用大模型，使用内置算法引擎（零配置即可跑通）
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
# app/config.py -> app/ -> 项目根目录
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
UPLOAD_DIR: Path = BASE_DIR / "uploads"

# 确保运行期必需的目录存在（首次启动时自动创建）
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """应用配置项。所有字段可通过同名环境变量覆盖。"""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------------- 基础信息 ----------------
    app_name: str = "NeuroArchAI Platform"
    debug: bool = False

    # ---------------- LLM 提供商 ----------------
    llm_provider: Literal["groq", "ollama", "none"] = "none"

    # Groq 云端
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # Ollama 本地
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"

    # 通用生成参数
    llm_timeout: float = 60.0
    llm_max_tokens: int = 2048

    # 视觉模型（用于识别户型图）；留空则按 provider 取默认
    vision_model: str = ""

    # ---------------- 安全 ----------------
    # 开发默认值；生产环境请在 .env 中替换为随机长字符串（≥32 字节）
    secret_key: str = "change-me-in-production-use-a-long-random-secret-string"
    access_token_expire_minutes: int = 60 * 24 * 7  # 默认 7 天

    # ---------------- 存储 ----------------
    database_url: str = f"sqlite:///{(DATA_DIR / 'neuroarchai.db').as_posix()}"
    upload_dir: Path = UPLOAD_DIR
    max_upload_mb: int = 10
    allowed_image_types: List[str] = [
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
    ]

    # ---------------- 跨域 ----------------
    cors_origins: List[str] = ["*"]

    # 说明：pydantic 的 BaseSettings 不会暴露类上定义的 @property，
    # 因此体积上限直接在业务代码中按 max_upload_mb 换算，避免取值失败。


@lru_cache
def get_settings() -> Settings:
    """返回带缓存的配置单例，避免重复读取 .env。"""
    return Settings()


settings: Settings = get_settings()
