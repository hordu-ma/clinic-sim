"""聊天相关路由。

提供 SSE 流式对话功能。
核心实现：学生问诊，LLM 扮演病人回答。
"""

import json
import time
from collections.abc import AsyncGenerator

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.apps.api.config import settings
from src.apps.api.dependencies import CurrentUser, DbSession
from src.apps.api.logging_config import logger
from src.apps.api.models import Case, Message, Session
from src.apps.api.rate_limit import limiter
from src.apps.api.schemas.chat import ChatRequest

router = APIRouter()

# 系统提示词模板（固定角色约束）
SYSTEM_PROMPT = """你是一名正在看病的普通患者，医生正在给你问诊。

【身份铁律 - 绝对不可违反】
- 你是患者，不是医生、护士或任何医疗人员
- 你来看病是因为身体不舒服，你不懂医学
- 你绝对不能：开药、给建议、做诊断、说"我帮你"、说"给你开药"
- 医生说什么你就听着，最多问"那我该怎么办"或"严重吗"

【回答原则】
1. 只描述自己的症状和感受，不给任何医学意见
2. 只回答医生问的问题，不主动提供信息
3. 用普通人的话说症状，比如"肚子疼"而不是"腹痛"
4. 回答简短自然，一两句话即可
5. 如果医生问你该怎么治，回答"我不懂，您是医生您说了算"
6. 如果医生让你吃药/检查，回答"好的"或"行"即可
【首次回复规则】
- 在你的第一次回答的末尾，附上格式为「（病例序号：XX）」的病例编号（XX 为实际序号）。
- 仅第一次回复需要附带序号，后续回复不再重复。

【诊断终止规则】
- 当用户明确给出最终诊断时，你必须：
  （触发词示例："我的诊断是…"、"最终诊断：…"、"诊断为…"、"初步诊断…"）
  1. 立即退出患者角色扮演
  2. 判断用户的诊断是否与你预设的「初步诊断」一致
     给出判断结果（✔ 正确 / ✖ 不正确，并说明正确诊断）
  3. 完整展示预先生成的病历，格式如下：
     ---
     【预设病历】
     性别：XX
     年龄：XX岁
     职业：XX
     主诉：XX
     现病史：XX
     既往史：XX
     婚育个人史：XX
     家族史：XX
     初步诊断：XX
     ---"""


def build_developer_prompt(case: Case) -> str:
    """构建开发者提示词（包含病例信息）。

    Args:
        case: 病例对象

    Returns:
        开发者提示词字符串
    """
    # 提取体格检查中可透露的信息
    physical_exam = case.physical_exam or {}
    visible_signs = physical_exam.get("visible", {})
    on_request_signs = physical_exam.get("on_request", {})

    # 格式化可见体征
    visible_str = (
        "\n".join(f"  - {k}: {v}" for k, v in visible_signs.items())
        if visible_signs
        else "  - 无明显异常"
    )

    # 格式化按需体征（医生检查时才显示）
    on_request_str = (
        "\n".join(f"  - {k}: {v}" for k, v in on_request_signs.items())
        if on_request_signs
        else "  - 无特殊发现"
    )

    # 提取患者信息
    patient_info = case.patient_info or {}
    age = patient_info.get("age", "未知")
    gender = patient_info.get("gender", "未知")
    occupation = patient_info.get("occupation", "未知")

    # 既往史
    past_history = case.past_history or {}
    diseases = past_history.get("diseases", [])
    allergies = past_history.get("allergies", [])
    medications = past_history.get("medications", [])

    # 婚育个人史和家族史
    marriage_history = getattr(case, "marriage_childbearing_history", None) or "未提供"
    fam_history = getattr(case, "family_history", None) or "未提供"

    # 病例序号
    case_num = getattr(case, "case_number", None)
    case_number_line = f"\n病例序号：{case_num}" if case_num else ""

    # 初步诊断（隐藏信息，仅供终止判断使用）
    std_diag = case.standard_diagnosis or {}
    primary_diag = std_diag.get("primary", "未知")
    differential = std_diag.get("differential", [])

    return f"""你扮演的患者信息：
- 年龄：{age}岁
- 性别：{"男" if gender == "male" else "女" if gender == "female" else gender}
- 职业：{occupation}{case_number_line}

主诉：{case.chief_complaint}

现病史：{case.present_illness}

既往史：
- 疾病史：{", ".join(diseases) if diseases else "无"}
- 过敏史：{", ".join(allergies) if allergies else "无"}
- 用药史：{", ".join(medications) if medications else "无"}

婚育个人史：{marriage_history}

家族史：{fam_history}

可见体征（医生一眼能看到的）：
{visible_str}

体格检查结果（医生检查时你要描述的感受）：
{on_request_str}

【隐藏信息 - 仅用于诊断终止时的比对，不要主动提及】
初步诊断：{primary_diag}
鉴别诊断：{", ".join(differential) if differential else "无"}

【再次强调】你只是一个普通患者：
- 绝对禁止说"我给你开药"、"你需要吃xx药"、"建议你xxx"这类话
- 医生说吃药就说"好的"，医生说检查就说"行"
- 你来看病是求助的，不是给建议的
"""


def build_messages(
    case: Case,
    history: list[Message],
    user_message: str,
) -> list[dict]:
    """构建发送给 LLM 的消息列表。

    Args:
        case: 病例对象
        history: 历史消息列表
        user_message: 用户当前消息

    Returns:
        OpenAI 格式的消息列表
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": build_developer_prompt(case)},
    ]

    # 添加历史消息（最近 20 条）
    recent_history = history[-20:] if len(history) > 20 else history
    for msg in recent_history:
        messages.append(
            {
                "role": msg.role,
                "content": msg.content,
            }
        )

    # 添加当前用户消息
    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    return messages


def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量。

    简单估算：中文约 1.5 字符/token，英文约 4 字符/token
    混合文本取中间值

    Args:
        text: 输入文本

    Returns:
        估算的 token 数
    """
    # 简单方法：字符数 / 2
    return max(1, len(text) // 2)


def estimate_prompt_tokens(messages: list[dict]) -> int:
    """保守估算 prompt token 数。

    Args:
        messages: OpenAI 格式消息列表

    Returns:
        估算的 token 数（偏保守）
    """
    return sum(max(1, len(str(m.get("content", "")))) for m in messages)


@router.post("/")
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    data: ChatRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> StreamingResponse:
    """SSE 流式对话接口。

    学生（医生角色）发送问诊消息，LLM（病人角色）流式返回回答。
    限流：每用户每分钟最多 20 次请求。

    Args:
        request: FastAPI Request 对象（限流需要）
        data: 聊天请求（session_id, message）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        StreamingResponse: SSE 流式响应

    Raises:
        HTTPException: 403 如果用户无权访问会话
        HTTPException: 404 如果会话不存在
        HTTPException: 400 如果会话已结束
    """
    # 1. 查询会话（包含病例和历史消息）
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.case),
            selectinload(Session.messages),
        )
        .where(Session.id == data.session_id)
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # 2. 权限检查
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # 3. 检查会话状态
    if session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is {session.status}, cannot continue chat",
        )

    # 4. 构建消息
    case = session.case
    history = sorted(session.messages, key=lambda m: m.created_at)
    messages = build_messages(case, history, data.message)
    prompt_tokens = estimate_prompt_tokens(messages)
    available_tokens = settings.LLM_MAX_CONTEXT_LEN - prompt_tokens
    if available_tokens < 16:
        logger.warning(
            "上下文过长，无法继续生成",
            session_id=data.session_id,
            prompt_tokens=prompt_tokens,
            max_context=settings.LLM_MAX_CONTEXT_LEN,
        )

        async def over_limit_generator() -> AsyncGenerator[str, None]:
            yield "data: " + json.dumps({"error": "上下文过长，请结束会话或减少消息"}) + "\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            over_limit_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    max_tokens = min(settings.LLM_MAX_TOKENS, available_tokens)

    # 5. 创建 SSE 生成器
    async def event_generator() -> AsyncGenerator[str, None]:
        full_response = ""
        start_time = time.time()
        user_tokens = estimate_tokens(data.message)

        try:
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{settings.LLM_BASE_URL}/v1/chat/completions",
                    json={
                        "model": settings.LLM_MODEL,
                        "messages": messages,
                        "stream": True,
                        "temperature": settings.LLM_TEMPERATURE,
                        "max_tokens": max_tokens,
                    },
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        err_msg = f"LLM error: {error_text.decode()}"
                        yield f"data: {json.dumps({'error': err_msg})}\n\n"
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:]

                            if data_str.strip() == "[DONE]":
                                break

                            try:
                                chunk = json.loads(data_str)
                                content = (
                                    chunk.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if content:
                                    full_response += content
                                    chunk_data = {"content": content, "done": False}
                                    yield f"data: {json.dumps(chunk_data)}\n\n"
                            except json.JSONDecodeError:
                                continue

        except httpx.TimeoutException:
            yield f"data: {json.dumps({'error': 'LLM request timeout'})}\n\n"
            return
        except httpx.RequestError as e:
            yield f"data: {json.dumps({'error': f'LLM connection error: {str(e)}'})}\n\n"
            return

        # 6. 流式结束，发送完成信号
        latency_ms = int((time.time() - start_time) * 1000)
        yield f"data: {json.dumps({'content': '', 'done': True, 'latency_ms': latency_ms})}\n\n"

        # 7. 落库：保存用户消息和助手回复
        if full_response:
            # 使用新的数据库会话来保存消息（避免上下文管理器问题）
            from src.apps.api.dependencies import AsyncSessionLocal

            async with AsyncSessionLocal() as save_db:
                try:
                    # 保存用户消息
                    user_msg = Message(
                        session_id=data.session_id,
                        role="user",
                        content=data.message,
                        tokens=user_tokens,
                    )
                    save_db.add(user_msg)

                    # 保存助手回复
                    assistant_msg = Message(
                        session_id=data.session_id,
                        role="assistant",
                        content=full_response,
                        tokens=estimate_tokens(full_response),
                        latency_ms=latency_ms,
                    )
                    save_db.add(assistant_msg)

                    await save_db.commit()
                    logger.debug(
                        "对话消息已保存",
                        session_id=data.session_id,
                        latency_ms=latency_ms,
                    )
                except Exception as e:
                    # 落库失败不影响用户体验，但应记录日志
                    await save_db.rollback()
                    logger.error(
                        "保存对话消息失败",
                        session_id=data.session_id,
                        error=str(e),
                    )

        # 发送最终的 [DONE] 信号
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )
