"""文件存储服务：校验并保存用户上传的户型图。"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import settings

_CHUNK_SIZE = 1024 * 1024  # 1MB
_ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def _upload_dir() -> Path:
    """确保上传目录存在并返回其路径。"""
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings.upload_dir


def _max_bytes() -> int:
    """单文件体积上限（字节）。"""
    return settings.max_upload_mb * 1024 * 1024


def save_upload(file: UploadFile) -> str:
    """保存上传文件，返回其在 uploads/ 下的相对文件名。

    会校验 MIME 类型、扩展名与体积；任一不合法抛出 HTTPException。
    """
    # 1) 类型校验
    if file.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型：{file.content_type}，仅支持 PNG/JPG/WEBP",
        )

    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_EXT:
        ext = ".png"

    # 2) 随机文件名，避免冲突与路径猜测
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = _upload_dir() / filename

    # 3) 流式写入并限制体积
    size = 0
    try:
        with dest.open("wb") as out:
            while True:
                chunk = file.file.read(_CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > _max_bytes():
                    out.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"文件体积超过 {settings.max_upload_mb}MB 限制",
                    )
                out.write(chunk)
    finally:
        file.file.close()

    return filename


def delete_upload(rel_path: str | None) -> None:
    """删除 uploads/ 下的文件（忽略不存在的情况）。"""
    if not rel_path:
        return
    try:
        (_upload_dir() / rel_path).unlink(missing_ok=True)
    except OSError:
        pass
