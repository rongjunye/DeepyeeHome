"""安全工具：密码哈希 + JWT 访问令牌。

密码哈希使用标准库 ``hashlib.pbkdf2_hmac`` 实现，不引入额外依赖，
存储格式为 ``pbkdf2$<rounds>$<salt_b64>$<hash_b64>``。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt  # PyJWT

from app.config import settings

_ALGORITHM = "HS256"
_PBKDF2_ROUNDS = 260_000


def hash_password(password: str) -> str:
    """对明文密码加盐哈希，返回可安全入库的字符串。"""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
    return "pbkdf2${}${}${}".format(
        _PBKDF2_ROUNDS,
        base64.b64encode(salt).decode(),
        base64.b64encode(dk).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    """校验明文密码是否与存储的哈希匹配（常量时间比较）。"""
    try:
        scheme, rounds, salt_b64, hash_b64 = stored.split("$")
        if scheme != "pbkdf2":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(rounds)
        )
        return hmac.compare_digest(dk, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str | int, expires_minutes: int | None = None) -> str:
    """签发 JWT 访问令牌。``subject`` 一般为用户 ID。"""
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """解析并校验 JWT，失败（过期/篡改）返回 ``None``。"""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    except jwt.PyJWTError:
        return None
