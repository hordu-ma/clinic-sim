"""病例相关路由。

提供病例列表、详情查询等功能。
"""

from fastapi import APIRouter

router = APIRouter()


# TODO: 实现病例列表接口
# @router.get("/")
# async def list_cases(
#     difficulty: str | None = None,
#     department: str | None = None,
#     skip: int = 0,
#     limit: int = 20,
# ):
#     """获取病例列表。"""
#     pass


# TODO: 实现病例详情接口
# @router.get("/{case_id}")
# async def get_case(case_id: int, current_user: User = Depends(get_current_user)):
#     """获取病例详情（根据用户角色过滤敏感信息）。"""
#     pass
