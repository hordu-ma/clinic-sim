"""认证相关路由。

提供用户登录、JWT 验证等功能。
"""

from fastapi import APIRouter

router = APIRouter()


# TODO: 实现登录接口
# @router.post("/login")
# async def login(credentials: LoginCredentials):
#     """用户登录。"""
#     pass


# TODO: 实现获取当前用户信息接口
# @router.get("/me")
# async def get_current_user_info(current_user: User = Depends(get_current_user)):
#     """获取当前用户信息。"""
#     pass
