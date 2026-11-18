"""管理员账号命令行工具（创建 / 提升 / 查看）。

用法::

    # 创建管理员（若邮箱已存在则直接提升为管理员）
    python scripts/create_admin.py --email you@example.com --username CAPS --password 'YourPass123'

    # 只把已有用户提升为管理员（不改密码）
    python scripts/create_admin.py --promote you@example.com

    # 查看所有用户
    python scripts/create_admin.py --list
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 让脚本可以直接 import app 包（无需先安装）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.database import SessionLocal, init_db  # noqa: E402
from app.models import User  # noqa: E402
from app.security import hash_password  # noqa: E402

MIN_PASSWORD_LEN = 6


def list_users(db: Session) -> int:
    """打印全部用户。"""
    users = db.scalars(select(User).order_by(User.id)).all()
    if not users:
        print("（暂无用户）")
        return 0

    print(f"{'ID':<5}{'邮箱':<34}{'用户名':<14}{'管理员':<8}{'状态':<8}")
    print("-" * 72)
    for user in users:
        role = "是" if user.is_admin else "否"
        state = "启用" if user.is_active else "停用"
        print(f"{user.id:<5}{user.email:<34}{user.username:<14}{role:<8}{state:<8}")
    return 0


def create_or_promote(
    db: Session,
    email: str,
    username: str | None,
    password: str | None,
    promote_only: bool,
) -> int:
    """创建管理员；邮箱已存在时改为提升（并可选重置密码）。"""
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        if promote_only:
            print(f"未找到邮箱为 {email} 的用户，无法提升。")
            return 1
        if not password:
            print("创建新账号需要提供 --password。")
            return 1
        if len(password) < MIN_PASSWORD_LEN:
            print(f"密码至少需要 {MIN_PASSWORD_LEN} 位。")
            return 1

        user = User(
            email=email,
            username=username or email.split("@")[0],
            hashed_password=hash_password(password),
            is_admin=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"已创建管理员账号：{user.email}（ID {user.id}，用户名 {user.username}）")
        return 0

    changed: list[str] = []
    if not user.is_admin:
        user.is_admin = True
        changed.append("已授予管理员")
    if not user.is_active:
        user.is_active = True
        changed.append("已启用账号")
    if password:
        if len(password) < MIN_PASSWORD_LEN:
            print(f"密码至少需要 {MIN_PASSWORD_LEN} 位。")
            return 1
        user.hashed_password = hash_password(password)
        changed.append("已重置密码")
    if username:
        user.username = username
        changed.append("已更新用户名")

    if changed:
        db.commit()
        print(f"已更新 {user.email}（ID {user.id}）：" + "、".join(changed))
    else:
        print(f"{user.email} 已是管理员，无需修改。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="NeuroArchAI 管理员账号工具")
    parser.add_argument("--email", help="账号邮箱")
    parser.add_argument("--username", help="用户名/昵称")
    parser.add_argument("--password", help="密码（至少 6 位）")
    parser.add_argument("--promote", metavar="EMAIL", help="把已有用户提升为管理员")
    parser.add_argument("--list", action="store_true", help="列出所有用户")
    args = parser.parse_args()

    init_db()  # 确保表与新增列存在

    db = SessionLocal()
    try:
        if args.list:
            return list_users(db)
        if args.promote:
            return create_or_promote(db, args.promote, args.username, args.password, True)
        if args.email:
            return create_or_promote(db, args.email, args.username, args.password, False)

        parser.print_help()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
