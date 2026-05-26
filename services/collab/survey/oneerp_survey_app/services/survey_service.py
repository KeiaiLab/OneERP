"""설문 서비스 — 설문 생성, 배포, 응답 제출, 결과 집계 비즈니스 로직.

SC-SVY-001~009: 설문 전체 플로우.
EX-SVY-001~012: 예외/에지 케이스 처리.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from statistics import mean, median
from typing import Any, cast

from oneerp_core.errors import (
    raise_bad_request,
    raise_not_found,
    raise_unprocessable,
)
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 상태 전이 규칙
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["active", "archived"],
    "active": ["closed"],
    "closed": ["archived"],
    "archived": [],
}

# 익명 보호 최소 그룹 인원
_ANON_MIN_GROUP_SIZE = 10


class SurveyService:
    """설문 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._survey_repo = Repository("surveys", tenant_id=tenant_id)
        self._question_repo = Repository("survey_questions", tenant_id=tenant_id)
        self._response_repo = Repository("survey_responses", tenant_id=tenant_id)
        self._template_repo = Repository("survey_templates", tenant_id=tenant_id)

    # ── 설문 배포 ──

    def publish_survey(self, survey_id: str) -> dict[str, Any]:
        """설문을 배포한다 (draft → active).

        ERR-SVY-081: 질문이 없는 설문은 배포 불가.
        """
        survey = self._get_survey_or_404(survey_id)
        self._validate_transition(survey, "active")

        # 질문 존재 여부 확인
        question_count = self._question_repo.count({"survey_id": survey_id})
        if question_count == 0:
            raise_unprocessable("ERR-SVY-081", "질문이 없는 설문은 배포할 수 없습니다")

        update_data: dict[str, Any] = {"status": "active"}
        if not survey.get("starts_at"):
            update_data["starts_at"] = datetime.now(tz=UTC)

        self._survey_repo.update_by_id(survey_id, update_data)
        logger.info("설문 배포: %s", survey_id)
        return {**survey, **update_data}

    def close_survey(self, survey_id: str) -> dict[str, Any]:
        """설문을 마감한다 (active → closed)."""
        survey = self._get_survey_or_404(survey_id)
        self._validate_transition(survey, "closed")

        update_data: dict[str, Any] = {"status": "closed"}
        self._survey_repo.update_by_id(survey_id, update_data)
        logger.info("설문 마감: %s (응답 수: %d)", survey_id, survey.get("response_count", 0))
        return {**survey, **update_data}

    # ── 질문 관리 ──

    def add_question(self, survey_id: str, question_data: dict[str, Any]) -> dict[str, Any]:
        """설문에 질문을 추가한다.

        ERR-SVY-080: 진행 중인 설문의 질문은 수정할 수 없다.
        """
        survey = self._get_survey_or_404(survey_id)
        if survey.get("status") == "active":
            raise_unprocessable("ERR-SVY-080", "진행 중인 설문의 질문은 수정할 수 없습니다")

        question_id = generate_name("SQ", tenant_id=self._tenant_id)
        doc = {
            "_id": question_id,
            "survey_id": survey_id,
            **question_data,
            "tenant_id": self._tenant_id,
        }
        self._question_repo.insert(doc)
        logger.info("질문 추가: %s → %s", question_id, survey_id)
        return doc

    def update_question(self, question_id: str, update_data: dict[str, Any]) -> dict[str, Any]:
        """질문을 수정한다.

        ERR-SVY-080: 진행 중인 설문의 질문은 수정할 수 없다.
        """
        question = self._question_repo.find_by_id(question_id)
        if question is None:
            raise_not_found("설문 질문을 찾을 수 없습니다")
        question = cast("dict[str, Any]", question)

        survey = self._get_survey_or_404(question["survey_id"])
        if survey.get("status") == "active":
            raise_unprocessable("ERR-SVY-080", "진행 중인 설문의 질문은 수정할 수 없습니다")

        self._question_repo.update_by_id(question_id, update_data)
        return {**question, **update_data}

    # ── 응답 제출 ──

    def submit_response(self, survey_id: str, response_data: dict[str, Any]) -> dict[str, Any]:
        """설문 응답을 제출한다.

        ERR-SVY-050: 중복 응답 거부 (allow_multiple=false).
        ERR-SVY-051: 마감된 설문 응답 거부.
        ERR-SVY-052: 시작 전 설문 응답 거부.
        ERR-SVY-060: 필수 질문 미응답 거부.
        """
        survey = self._get_survey_or_404(survey_id)

        # 상태 확인
        if survey.get("status") == "closed":
            raise_unprocessable("ERR-SVY-051", "마감된 설문입니다")
        if survey.get("status") != "active":
            raise_unprocessable("ERR-SVY-052", "아직 시작되지 않은 설문입니다")

        # 시작 시각 확인
        now = datetime.now(tz=UTC)
        starts_at = survey.get("starts_at")
        if starts_at and starts_at > now:
            raise_unprocessable("ERR-SVY-052", "아직 시작되지 않은 설문입니다")

        # 중복 응답 확인
        respondent_id = response_data.get("respondent_id")
        if not survey.get("allow_multiple") and respondent_id:
            existing = self._response_repo.find_many(
                {"survey_id": survey_id, "respondent_id": respondent_id}, limit=1
            )
            if existing:
                raise_unprocessable("ERR-SVY-050", "이미 응답한 설문입니다")

        # 필수 질문 확인
        answers = response_data.get("answers", [])
        self._validate_required_questions(survey_id, answers)

        # NPS 값 범위 확인
        self._validate_nps_values(answers)

        # 응답 생성
        response_id = generate_name("SR", tenant_id=self._tenant_id)

        # 익명 설문이면 respondent_id 제거
        if survey.get("anonymity") == "anonymous":
            response_data["respondent_id"] = None

        doc = {
            "_id": response_id,
            "survey_id": survey_id,
            **response_data,
            "submitted_at": now,
            "tenant_id": self._tenant_id,
        }
        self._response_repo.insert(doc)

        # 응답 수 증가
        current_count = survey.get("response_count", 0)
        self._survey_repo.update_by_id(survey_id, {"response_count": current_count + 1})

        logger.info("설문 응답 제출: %s → %s", response_id, survey_id)
        return doc

    # ── 결과 집계 ──

    def calculate_nps(self, responses: list[dict[str, Any]], question_id: str) -> dict[str, Any]:
        """NPS(Net Promoter Score)를 계산한다.

        9~10: 추천자(promoters), 7~8: 중립(passives), 0~6: 비추천자(detractors).
        NPS = (추천자% - 비추천자%).
        """
        nps_values: list[int] = [
            answer["nps_value"]
            for resp in responses
            for answer in resp.get("answers", [])
            if answer.get("question_id") == question_id and answer.get("nps_value") is not None
        ]

        if not nps_values:
            return {"nps_score": Decimal(0), "promoters": 0, "passives": 0, "detractors": 0}

        total = len(nps_values)
        promoters = sum(1 for v in nps_values if v >= 9)
        passives = sum(1 for v in nps_values if 7 <= v <= 8)
        detractors = sum(1 for v in nps_values if v <= 6)

        nps_score = Decimal(str((promoters - detractors) / total * 100))

        return {
            "nps_score": nps_score,
            "promoters": promoters,
            "passives": passives,
            "detractors": detractors,
            "total": total,
        }

    def calculate_scale_stats(
        self, responses: list[dict[str, Any]], question_id: str
    ) -> dict[str, Any]:
        """척도 질문의 통계를 계산한다 (평균/중앙값/최빈값)."""
        values: list[int] = [
            answer["scale_value"]
            for resp in responses
            for answer in resp.get("answers", [])
            if answer.get("question_id") == question_id and answer.get("scale_value") is not None
        ]

        if not values:
            return {"mean": Decimal(0), "median": Decimal(0), "mode": 0, "count": 0}

        avg = Decimal(str(round(mean(values), 2)))
        med = Decimal(str(round(median(values), 2)))
        mode_val = max(set(values), key=values.count)

        return {"mean": avg, "median": med, "mode": mode_val, "count": len(values)}

    def calculate_response_rate(self, survey_id: str, total_target: int) -> Decimal:
        """응답률을 계산한다."""
        if total_target <= 0:
            return Decimal(0)
        survey = self._get_survey_or_404(survey_id)
        response_count = survey.get("response_count", 0)
        return Decimal(str(round(response_count / total_target * 100, 2)))

    def get_results_grouped(self, survey_id: str, group_by: str = "department") -> dict[str, Any]:
        """교차 분석 결과를 반환한다.

        소규모 그룹 익명 보호: 10명 미만은 '기타'로 합산.
        """
        responses = self._response_repo.find_many({"survey_id": survey_id}, limit=10000)
        groups: dict[str, list[dict[str, Any]]] = {}

        group_field = f"respondent_{group_by}"
        for resp in responses:
            group_key = resp.get(group_field, "기타") or "기타"
            groups.setdefault(group_key, []).append(resp)

        # 소규모 그룹 보호
        result: dict[str, list[dict[str, Any]]] = {}
        others: list[dict[str, Any]] = []
        for key, group_responses in groups.items():
            if len(group_responses) < _ANON_MIN_GROUP_SIZE:
                others.extend(group_responses)
            else:
                result[key] = group_responses

        if others:
            result.setdefault("기타", []).extend(others)

        return {
            "survey_id": survey_id,
            "group_by": group_by,
            "groups": {k: len(v) for k, v in result.items()},
        }

    # ── 조건부 로직 ──

    def evaluate_logic_rules(
        self,
        question_id: str,
        selected_option_id: str,
        all_questions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """조건부 로직 분기를 평가한다.

        SC-SVY-002: jump_to, skip, end_survey 처리.
        """
        # 현재 질문 찾기
        current_question = None
        current_idx = -1
        for idx, q in enumerate(all_questions):
            if q.get("_id") == question_id:
                current_question = q
                current_idx = idx
                break

        if current_question is None:
            return {"action": "continue", "next_question_id": None}

        # 로직 규칙 확인
        for rule in current_question.get("logic_rules", []):
            if rule.get("condition_option_id") == selected_option_id:
                action = rule.get("action")
                if action == "jump_to":
                    return {
                        "action": "jump_to",
                        "next_question_id": rule.get("target_question_id"),
                    }
                if action == "skip":
                    # 다음 질문 건너뛰기
                    skip_idx = current_idx + 2
                    if skip_idx < len(all_questions):
                        return {
                            "action": "skip",
                            "next_question_id": all_questions[skip_idx].get("_id"),
                        }
                    return {"action": "end_survey", "next_question_id": None}
                if action == "end_survey":
                    return {"action": "end_survey", "next_question_id": None}

        # 기본: 다음 질문으로 계속
        next_idx = current_idx + 1
        if next_idx < len(all_questions):
            return {"action": "continue", "next_question_id": all_questions[next_idx].get("_id")}
        return {"action": "end_survey", "next_question_id": None}

    # ── 템플릿 ──

    def create_from_template(self, template_id: str, survey_data: dict[str, Any]) -> dict[str, Any]:
        """템플릿으로 설문을 생성한다.

        SC-SVY-007: 질문 자동 복사, usage_count 증가.
        """
        template = self._template_repo.find_by_id(template_id)
        if template is None:
            raise_not_found("설문 템플릿을 찾을 수 없습니다")

        # 설문 생성
        survey_id = generate_name("SVY", tenant_id=self._tenant_id)
        doc = {
            "_id": survey_id,
            "status": "draft",
            "response_count": 0,
            "template_id": template_id,
            **survey_data,
            "tenant_id": self._tenant_id,
        }
        self._survey_repo.insert(doc)

        # 질문 복사
        questions_created = []
        for tq in template.get("questions", []):
            q_id = generate_name("SQ", tenant_id=self._tenant_id)
            q_doc = {
                "_id": q_id,
                "survey_id": survey_id,
                "question_text": tq.get("question_text", ""),
                "question_type": tq.get("question_type", "text"),
                "required": tq.get("required", True),
                "order": tq.get("order", 1),
                "options": tq.get("options", []),
                "scale_min": tq.get("scale_min", 1),
                "scale_max": tq.get("scale_max", 5),
                "matrix_rows": tq.get("matrix_rows", []),
                "matrix_columns": tq.get("matrix_columns", []),
                "tenant_id": self._tenant_id,
            }
            self._question_repo.insert(q_doc)
            questions_created.append(q_doc)

        # usage_count 증가
        usage = template.get("usage_count", 0) + 1
        self._template_repo.update_by_id(template_id, {"usage_count": usage})

        logger.info(
            "템플릿에서 설문 생성: %s → %s (질문 %d개)",
            template_id,
            survey_id,
            len(questions_created),
        )
        return {**doc, "questions_created": len(questions_created)}

    # ── 내부 헬퍼 ──

    def _get_survey_or_404(self, survey_id: str) -> dict[str, Any]:
        """설문을 조회하고 없으면 404를 발생시킨다."""
        survey = self._survey_repo.find_by_id(survey_id)
        if survey is None:
            raise_not_found("설문을 찾을 수 없습니다")
        return cast("dict[str, Any]", survey)

    def _validate_transition(self, survey: dict[str, Any], target_status: str) -> None:
        """설문 상태 전이 유효성을 검증한다."""
        current = survey.get("status", "draft")
        allowed = _VALID_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise_bad_request(f"'{current}' 상태에서 '{target_status}'로 전이할 수 없습니다")

    def _validate_required_questions(self, survey_id: str, answers: list[dict[str, Any]]) -> None:
        """필수 질문 응답 여부를 검증한다."""
        questions = self._question_repo.find_many(
            {"survey_id": survey_id, "required": True}, limit=100
        )
        answered_ids = {a.get("question_id") for a in answers}
        for q in questions:
            q_id = q.get("_id", "")
            if q_id not in answered_ids:
                raise_unprocessable("ERR-SVY-060", f"필수 질문에 응답해주세요: {q_id}")

    @staticmethod
    def _validate_nps_values(answers: list[dict[str, Any]]) -> None:
        """NPS 값 범위를 검증한다 (0~10)."""
        for answer in answers:
            nps_val = answer.get("nps_value")
            if nps_val is not None and (nps_val < 0 or nps_val > 10):
                raise_bad_request("NPS 값은 0~10 사이여야 합니다")
