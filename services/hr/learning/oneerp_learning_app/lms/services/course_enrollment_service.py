"""교육 수강·진도·이수·퀴즈 서비스 — LMS 핵심 비즈니스 로직.

L2 사양: docs/product/scope/modules/lms/L2-spec.md

비즈니스 규칙:
- BR-LMS-002: 수강 정원 확인 (max_enrollments)
- BR-LMS-003: 게시 상태 확인 (PUBLISHED)
- BR-LMS-004: 학습 진도율 자동 계산
- BR-LMS-005: 자동 이수 판정 (진도/출석/퀴즈)
- BR-LMS-007: 퀴즈 자동 채점 (객관식/O-X, 대소문자/공백 정규화)
- BR-LMS-008: 퀴즈 응시 횟수 제한 (max_attempts)
- BR-LMS-013: 중복 수강 방지
- BR-LMS-015: 보관(ARCHIVED) 과정 수강 불가

에러 코드:
- ERR-LMS-032: 수강 정원 초과
- ERR-LMS-033: 게시되지 않은 과정
- ERR-LMS-034: 최대 응시 횟수 초과
- ERR-LMS-035: 이미 수강 중인 과정
- ERR-LMS-036: 보관된 과정 수강 불가

설계 주석:
- 표준 라이브러리 decimal 기반 산술, LLM 호출 금지
- Repository 의존성을 제거하고 pure Python 계산만 수행해
  상위 라우터에서 저장소 I/O와 조합할 수 있도록 한다
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from oneerp_core.errors import OneERPError

logger = logging.getLogger(__name__)


# 과정 상태 상수 — L2 사양 1.1 Course.status 참조
_COURSE_STATUS_PUBLISHED = "PUBLISHED"
_COURSE_STATUS_ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class PassCriteria:
    """이수 기준 — Course.pass_criteria 내장 문서."""

    min_attendance_rate: Decimal
    min_progress_rate: Decimal
    min_quiz_score: Decimal | None
    requires_quiz_pass: bool


@dataclass(frozen=True)
class QuizQuestion:
    """퀴즈 문항 — Quiz.questions 내장 문서 중 채점에 필요한 부분."""

    question_id: str
    correct_answer: str
    score: Decimal


@dataclass(frozen=True)
class EvaluationResult:
    """이수 판정 결과."""

    is_passed: bool
    reason: str


@dataclass(frozen=True)
class EnrollmentRequest:
    """수강 신청 입력 DTO."""

    course: dict[str, Any]
    current_enrolled: int
    duplicate_exists: bool
    employee_id: str
    employee_name: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


class CourseEnrollmentService:
    """수강·진도·이수·퀴즈 비즈니스 로직."""

    # ------------------------------------------------------------------
    # 수강 신청 가드
    # ------------------------------------------------------------------

    def check_enrollment_allowed(
        self,
        course: dict[str, Any],
        *,
        current_enrolled: int,
        duplicate_exists: bool,
    ) -> bool:
        """수강 신청 가드 전체 검증 — BR-LMS-002/003/013/015.

        Returns:
            통과 시 True. 위반 시 OneERPError.
        """
        status = course.get("status", "")

        # BR-LMS-015: 보관 과정 수강 불가 (더 명확한 오류가 우선)
        if status == _COURSE_STATUS_ARCHIVED:
            raise OneERPError(
                status_code=422,
                error="ERR-LMS-036",
                detail="보관된 과정에는 수강 신청할 수 없습니다 (BR-LMS-015)",
            )

        # BR-LMS-003: 게시 상태 확인
        if status != _COURSE_STATUS_PUBLISHED:
            raise OneERPError(
                status_code=422,
                error="ERR-LMS-033",
                detail=f"게시되지 않은 과정에는 수강 신청할 수 없습니다 (BR-LMS-003, 현재: {status})",
            )

        # BR-LMS-013: 중복 수강 방지
        if duplicate_exists:
            raise OneERPError(
                status_code=422,
                error="ERR-LMS-035",
                detail="이미 수강 중인 과정입니다 (BR-LMS-013)",
            )

        # BR-LMS-002: 수강 정원 확인 (None = 무제한)
        max_enrollments = course.get("max_enrollments")
        if max_enrollments is not None and current_enrolled >= int(max_enrollments):
            raise OneERPError(
                status_code=422,
                error="ERR-LMS-032",
                detail=f"수강 정원이 초과되었습니다 (BR-LMS-002, 정원: {max_enrollments})",
            )

        return True

    def enroll(self, request: EnrollmentRequest) -> dict[str, Any]:
        """수강 신청을 수행한다 (가드 통과 시 ENROLLED 상태 결과 반환)."""
        self.check_enrollment_allowed(
            request.course,
            current_enrolled=request.current_enrolled,
            duplicate_exists=request.duplicate_exists,
        )
        logger.info("수강 신청: 과정=%s", request.course.get("_id", ""))
        return {
            "course_ref": request.course.get("_id", ""),
            "employee_id": request.employee_id,
            "employee_name": request.employee_name,
            "status": "ENROLLED",
        }

    # ------------------------------------------------------------------
    # 진도율 계산 — BR-LMS-004
    # ------------------------------------------------------------------

    def calculate_progress_rate(
        self,
        *,
        completed_lessons: list[str],
        required_lessons: list[str],
    ) -> Decimal:
        """완료한 차시 대비 필수 차시 비율(%)을 계산한다.

        수식: progress_rate = count(완료 AND 필수) / count(필수) x 100
        필수 차시가 0개이면 100%로 처리한다 (ZeroDivision 방지).
        """
        if not required_lessons:
            return Decimal("100.0")

        required_set = set(required_lessons)
        completed_required = sum(1 for lsn in completed_lessons if lsn in required_set)
        rate = (Decimal(completed_required) / Decimal(len(required_lessons))) * Decimal(100)
        return rate.quantize(Decimal("0.1"))

    # ------------------------------------------------------------------
    # 이수 판정 — BR-LMS-005
    # ------------------------------------------------------------------

    def evaluate_completion(
        self,
        *,
        progress_rate: Decimal,
        attendance_rate: Decimal,
        quiz_score: Decimal | None,
        quiz_passed: bool | None,
        criteria: PassCriteria,
    ) -> EvaluationResult:
        """이수 판정 — 진도/출석/퀴즈 기준을 모두 충족해야 합격."""
        reasons: list[str] = []

        if progress_rate < criteria.min_progress_rate:
            reasons.append(f"진도율 미달 ({progress_rate}% < {criteria.min_progress_rate}%)")
        if attendance_rate < criteria.min_attendance_rate:
            reasons.append(f"출석률 미달 ({attendance_rate}% < {criteria.min_attendance_rate}%)")
        if criteria.requires_quiz_pass:
            if not quiz_passed:
                reasons.append("퀴즈 합격 필요")
            if criteria.min_quiz_score is not None and (
                quiz_score is None or quiz_score < criteria.min_quiz_score
            ):
                reasons.append(f"퀴즈 점수 미달 ({quiz_score} < {criteria.min_quiz_score})")

        if reasons:
            return EvaluationResult(is_passed=False, reason=", ".join(reasons))
        return EvaluationResult(is_passed=True, reason="")

    # ------------------------------------------------------------------
    # 퀴즈 채점 — BR-LMS-007/008
    # ------------------------------------------------------------------

    def grade_quiz(
        self,
        *,
        questions: list[QuizQuestion],
        answers: dict[str, str],
        pass_score: Decimal,
    ) -> dict[str, Any]:
        """객관식/O-X 퀴즈를 채점한다.

        정답 비교 시 대소문자·앞뒤 공백을 정규화한다.
        """
        total_score = sum((q.score for q in questions), Decimal(0))
        earned = Decimal(0)
        correct_count = 0
        results: list[dict[str, Any]] = []

        for question in questions:
            user_answer = self._normalize(answers.get(question.question_id, ""))
            correct_answer = self._normalize(question.correct_answer)
            is_correct = user_answer == correct_answer
            if is_correct:
                earned += question.score
                correct_count += 1
            results.append(
                {
                    "question_id": question.question_id,
                    "correct": is_correct,
                    "score": float(question.score) if is_correct else 0.0,
                }
            )

        passed = earned >= pass_score
        return {
            "score": earned,
            "total_score": total_score,
            "passed": passed,
            "correct_count": correct_count,
            "results": results,
        }

    @staticmethod
    def _normalize(value: str) -> str:
        """정답 비교용 정규화 — 앞뒤 공백 제거 + 대문자 통일."""
        return value.strip().upper()

    def check_quiz_attempt_allowed(
        self,
        *,
        current_attempts: int,
        max_attempts: int,
    ) -> bool:
        """BR-LMS-008: 최대 응시 횟수 확인."""
        if current_attempts >= max_attempts:
            raise OneERPError(
                status_code=422,
                error="ERR-LMS-034",
                detail=f"최대 응시 횟수를 초과했습니다 (BR-LMS-008, 최대: {max_attempts})",
            )
        return True
