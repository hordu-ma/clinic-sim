"""评分服务模块。

实现基于规则的评分逻辑，计算问诊完整性、检查合理性、诊断准确性等维度得分。
"""

import re
from dataclasses import dataclass

from src.apps.api.models import Case, Message, Session, TestRequest

# 评分规则版本
SCORING_RULE_VERSION = "1.0"


@dataclass
class ScoreResult:
    """评分结果数据类。"""

    total_score: float
    dimensions: dict
    details: dict


class ScoringService:
    """评分服务类。

    提供基于规则的评分计算功能。
    """

    # 评分权重配置
    WEIGHT_INTERVIEW = 40  # 问诊完整性权重
    WEIGHT_RED_FLAG = 20  # 红旗症状识别权重（目前合并到问诊完整性）
    WEIGHT_TEST = 20  # 检查合理性权重
    WEIGHT_DIAGNOSIS = 20  # 诊断准确性权重

    @classmethod
    def calculate_score(
        cls,
        session: Session,
        case: Case,
        messages: list[Message],
        test_requests: list[TestRequest],
        submitted_diagnosis: str,
    ) -> ScoreResult:
        """计算会话评分。

        Args:
            session: 会话对象
            case: 病例对象
            messages: 消息列表
            test_requests: 检查申请列表
            submitted_diagnosis: 提交的诊断

        Returns:
            评分结果
        """
        # 1. 从对话中提取关键词
        keywords_asked = cls._extract_keywords_from_messages(messages, case)

        # 2. 计算问诊完整性得分
        key_points = case.key_points or []
        interview_score, covered_points = cls._calculate_interview_score(keywords_asked, key_points)

        # 3. 计算检查合理性得分
        recommended_tests = case.recommended_tests or []
        test_score, tests_info = cls._calculate_test_score(test_requests, recommended_tests)

        # 4. 计算诊断准确性得分
        standard_diagnosis = case.standard_diagnosis or {}
        diagnosis_score, matched_keywords = cls._calculate_diagnosis_score(
            submitted_diagnosis, standard_diagnosis
        )

        # 5. 综合计算总分
        total_score = (
            interview_score * cls.WEIGHT_INTERVIEW / 100
            + test_score * cls.WEIGHT_TEST / 100
            + diagnosis_score * cls.WEIGHT_DIAGNOSIS / 100
        )

        # 构建结果
        dimensions = {
            "interview_completeness": round(interview_score, 2),
            "test_appropriateness": round(test_score, 2),
            "diagnosis_accuracy": round(diagnosis_score, 2),
        }

        details = {
            "keywords_asked": keywords_asked,
            "key_points_covered": covered_points,
            "key_points_total": key_points,
            "tests_requested": tests_info["requested"],
            "recommended_tests": recommended_tests,
            "diagnosis_keywords_matched": matched_keywords,
            "standard_diagnosis": standard_diagnosis.get("primary", ""),
            "submitted_diagnosis": submitted_diagnosis,
            "scoring_rule_version": SCORING_RULE_VERSION,
        }

        return ScoreResult(
            total_score=round(total_score, 2),
            dimensions=dimensions,
            details=details,
        )

    @classmethod
    def _extract_keywords_from_messages(cls, messages: list[Message], case: Case) -> list[str]:
        """从消息中提取关键词。

        基于病例的关键点列表，检查对话中是否提及相关内容。

        Args:
            messages: 消息列表
            case: 病例对象

        Returns:
            提取到的关键词列表
        """
        keywords = []
        key_points = case.key_points or []

        # 将所有消息内容合并（仅用户消息，即医生问诊内容）
        user_messages = [msg.content for msg in messages if msg.role == "user"]
        all_content = " ".join(user_messages).lower()

        # 检查每个关键点是否在对话中被提及
        for point in key_points:
            # 将关键点拆分为关键词进行模糊匹配
            point_keywords = cls._extract_point_keywords(point)
            for kw in point_keywords:
                if kw.lower() in all_content:
                    if point not in keywords:
                        keywords.append(point)
                    break

        return keywords

    @classmethod
    def _extract_point_keywords(cls, point: str) -> list[str]:
        """从关键点中提取可匹配的关键词。

        Args:
            point: 关键问诊点

        Returns:
            关键词列表
        """
        # 移除标点和特殊字符
        clean_point = re.sub(r"[（）()、，。？！]", " ", point)
        # 分词（简单按空格和常见分隔符）
        words = clean_point.split()

        # 添加一些同义词映射
        synonyms = {
            "发热": ["发烧", "体温", "高烧", "低烧"],
            "咽痛": ["嗓子疼", "喉咙痛", "咽部"],
            "咳嗽": ["咳", "干咳", "有痰"],
            "头痛": ["头疼", "头晕"],
            "腹痛": ["肚子疼", "腹部"],
            "血压": ["高血压", "低血压"],
            "体征": ["检查", "查体"],
        }

        expanded_keywords = list(words)
        for word in words:
            if word in synonyms:
                expanded_keywords.extend(synonyms[word])

        # 添加原始关键点作为整体匹配
        expanded_keywords.append(point)

        return expanded_keywords

    @classmethod
    def _calculate_interview_score(
        cls, keywords_asked: list[str], key_points: list[str]
    ) -> tuple[float, list[str]]:
        """计算问诊完整性得分。

        Args:
            keywords_asked: 提取到的关键词
            key_points: 病例关键问诊点

        Returns:
            (得分, 覆盖的关键点列表)
        """
        if not key_points:
            return 100.0, []

        covered = [kp for kp in key_points if kp in keywords_asked]
        coverage_rate = len(covered) / len(key_points)
        score = coverage_rate * 100

        return score, covered

    @classmethod
    def _calculate_test_score(
        cls, test_requests: list[TestRequest], recommended_tests: list[str]
    ) -> tuple[float, dict]:
        """计算检查合理性得分。

        评分逻辑：
        - 申请了推荐检查：加分
        - 未申请推荐检查：不扣分（可能有理由）
        - 申请了非推荐检查：轻微扣分（可能过度检查）

        Args:
            test_requests: 检查申请列表
            recommended_tests: 推荐检查列表

        Returns:
            (得分, 检查信息字典)
        """
        requested_types = [tr.test_type for tr in test_requests]

        info = {
            "requested": requested_types,
            "appropriate": [],
            "extra": [],
        }

        if not recommended_tests:
            # 没有推荐检查，只要不过度申请就给满分
            if len(requested_types) <= 2:
                return 100.0, info
            else:
                # 过度检查，每多申请一项扣 10 分
                penalty = (len(requested_types) - 2) * 10
                return max(0, 100 - penalty), info

        # 计算申请的推荐检查数量
        appropriate = [t for t in requested_types if t in recommended_tests]
        extra = [t for t in requested_types if t not in recommended_tests]

        info["appropriate"] = appropriate
        info["extra"] = extra

        # 基础分：覆盖推荐检查的比例
        coverage = len(appropriate) / len(recommended_tests) if recommended_tests else 1.0
        base_score = coverage * 100

        # 过度检查惩罚（每多申请一项非推荐检查扣 5 分）
        penalty = len(extra) * 5

        score = max(0, base_score - penalty)
        return score, info

    @classmethod
    def _calculate_diagnosis_score(
        cls, submitted_diagnosis: str, standard_diagnosis: dict
    ) -> tuple[float, list[str]]:
        """计算诊断准确性得分。

        评分逻辑：
        - 完全匹配主要诊断：100 分
        - 包含主要诊断关键词：80 分
        - 匹配鉴别诊断：60 分
        - 部分相关：40 分
        - 完全不相关：0 分

        Args:
            submitted_diagnosis: 提交的诊断
            standard_diagnosis: 标准诊断

        Returns:
            (得分, 匹配的关键词列表)
        """
        if not standard_diagnosis:
            return 0.0, []

        submitted_lower = submitted_diagnosis.lower()
        matched_keywords = []

        primary = standard_diagnosis.get("primary", "")
        differential = standard_diagnosis.get("differential", [])

        # 检查主要诊断匹配
        if primary:
            primary_lower = primary.lower()
            # 完全匹配
            if primary_lower in submitted_lower or submitted_lower in primary_lower:
                matched_keywords.append(primary)
                return 100.0, matched_keywords

            # 关键词匹配
            primary_keywords = cls._extract_diagnosis_keywords(primary)
            matched_primary = [kw for kw in primary_keywords if kw.lower() in submitted_lower]
            if matched_primary:
                matched_keywords.extend(matched_primary)
                # 匹配关键词数量越多，分数越高
                match_ratio = len(matched_primary) / len(primary_keywords)
                if match_ratio >= 0.5:
                    return 80.0, matched_keywords
                else:
                    return 60.0, matched_keywords

        # 检查鉴别诊断匹配
        for diff in differential:
            diff_lower = diff.lower()
            if diff_lower in submitted_lower or submitted_lower in diff_lower:
                matched_keywords.append(diff)
                return 60.0, matched_keywords

            # 鉴别诊断关键词匹配
            diff_keywords = cls._extract_diagnosis_keywords(diff)
            matched_diff = [kw for kw in diff_keywords if kw.lower() in submitted_lower]
            if matched_diff:
                matched_keywords.extend(matched_diff)
                return 40.0, matched_keywords

        return 0.0, matched_keywords

    @classmethod
    def _extract_diagnosis_keywords(cls, diagnosis: str) -> list[str]:
        """从诊断中提取关键词。

        Args:
            diagnosis: 诊断文本

        Returns:
            关键词列表
        """
        # 移除标点
        clean = re.sub(r"[（）()、，。？！]", " ", diagnosis)
        # 按空格分词
        words = [w.strip() for w in clean.split() if w.strip()]

        # 医学常见词汇不作为关键词
        stop_words = {"急性", "慢性", "型", "性", "期", "症", "病"}
        keywords = [w for w in words if w not in stop_words and len(w) >= 2]

        # 添加原始诊断
        keywords.append(diagnosis)

        return keywords
