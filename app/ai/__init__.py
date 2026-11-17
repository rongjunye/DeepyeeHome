"""AI 能力包：LLM 提供商抽象、多智能体编排、算法回退引擎。"""

from app.ai.pipeline import generate_design  # noqa: F401  对外统一入口

__all__ = ["generate_design"]
