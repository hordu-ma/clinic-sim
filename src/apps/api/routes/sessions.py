"""会话相关路由。

提供会话创建、查询、历史记录等功能。
"""

from fastapi import APIRouter

router = APIRouter()


# TODO: 实现创建会话接口
# @router.post("/")
# async def create_session(
#     case_id: int,
#     current_user: User = Depends(get_current_user),
# ):
#     """创建新的问诊会话。"""
#     pass


# TODO: 实现会话列表接口
# @router.get("/")
# async def list_sessions(
#     current_user: User = Depends(get_current_user),
#     skip: int = 0,
#     limit: int = 20,
# ):
#     """获取用户的会话历史。"""
#     pass


# TODO: 实现会话详情接口
# @router.get("/{session_id}")
# async def get_session(
#     session_id: int,
#     current_user: User = Depends(get_current_user),
# ):
#     """获取会话详情（包含消息历史）。"""
#     pass


# TODO: 实现提交诊断接口
# @router.post("/{session_id}/submit")
# async def submit_diagnosis(
#     session_id: int,
#     diagnosis: str,
#     current_user: User = Depends(get_current_user),
# ):
#     """提交诊断并触发评分。"""
#     pass


# TODO: 实现申请检查接口
# @router.post("/{session_id}/tests")
# async def request_test(
#     session_id: int,
#     test_type: str,
#     current_user: User = Depends(get_current_user),
# ):
#     """申请检查项目。"""
#     pass


# TODO: 实现查看检查结果接口
# @router.get("/{session_id}/tests")
# async def list_tests(
#     session_id: int,
#     current_user: User = Depends(get_current_user),
# ):
#     """查看已申请的检查项目。"""
#     pass


# TODO: 实现查看评分接口
# @router.get("/{session_id}/score")
# async def get_score(
#     session_id: int,
#     current_user: User = Depends(get_current_user),
# ):
#     """查看会话评分（需已提交诊断）。"""
#     pass
