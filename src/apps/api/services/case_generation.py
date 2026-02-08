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
import random
from datetime import datetime
from typing import Any

import httpx

from src.apps.api.config import settings
from src.apps.api.exceptions import BusinessError

CASE_GENERATION_PROMPT_VERSION = "2.0"

# 106 种疾病列表（序号 1-106）
DISEASE_LIST: dict[int, str] = {
    1: "慢性阻塞性肺疾病",
    2: "食管癌",
    3: "支气管哮喘",
    4: "气胸",
    5: "胃炎",
    6: "支气管扩张",
    7: "肋骨骨折",
    8: "消化性溃疡",
    9: "肺炎",
    10: "心力衰竭",
    11: "消化道穿孔",
    12: "肺结核",
    13: "心律失常",
    14: "消化道出血",
    15: "肺栓塞",
    16: "冠状动脉性心脏病",
    17: "胃癌",
    18: "肺癌",
    19: "高血压",
    20: "肝硬化",
    21: "呼吸衰竭",
    22: "心脏瓣膜病",
    23: "非酒精性脂肪性肝病",
    24: "急性呼吸窘迫综合征",
    25: "结核性心包炎",
    26: "肝癌",
    27: "胸腔积液",
    28: "胃食管反流病",
    29: "胆石病、胆道感染",
    30: "急性胰腺炎",
    31: "胎盘早剥",
    32: "颈椎病",
    33: "肝脓肿",
    34: "产后出血",
    35: "腰椎间盘突出症",
    36: "胰腺癌",
    37: "盆腔炎性疾病",
    38: "骨关节炎",
    39: "溃疡性结肠炎",
    40: "子宫颈癌",
    41: "系统性红斑狼疑",
    42: "克罗恩病",
    43: "子宫肌瘤",
    44: "类风湿关节炎",
    45: "肠梠阻",
    46: "卵巢肿瘤",
    47: "痛风",
    48: "结直肠癌",
    49: "子宫内膜癌",
    50: "肺炎",
    51: "肠结核",
    52: "子宫内膜异位症",
    53: "腹泻病",
    54: "结核性腹膜炎",
    55: "排卵障碍性子宫出血",
    56: "维生素D缺乏性佝偸病",
    57: "急性阑尾炎",
    58: "缺铁性贫血",
    59: "小儿常见发疑性疾病",
    60: "肛管、直肠良性病变",
    61: "再生障碍性贫血",
    62: "腹外疹",
    63: "急性白血病",
    64: "腹部闭合性损伤",
    65: "淋巴瘤",
    66: "小儿惊厥",
    67: "原发免疫性血小板减少症",
    68: "新生儿黄疸",
    69: "急性肾小球肾炎",
    70: "甲状腺功能亢进症",
    71: "川崎病",
    72: "慢性肾小球肾炎",
    73: "甲状腺功能减退症",
    74: "病毒性肝炎",
    75: "肾病综合征",
    76: "糖尿病",
    77: "细菌性痢疾",
    78: "尿路感染",
    79: "脑出血",
    80: "流行性脑脊髓膜炎",
    81: "尿路结石",
    82: "急性缺血性卒中",
    83: "肾综合征出血热",
    84: "膀胱肿瘤",
    85: "蛛网膜下腔出血",
    86: "艾滋病",
    87: "良性前列腺增生",
    88: "急性硬膜外血肿",
    89: "浅部组织及手部细菌性感染",
    90: "急性肾损伤",
    91: "颅骨骨折",
    92: "急性乳腺炎",
    93: "慢性肾脏病",
    94: "颅底骨折",
    95: "乳腺癌",
    96: "自然流产",
    97: "颅内肿瘤",
    98: "一氧化碳中毒",
    99: "异位妊娠",
    100: "椎管内肿瘤",
    101: "急性有机磷农药中毒",
    102: "子痫前期-子痫",
    103: "四肢骨折",
    104: "镇静催眠药中毒",
    105: "前置胎盘",
    106: "关节脱位",
}


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


def _build_generation_messages(disease_name: str, case_number: int) -> list[dict[str, str]]:
    system = (
        "你是一个临床医学教学用病例生成器。你的任务是根据指定的疾病名称，"
        "生成一个可用于模拟问诊的完整病例，"
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
        "10) recommended_tests 必须从 available_tests[].type 中选择（同一套 test_type）。\n"
        "11) marriage_childbearing_history 为字符串，"
        "描述婚育及个人史（如婚姻状况、生育史、吸烟饮酒等）。\n"
        "12) family_history 为字符串，描述家族史（父母、兄弟姐妹的重大疾病史）。\n\n"
        "输出字段（必须全部包含）：\n"
        "- title, difficulty, department\n"
        "- patient_info{age,gender,occupation}\n"
        "- chief_complaint, present_illness\n"
        "- past_history{diseases[],allergies[],medications[]}\n"
        "- marriage_childbearing_history (字符串)\n"
        "- family_history (字符串)\n"
        "- physical_exam{visible{temperature,pulse,respiration,blood_pressure,"
        "general},on_request{}}\n"
        "- available_tests[{type,name,result{}}]（type 使用："
        "blood_routine/urine_routine/ecg/x_ray/ultrasound/ct 之一）\n"
        "- standard_diagnosis{primary,differential[]}\n"
        "- key_points[]\n"
        "- recommended_tests[]\n"
    )
    user = (
        f"请针对『{disease_name}』（病例序号 {case_number}）生成一个完整的模拟病例。\n"
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

    Randomly selects a disease from the 106-disease list, then asks the LLM
    to generate a complete case for that disease.

    Returns:
        (case_payload, generation_meta)
    """
    case_number = random.randint(1, len(DISEASE_LIST))
    disease_name = DISEASE_LIST[case_number]
    messages = _build_generation_messages(disease_name, case_number)
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

    # 将 case_number 和 disease_name 写入 payload，便于下游落库
    payload["case_number"] = case_number
    # 确保新增字段有默认值
    if "marriage_childbearing_history" not in payload:
        payload["marriage_childbearing_history"] = "未提供"
    if "family_history" not in payload:
        payload["family_history"] = "未提供"

    generation_meta = {
        "generated_at": start.isoformat() + "Z",
        "prompt_version": CASE_GENERATION_PROMPT_VERSION,
        "model": settings.LLM_MODEL,
        "temperature": settings.LLM_CASE_GEN_TEMPERATURE,
        "max_tokens": settings.LLM_CASE_GEN_MAX_TOKENS,
        "retries": settings.LLM_CASE_GEN_RETRIES,
        "case_number": case_number,
        "disease_name": disease_name,
    }
    return payload, generation_meta
