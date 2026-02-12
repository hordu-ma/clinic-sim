"""Test intent parsing and formatting.

This module supports the "option 2" UX:
- doctors can order tests via natural language in chat
- the system auto-creates TestRequest records and returns the report

We intentionally keep it lightweight (regex/keyword) for determinism and auditability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TestIntent:
    kind: str  # "order" | "result"
    test_types: list[str]


_ORDER_VERBS = (
    "做",
    "查",
    "开",
    "申请",
    "安排",
    "先做",
    "去做",
    "做个",
    "做一下",
    "查一下",
)

_RESULT_WORDS = ("结果", "报告", "片子", "片", "单")


def extract_test_intent(message: str, available_test_types: set[str]) -> TestIntent | None:
    """Extract a test intent from a doctor's message.

    Args:
        message: raw user message
        available_test_types: test_type allowed by current case

    Returns:
        TestIntent or None
    """
    text = (message or "").strip()
    if not text:
        return None

    normalized = text.lower()

    # Keyword mapping (cn + en variants) -> canonical test_type.
    keyword_to_type: list[tuple[str, str]] = [
        ("血常规", "blood_routine"),
        ("血常", "blood_routine"),
        ("尿常规", "urine_routine"),
        ("尿常", "urine_routine"),
        ("心电", "ecg"),
        ("ecg", "ecg"),
        ("超声", "ultrasound"),
        ("b超", "ultrasound"),
        ("b 超", "ultrasound"),
        ("x光", "x_ray"),
        ("x-ray", "x_ray"),
        ("x ray", "x_ray"),
        ("胸片", "x_ray"),
        ("ct", "ct"),
    ]

    matched: list[str] = []
    for kw, test_type in keyword_to_type:
        if kw in normalized and test_type in available_test_types and test_type not in matched:
            matched.append(test_type)

    if not matched:
        return None

    # Heuristics: asking for results vs ordering.
    wants_result = any(w in text for w in _RESULT_WORDS)

    if wants_result:
        return TestIntent(kind="result", test_types=matched)

    # Ordering: require a verb-ish signal to avoid accidental triggers.
    if any(v in text for v in _ORDER_VERBS) or re.search(
        r"(做|查).{0,6}(ct|血常规|尿常规|心电|超声|胸片|x光)", text, re.IGNORECASE
    ):
        return TestIntent(kind="order", test_types=matched)

    return None


def format_test_result_text(test_name: str, result: dict) -> str:
    """Format a test result dict into a readable text block."""
    if not result:
        return f"[检查结果] {test_name}: 无异常"

    # Prefer pretty JSON for nested structures.
    lines: list[str] = []
    for key, value in result.items():
        if isinstance(value, (dict, list)):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")

    joined = "\n".join(lines)
    return f"[检查结果] {test_name}:\n{joined}"
