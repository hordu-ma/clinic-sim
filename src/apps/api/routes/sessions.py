from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.apps.api.dependencies import CurrentUser, DbSession
from src.apps.api.models import Case, Message, Score, Session, TestRequest
from src.apps.api.schemas.scores import (
    DiagnosisSubmit,
    DiagnosisSubmitResponse,
    ScoreDimensions,
    ScoreResponse,
    ScoringDetails,
)
from src.apps.api.schemas.sessions import (
    MessageItem,
    SessionCreate,
    SessionDetail,
    SessionListItem,
    SessionListResponse,
    SessionResponse,
)
from src.apps.api.services.case_generation import generate_random_case_payload
from src.apps.api.schemas.tests import (
    TestRequestCreate,
    TestRequestListItem,
    TestRequestListResponse,
    TestRequestResponse,
)
from src.apps.api.services.scoring import ScoringService

router = APIRouter()


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> SessionResponse:
    """创建新的问诊会话。

    Args:
        data: 创建会话请求数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        新创建的会话信息

    Raises:
        HTTPException: 404 如果病例不存在或已禁用
    """
    # 模式分流：fixed / random
    if data.mode == "random":
        payload, meta = await generate_random_case_payload()

        # normalize to avoid UnboundLocal in case of early validation failures
        recommended_tests = payload.get("recommended_tests")

        # 基础校验（尽量轻量，失败则返回 502）
        required_fields = [
            "title",
            "difficulty",
            "department",
            "patient_info",
            "chief_complaint",
            "present_illness",
            "past_history",
            "physical_exam",
            "available_tests",
            "standard_diagnosis",
            "key_points",
        ]
        missing = [f for f in required_fields if f not in payload]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"LLM generated case missing fields: {', '.join(missing)}",
            )

        # recommended_tests 若存在，应与 available_tests.type 保持一致，否则检查申请会失败
        available_test_types = {
            str(t.get("type"))
            for t in (payload.get("available_tests") or [])
            if isinstance(t, dict) and t.get("type")
        }
        if recommended_tests is not None:
            if not isinstance(recommended_tests, list) or not all(
                isinstance(x, str) and x for x in recommended_tests
            ):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="LLM generated case has invalid recommended_tests type",
                )
            unknown = [t for t in recommended_tests if t not in available_test_types]
            if unknown:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=(
                        "LLM generated case has recommended_tests not in available_tests.type: "
                        + ", ".join(unknown)
                    ),
                )

        case = Case(
            title=str(payload["title"]),
            difficulty=str(payload["difficulty"]),
            department=str(payload["department"]),
            patient_info=payload["patient_info"],
            chief_complaint=str(payload["chief_complaint"]),
            present_illness=str(payload["present_illness"]),
            past_history=payload["past_history"],
            physical_exam=payload["physical_exam"],
            available_tests=payload["available_tests"],
            standard_diagnosis=payload["standard_diagnosis"],
            key_points=payload["key_points"],
            recommended_tests=recommended_tests,
            is_active=True,
            source="random",
            generation_meta=meta,
        )
        db.add(case)
        await db.commit()
        await db.refresh(case)

        case_id = case.id
    else:
        if data.case_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="case_id is required when mode=fixed",
            )

        # 检查病例是否存在且启用
        result = await db.execute(
            select(Case).where(Case.id == data.case_id, Case.is_active == True)  # noqa: E712
        )
        case = result.scalar_one_or_none()

        if case is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found or is inactive",
            )
        case_id = data.case_id

    # 创建会话
    session = Session(
        user_id=current_user.id,
        case_id=case_id,
        status="in_progress",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse(
        id=session.id,
        case_id=session.case_id,
        status=session.status,
        started_at=session.started_at,
    )


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    db: DbSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: str | None = Query(None, alias="status", description="状态筛选"),
) -> SessionListResponse:
    """获取用户的会话历史。

    Args:
        db: 数据库会话
        current_user: 当前用户
        skip: 分页偏移
        limit: 每页数量
        status_filter: 可选状态筛选

    Returns:
        会话列表（分页）
    """
    # 构建基础查询
    base_query = select(Session).where(Session.user_id == current_user.id)

    if status_filter:
        base_query = base_query.where(Session.status == status_filter)

    # 获取总数
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar() or 0

    # 获取会话列表（包含病例信息）
    query = (
        base_query.options(selectinload(Session.case))
        .order_by(Session.started_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()

    # 获取每个会话的消息数量
    session_ids = [s.id for s in sessions]
    if session_ids:
        msg_count_result = await db.execute(
            select(Message.session_id, func.count(Message.id).label("message_count"))
            .where(Message.session_id.in_(session_ids))
            .group_by(Message.session_id)
        )
        # row attribute access may collide with dict methods; use indexing for robustness
        msg_counts = {int(row[0]): int(row[1]) for row in msg_count_result}
    else:
        msg_counts = {}

    # 构建响应
    items = [
        SessionListItem(
            id=session.id,
            case_id=session.case_id,
            case_title=session.case.title,
            case_difficulty=session.case.difficulty,
            status=session.status,
            started_at=session.started_at,
            ended_at=session.ended_at,
            message_count=msg_counts.get(session.id, 0),
        )
        for session in sessions
    ]

    return SessionListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> SessionDetail:
    """获取会话详情（包含消息历史）。

    Args:
        session_id: 会话ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        会话详情，包含完整消息历史

    Raises:
        HTTPException: 404 如果会话不存在
        HTTPException: 403 如果用户无权访问
    """
    # 查询会话（包含病例和消息）
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.case),
            selectinload(Session.messages),
        )
        .where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # 权限检查：仅会话所属用户可访问
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # 按时间排序消息
    sorted_messages = sorted(session.messages, key=lambda m: m.created_at)

    return SessionDetail(
        id=session.id,
        case_id=session.case_id,
        case_title=session.case.title,
        case_difficulty=session.case.difficulty,
        status=session.status,
        submitted_diagnosis=session.submitted_diagnosis,
        started_at=session.started_at,
        ended_at=session.ended_at,
        messages=[
            MessageItem(
                id=msg.id,
                role=_normalize_message_role(msg.role),
                content=msg.content,
                tokens=msg.tokens,
                latency_ms=msg.latency_ms,
                created_at=msg.created_at,
            )
            for msg in sorted_messages
        ],
    )


def _normalize_message_role(role: str) -> Literal["user", "assistant"]:
    if role == "user":
        return "user"
    if role == "assistant":
        return "assistant"
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Invalid message role in DB: {role}",
    )


@router.post(
    "/{session_id}/tests",
    response_model=TestRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_test(
    session_id: int,
    data: TestRequestCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> TestRequestResponse:
    """申请检查。

    Args:
        session_id: 会话ID
        data: 检查申请请求数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        检查申请结果

    Raises:
        HTTPException: 404 如果会话不存在
        HTTPException: 403 如果用户无权访问
        HTTPException: 400 如果检查类型无效或会话已结束
        HTTPException: 409 如果检查已申请过
    """
    # 查询会话（包含病例信息）
    result = await db.execute(
        select(Session).options(selectinload(Session.case)).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # 权限检查
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # 检查会话状态
    if session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot request test for a completed session",
        )

    # 验证检查类型是否在病例可用检查中
    available_tests = session.case.available_tests or []
    test_info = None
    for test in available_tests:
        if test.get("type") == data.test_type:
            test_info = test
            break

    if test_info is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid test type: {data.test_type}. Not available for this case.",
        )

    # 检查是否已申请过该检查（可配置允许重复）
    existing_result = await db.execute(
        select(TestRequest).where(
            TestRequest.session_id == session_id,
            TestRequest.test_type == data.test_type,
        )
    )
    existing_test = existing_result.scalar_one_or_none()

    if existing_test is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Test '{data.test_type}' has already been requested for this session",
        )

    # 创建检查申请记录
    test_request = TestRequest(
        session_id=session_id,
        test_type=data.test_type,
        test_name=test_info.get("name", data.test_type),
        result=test_info.get("result", {}),
    )
    db.add(test_request)
    await db.commit()
    await db.refresh(test_request)

    return TestRequestResponse(
        id=test_request.id,
        session_id=test_request.session_id,
        test_type=test_request.test_type,
        test_name=test_request.test_name,
        result=test_request.result,
        requested_at=test_request.requested_at,
    )


@router.get("/{session_id}/tests", response_model=TestRequestListResponse)
async def list_session_tests(
    session_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> TestRequestListResponse:
    """获取会话已申请的检查列表。

    Args:
        session_id: 会话ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        已申请检查列表

    Raises:
        HTTPException: 404 如果会话不存在
        HTTPException: 403 如果用户无权访问
    """
    # 查询会话
    session_result = await db.execute(select(Session).where(Session.id == session_id))
    session = session_result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # 权限检查
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # 查询已申请的检查
    result = await db.execute(
        select(TestRequest)
        .where(TestRequest.session_id == session_id)
        .order_by(TestRequest.requested_at)
    )
    tests = result.scalars().all()

    items = [
        TestRequestListItem(
            id=test.id,
            test_type=test.test_type,
            test_name=test.test_name,
            result=test.result,
            requested_at=test.requested_at,
        )
        for test in tests
    ]

    return TestRequestListResponse(items=items, total=len(items))


@router.post("/{session_id}/submit", response_model=DiagnosisSubmitResponse)
async def submit_diagnosis(
    session_id: int,
    data: DiagnosisSubmit,
    db: DbSession,
    current_user: CurrentUser,
) -> DiagnosisSubmitResponse:
    """提交诊断并获取评分。

    Args:
        session_id: 会话ID
        data: 诊断提交请求数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        提交结果和评分报告

    Raises:
        HTTPException: 404 如果会话不存在
        HTTPException: 403 如果用户无权访问
        HTTPException: 400 如果会话已提交
        HTTPException: 409 如果已有评分记录
    """
    # 查询会话（包含病例、消息、检查申请）
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.case),
            selectinload(Session.messages),
            selectinload(Session.test_requests),
            selectinload(Session.score),
        )
        .where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # 权限检查
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # 检查会话状态
    if session.status != "in_progress":
        # 如果已提交，返回已有评分
        if session.score:
            return DiagnosisSubmitResponse(
                session_id=session.id,
                status=session.status,
                submitted_diagnosis=session.submitted_diagnosis or "",
                score=_build_score_response(session.score),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has already been submitted",
        )

    # 计算评分
    score_result = ScoringService.calculate_score(
        session=session,
        case=session.case,
        messages=list(session.messages),
        test_requests=list(session.test_requests),
        submitted_diagnosis=data.diagnosis,
    )

    # 更新会话状态
    session.status = "submitted"
    session.submitted_diagnosis = data.diagnosis
    session.ended_at = datetime.utcnow()

    # 创建评分记录
    score = Score(
        session_id=session.id,
        total_score=score_result.total_score,
        dimensions=score_result.dimensions,
        scoring_details=score_result.details,
        scoring_method="rule_based",
        model_version=None,
    )
    db.add(score)

    await db.commit()
    await db.refresh(session)
    await db.refresh(score)

    return DiagnosisSubmitResponse(
        session_id=session.id,
        status=session.status,
        submitted_diagnosis=data.diagnosis,
        score=_build_score_response(score),
    )


@router.get("/{session_id}/score", response_model=ScoreResponse)
async def get_session_score(
    session_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ScoreResponse:
    """获取会话评分详情。

    Args:
        session_id: 会话ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        评分详情

    Raises:
        HTTPException: 404 如果会话不存在或未评分
        HTTPException: 403 如果用户无权访问
    """
    # 查询会话（包含评分）
    result = await db.execute(
        select(Session).options(selectinload(Session.score)).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # 权限检查
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # 检查是否有评分
    if session.score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score not found. Please submit diagnosis first.",
        )

    return _build_score_response(session.score)


def _build_score_response(score: Score) -> ScoreResponse:
    """构建评分响应对象。

    Args:
        score: 评分模型对象

    Returns:
        评分响应 schema
    """
    dimensions = score.dimensions or {}
    details = score.scoring_details or {}

    return ScoreResponse(
        id=score.id,
        session_id=score.session_id,
        total_score=float(score.total_score),
        dimensions=ScoreDimensions(
            interview_completeness=dimensions.get("interview_completeness", 0),
            test_appropriateness=dimensions.get("test_appropriateness", 0),
            diagnosis_accuracy=dimensions.get("diagnosis_accuracy", 0),
        ),
        scoring_details=ScoringDetails(
            keywords_asked=details.get("keywords_asked", []),
            key_points_covered=details.get("key_points_covered", []),
            key_points_total=details.get("key_points_total", []),
            tests_requested=details.get("tests_requested", []),
            recommended_tests=details.get("recommended_tests", []),
            diagnosis_keywords_matched=details.get("diagnosis_keywords_matched", []),
            standard_diagnosis=details.get("standard_diagnosis", ""),
            submitted_diagnosis=details.get("submitted_diagnosis", ""),
            scoring_rule_version=details.get("scoring_rule_version", "1.0"),
        ),
        scoring_method=score.scoring_method,
        model_version=score.model_version,
        scored_at=score.scored_at,
    )
