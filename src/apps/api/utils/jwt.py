"""JWT 令牌工具。"""

from datetime import UTC, datetime, timedelta

import jwt

from src.apps.api.config import settings


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建 JWT access token。

    Args:
        data: 要编码的数据（通常包含 sub: user_id）
        expires_delta: 过期时间间隔

    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
