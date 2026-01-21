"""Random case generation service.

Generates a full Case payload (including standard answers) via the configured LLM,
so that the random case is:
- consistent for the entire session (stored in DB)
- scorable using the existing rule-based scoring engine

Notes:
- This module intentionally keeps the generation contract aligned with the
  existing Case model fields.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import httpx

from src.apps.api.config import settings
from src.apps.api.exceptions import BusinessError

CASE_GENERATION_PROMPT_VERSION = "1.0"


_CASE_TEST_TYPES = [
    "blood_routine",
    "urine_routine",
    "ecg",
    "x_ray",
    "ultrasound",
    "ct",
]


def _extract_json(text: str) -> str:
    """Extract JSON object from LLM output.

    The generation prompt requests *only JSON*, but some models may wrap it in
    code fences. We tolerate that to improve robustness.
    """

    s = (text or "").strip()
    if not s:
        return s

    # Handle ```json ... ``` or ``` ... ``` wrappers
    if s.startswith("```"):
        # strip leading ```lang
        first_newline = s.find("\n")
        if first_newline != -1:
            s = s[first_newline + 1 :]
        # strip trailing ```
        if s.rstrip().endswith("```"):
            s = s.rstrip()
            s = s[:-3]
        s = s.strip()

    # If there's extra text, try to take the outermost JSON object.
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return s[start : end + 1].strip()
    return s


def _estimate_prompt_tokens(messages: list[dict[str, str]]) -> int:
    """Rough token estimator for OpenAI-style messages.

    We only need a conservative upper bound to avoid vLLM rejecting requests with
    max_tokens that exceed the remaining context window.
    """

    # Use tiktoken if available for a closer estimate (best effort).
    try:
        import tiktoken  # type: ignore

        enc = tiktoken.get_encoding("cl100k_base")
        total = 0
        for m in messages:
            total += len(enc.encode(str(m.get("content", ""))))
            total += 4
        return total
    except Exception:
        # Fallback heuristic.
        total = 0
        for m in messages:
            content = str(m.get("content", ""))
            total += max(1, len(content) // 2)
            total += 4
        return total


def _build_generation_messages() -> list[dict[str, str]]:
    system = (
        "你是一个临床医学教学用病例生成器。你的任务是随机生成一个可用于模拟问诊的病例，"
        "并输出严格的 JSON（不能包含任何额外文本、Markdown、注释）。\n\n"
        "要求：\n"
        "1) 生成内容必须自洽且符合常识（症状、体征、检查结果与诊断匹配）。\n"
        "2) 必须包含可评分信息：standard_diagnosis、key_points、recommended_tests。\n"
        "3) key_points 应该可被学生提问命中（用日常中文短语表达）。\n"
        "4) available_tests 的 type 必须与 recommended_tests 的字符串一致（同一套 test_type）。\n"
        "5) gender 必须为 male/female（便于后端统一处理）。\n"
        "6) difficulty 仅可为 easy/medium/hard。\n"
        "7) 输出必须能被 JSON 解析（必须是严格 JSON，不允许省略逗号、不允许 trailing comma）。\n"
        "8) past_history 必须是对象（dict），包含 diseases/allergies/medications 三个数组字段。\n"
        "9) available_tests[].type 必须是后端可识别的 test_type（例如："
        "blood_routine、x_ray、ct、ultrasound、ecg、urine_routine）。\n"
        "10) recommended_tests 必须从 available_tests[].type 中选择（同一套 test_type）。\n\n"
        "输出字段（必须全部包含）：\n"
        "- title, difficulty, department\n"
        "- patient_info{age,gender,occupation}\n"
        "- chief_complaint, present_illness\n"
        "- past_history{diseases[],allergies[],medications[]}\n"
        "- physical_exam{visible{temperature,pulse,respiration,blood_pressure,"
        "general},on_request{}}\n"
        "- available_tests[{type,name,result{}}]（type 使用："
        "blood_routine/urine_routine/ecg/x_ray/ultrasound/ct 之一）\n"
        "- standard_diagnosis{primary,differential[]}\n"
        "- key_points[]\n"
        "- recommended_tests[]\n"
    )
    user = (
        "请随机生成一个新的病例，偏向常见内科/急诊病种。\n"
        "重要：recommended_tests 必须是 test_type 列表（如 "
        "blood_routine/ecg/x_ray/ct/ultrasound/urine_routine），"
        "不能写检查中文名称。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


async def generate_random_case_payload() -> tuple[dict[str, Any], dict[str, Any]]:
    """Generate a random case payload via LLM.

    Returns:
        (case_payload, generation_meta)
    """
    messages = _build_generation_messages()
    start = datetime.utcnow()

    prompt_tokens = _estimate_prompt_tokens(messages)
    available_tokens = max(0, settings.LLM_MAX_CONTEXT_LEN - prompt_tokens)

    # Cap max_tokens to avoid vLLM 400: max_tokens must fit remaining context.
    # If we don't have enough room, still try a minimal generation so we can
    # return a more actionable error (e.g. JSON decode) instead of hard-failing.
    max_tokens = max(16, min(settings.LLM_CASE_GEN_MAX_TOKENS, available_tokens))

    last_err: Exception | None = None
    for _attempt in range(settings.LLM_CASE_GEN_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
                resp = await client.post(
                    f"{settings.LLM_BASE_URL}/v1/chat/completions",
                    json={
                        "model": settings.LLM_MODEL,
                        "messages": messages,
                        "stream": False,
                        "temperature": settings.LLM_CASE_GEN_TEMPERATURE,
                        "max_tokens": max_tokens,
                        # vLLM supports OpenAI-compatible response_format; this
                        # helps enforce strict JSON output.
                        "response_format": {"type": "json_object"},
                    },
                )
        except httpx.TimeoutException as e:
            last_err = e
            continue
        except httpx.RequestError as e:
            last_err = e
            continue

        if resp.status_code != 200:
            last_err = BusinessError(
                f"LLM 生成病例失败: HTTP {resp.status_code}",
                status_code=502,
            )
            continue

        data = resp.json()
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        if not content:
            last_err = BusinessError("LLM 返回为空，无法生成病例", status_code=502)
            continue

        # First parse attempt
        try:
            payload = json.loads(_extract_json(content))
        except json.JSONDecodeError as e:
            last_err = e
            continue

        # Minimal post-parse normalization to increase downstream success rate.
        # Ensure past_history is an object.
        if not isinstance(payload.get("past_history"), dict):
            payload["past_history"] = {"diseases": [], "allergies": [], "medications": []}

        # Ensure available_tests / recommended_tests use allowed test_type strings.
        if isinstance(payload.get("available_tests"), list):
            for t in payload["available_tests"]:
                if isinstance(t, dict) and "type" in t and isinstance(t["type"], str):
                    if t["type"] not in _CASE_TEST_TYPES:
                        # try a small mapping for common Chinese labels
                        mapping = {
                            "血常规": "blood_routine",
                            "尿常规": "urine_routine",
                            "心电图": "ecg",
                            "胸片": "x_ray",
                            "X光": "x_ray",
                            "X 线": "x_ray",
                            "超声": "ultrasound",
                            "B超": "ultrasound",
                            "CT": "ct",
                        }
                        t["type"] = mapping.get(t["type"], t["type"])

                # Ensure result is an object (dict) for downstream schemas.
                # Some models output a short string; we wrap it.
                if isinstance(t, dict):
                    result = t.get("result")
                    if result is None:
                        t["result"] = {}
                    elif not isinstance(result, dict):
                        t["result"] = {"summary": str(result)}

        if "recommended_tests" in payload and isinstance(payload.get("recommended_tests"), list):
            normalized: list[str] = []
            mapping = {
                "血常规": "blood_routine",
                "全血细胞计数": "blood_routine",
                "尿常规": "urine_routine",
                "心电图": "ecg",
                "胸片": "x_ray",
                "胸部X光片": "x_ray",
                "X光": "x_ray",
                "超声": "ultrasound",
                "B超": "ultrasound",
                "CT": "ct",
            }
            for r in payload["recommended_tests"]:
                if isinstance(r, str):
                    normalized.append(mapping.get(r, r))
            payload["recommended_tests"] = normalized

        break
    else:
        # retries exhausted
        if isinstance(last_err, BusinessError):
            raise last_err
        if isinstance(last_err, httpx.TimeoutException):
            raise BusinessError("LLM 生成病例超时", status_code=504) from last_err
        if isinstance(last_err, httpx.RequestError):
            raise BusinessError(f"LLM 连接失败: {str(last_err)}", status_code=502) from last_err
        if isinstance(last_err, json.JSONDecodeError):
            raise BusinessError(
                "LLM 返回不是合法 JSON，无法生成病例",
                status_code=502,
            ) from last_err
        raise BusinessError("LLM 生成病例失败", status_code=502) from last_err

    generation_meta = {
        "generated_at": start.isoformat() + "Z",
        "prompt_version": CASE_GENERATION_PROMPT_VERSION,
        "model": settings.LLM_MODEL,
        "temperature": settings.LLM_CASE_GEN_TEMPERATURE,
        "max_tokens": settings.LLM_CASE_GEN_MAX_TOKENS,
        "retries": settings.LLM_CASE_GEN_RETRIES,
    }
    return payload, generation_meta
