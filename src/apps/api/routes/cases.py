"""病例相关路由。

提供病例列表、详情查询等功能。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.api.dependencies import get_current_user, get_db
from src.apps.api.models import Case, User
from src.apps.api.schemas.cases import CaseDetail, CaseDetailFull, CaseListItem
from src.apps.api.schemas.tests import AvailableTestItem, AvailableTestsResponse

router = APIRouter()


@router.get("/", response_model=list[CaseListItem], summary="获取病例列表")
async def list_cases(
    db: Annotated[AsyncSession, Depends(get_db)],
    difficulty: Annotated[str | None, Query(description="难度筛选")] = None,
    department: Annotated[str | None, Query(description="科室筛选")] = None,
    skip: Annotated[int, Query(ge=0, description="跳过记录数")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="返回记录数")] = 20,
) -> list[CaseListItem]:
    """获取病例列表（不含敏感信息）。

    Args:
        db: 数据库会话
        difficulty: 难度筛选（可选）
        department: 科室筛选（可选）
        skip: 跳过记录数
        limit: 返回记录数

    Returns:
        病例列表
    """
    # 构建查询
    query = select(Case).where(Case.is_active == True)  # noqa: E712

    if difficulty:
        query = query.where(Case.difficulty == difficulty)

    if department:
        query = query.where(Case.department == department)

    # 分页
    query = query.offset(skip).limit(limit).order_by(Case.created_at.desc())

    result = await db.execute(query)
    cases = result.scalars().all()

    return [CaseListItem.model_validate(case) for case in cases]


@router.get("/{case_id}", summary="获取病例详情")
async def get_case(
    case_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CaseDetail | CaseDetailFull:
    """获取病例详情。

    学生角色返回基本信息（不含标准答案和关键点）。
    教师/管理员角色返回完整信息。

    Args:
        case_id: 病例ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        病例详情

    Raises:
        HTTPException: 404 病例不存在
    """
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="病例不存在",
        )

    # 根据角色返回不同详情
    if current_user.role in ("teacher", "admin"):
        # 教师和管理员可见完整信息
        return CaseDetailFull.model_validate(case)
    else:
        # 学生仅可见基本信息（不含答案）
        return CaseDetail.model_validate(case)


@router.get(
    "/{case_id}/available-tests",
    response_model=AvailableTestsResponse,
    summary="获取病例可用检查列表",
)
async def get_available_tests(
    case_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> AvailableTestsResponse:
    """获取病例支持的检查项列表（不含结果）。

    用于前端展示可选检查面板。

    Args:
        case_id: 病例ID
        db: 数据库会话
        _current_user: 当前用户（需认证）

    Returns:
        可用检查列表

    Raises:
        HTTPException: 404 病例不存在
    """
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="病例不存在",
        )

    # 提取可用检查（不含结果）
    available_tests = case.available_tests or []
    items = [
        AvailableTestItem(type=test.get("type", ""), name=test.get("name", ""))
        for test in available_tests
        if test.get("type") and test.get("name")
    ]

    return AvailableTestsResponse(case_id=case_id, items=items, total=len(items))
