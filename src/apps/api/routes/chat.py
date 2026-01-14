"""聊天相关路由。

提供 SSE 流式对话功能。
"""

from fastapi import APIRouter

router = APIRouter()


# TODO: 实现流式对话接口
# @router.post("/")
# async def chat_stream(
#     session_id: int,
#     message: str,
#     current_user: User = Depends(get_current_user),
# ):
#     """SSE 流式对话接口。"""
#     pass
