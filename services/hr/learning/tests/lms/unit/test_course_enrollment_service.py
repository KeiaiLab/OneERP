"""교육 수강/진도/이수/퀴즈 서비스(CourseEnrollmentService) 단위 테스트.

SC-LMS-E001 ~ SC-LMS-E010: 수강·진도·이수·퀴즈 시나리오.
EX-LMS-E001 ~ EX-LMS-E008: 예외 시나리오.

대상 비즈니스 룰:
- BR-LMS-002: 수강 정원 확인
- BR-LMS-003: 게시 상태 확인
- BR-LMS-004: 진도율 자동 계산
- BR-LMS-005: 자동 이수 판정
- BR-LMS-007: 퀴즈 자동 채점
- BR-LMS-008: 퀴즈 응시 횟수 제한
- BR-LMS-013: 중복 수강 방지
- BR-LMS-015: 보관 과정 수강 불가
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from oneerp_core.errors import OneERPError
from oneerp_learning_app.lms.services.course_enrollment_service import (
    CourseEnrollmentService,
    EnrollmentRequest,
    PassCriteria,
    QuizQuestion,
)


class Test수강신청_정원:
    """BR-LMS-002: 수강 정원 확인."""

    def test_정원_여유가_있으면_허용(self) -> None:
        service = CourseEnrollmentService()
        result = service.check_enrollment_allowed(
            course={
                "_id": "CRS-001",
                "status": "PUBLISHED",
                "max_enrollments": 30,
            },
            current_enrolled=10,
            duplicate_exists=False,
        )
        assert result is True

    def test_정원_초과시_거부(self) -> None:
        """EX-LMS-E001: BR-LMS-002 위반."""
        service = CourseEnrollmentService()
        with pytest.raises(OneERPError, match="ERR-LMS-032"):
            service.check_enrollment_allowed(
                course={
                    "_id": "CRS-001",
                    "status": "PUBLISHED",
                    "max_enrollments": 10,
                },
                current_enrolled=10,
                duplicate_exists=False,
            )

    def test_무제한_정원_허용(self) -> None:
        service = CourseEnrollmentService()
        assert service.check_enrollment_allowed(
            course={"_id": "CRS-001", "status": "PUBLISHED", "max_enrollments": None},
            current_enrolled=9999,
            duplicate_exists=False,
        )


class Test수강신청_상태가드:
    """BR-LMS-003/015: 게시/보관 상태 확인."""

    def test_DRAFT_과정_수강_불가(self) -> None:
        """EX-LMS-E002: BR-LMS-003 위반."""
        service = CourseEnrollmentService()
        with pytest.raises(OneERPError, match="ERR-LMS-033"):
            service.check_enrollment_allowed(
                course={"_id": "CRS-001", "status": "DRAFT", "max_enrollments": 10},
                current_enrolled=0,
                duplicate_exists=False,
            )

    def test_ARCHIVED_과정_수강_불가(self) -> None:
        """EX-LMS-E003: BR-LMS-015 위반."""
        service = CourseEnrollmentService()
        with pytest.raises(OneERPError, match="ERR-LMS-036"):
            service.check_enrollment_allowed(
                course={"_id": "CRS-001", "status": "ARCHIVED", "max_enrollments": 10},
                current_enrolled=0,
                duplicate_exists=False,
            )

    def test_중복_수강_방지(self) -> None:
        """EX-LMS-E004: BR-LMS-013 위반."""
        service = CourseEnrollmentService()
        with pytest.raises(OneERPError, match="ERR-LMS-035"):
            service.check_enrollment_allowed(
                course={"_id": "CRS-001", "status": "PUBLISHED", "max_enrollments": 10},
                current_enrolled=0,
                duplicate_exists=True,
            )


class Test진도율계산:
    """BR-LMS-004: 진도율 자동 계산."""

    def test_완료_차시_있음(self) -> None:
        service = CourseEnrollmentService()
        rate = service.calculate_progress_rate(
            completed_lessons=["LSN-1", "LSN-2", "LSN-3"],
            required_lessons=["LSN-1", "LSN-2", "LSN-3", "LSN-4", "LSN-5"],
        )
        assert rate == Decimal("60.0")

    def test_완료_차시_없음(self) -> None:
        service = CourseEnrollmentService()
        rate = service.calculate_progress_rate(
            completed_lessons=[],
            required_lessons=["LSN-1", "LSN-2"],
        )
        assert rate == Decimal("0.0")

    def test_필수_차시_0개이면_100퍼센트(self) -> None:
        """분모가 0인 경우 100%로 처리 (ZeroDivision 방지)."""
        service = CourseEnrollmentService()
        rate = service.calculate_progress_rate(
            completed_lessons=[],
            required_lessons=[],
        )
        assert rate == Decimal("100.0")

    def test_필수외_차시_무시(self) -> None:
        """필수 차시 목록에 없는 LSN은 진도율에 포함되지 않는다."""
        service = CourseEnrollmentService()
        rate = service.calculate_progress_rate(
            completed_lessons=["LSN-1", "LSN-EXTRA"],
            required_lessons=["LSN-1", "LSN-2"],
        )
        assert rate == Decimal("50.0")


class Test이수판정:
    """BR-LMS-005: 자동 이수 판정."""

    def _pass_criteria(self) -> PassCriteria:
        return PassCriteria(
            min_attendance_rate=Decimal(80),
            min_progress_rate=Decimal(80),
            min_quiz_score=Decimal(60),
            requires_quiz_pass=True,
        )

    def test_모든_기준_충족시_합격(self) -> None:
        service = CourseEnrollmentService()
        result = service.evaluate_completion(
            progress_rate=Decimal(100),
            attendance_rate=Decimal(100),
            quiz_score=Decimal(85),
            quiz_passed=True,
            criteria=self._pass_criteria(),
        )
        assert result.is_passed is True
        assert "합격" in result.reason or result.reason == ""

    def test_진도율_미달시_불합격(self) -> None:
        service = CourseEnrollmentService()
        result = service.evaluate_completion(
            progress_rate=Decimal(70),
            attendance_rate=Decimal(100),
            quiz_score=Decimal(85),
            quiz_passed=True,
            criteria=self._pass_criteria(),
        )
        assert result.is_passed is False
        assert "진도율" in result.reason

    def test_출석률_미달시_불합격(self) -> None:
        service = CourseEnrollmentService()
        result = service.evaluate_completion(
            progress_rate=Decimal(100),
            attendance_rate=Decimal(75),
            quiz_score=Decimal(85),
            quiz_passed=True,
            criteria=self._pass_criteria(),
        )
        assert result.is_passed is False
        assert "출석률" in result.reason

    def test_퀴즈_점수_미달시_불합격(self) -> None:
        service = CourseEnrollmentService()
        result = service.evaluate_completion(
            progress_rate=Decimal(100),
            attendance_rate=Decimal(100),
            quiz_score=Decimal(50),
            quiz_passed=False,
            criteria=self._pass_criteria(),
        )
        assert result.is_passed is False
        assert "퀴즈" in result.reason

    def test_퀴즈_불필요_과정(self) -> None:
        service = CourseEnrollmentService()
        criteria = PassCriteria(
            min_attendance_rate=Decimal(0),
            min_progress_rate=Decimal(80),
            min_quiz_score=None,
            requires_quiz_pass=False,
        )
        result = service.evaluate_completion(
            progress_rate=Decimal(90),
            attendance_rate=Decimal(0),
            quiz_score=None,
            quiz_passed=None,
            criteria=criteria,
        )
        assert result.is_passed is True


class Test퀴즈채점:
    """BR-LMS-007/008: 퀴즈 자동 채점 및 응시 횟수."""

    def _questions(self) -> list[QuizQuestion]:
        return [
            QuizQuestion(question_id="Q1", correct_answer="A", score=Decimal(25)),
            QuizQuestion(question_id="Q2", correct_answer="B", score=Decimal(25)),
            QuizQuestion(question_id="Q3", correct_answer="TRUE", score=Decimal(25)),
            QuizQuestion(question_id="Q4", correct_answer="D", score=Decimal(25)),
        ]

    def test_전문항_정답(self) -> None:
        service = CourseEnrollmentService()
        result = service.grade_quiz(
            questions=self._questions(),
            answers={"Q1": "A", "Q2": "B", "Q3": "TRUE", "Q4": "D"},
            pass_score=Decimal(60),
        )
        assert result["score"] == Decimal(100)
        assert result["passed"] is True

    def test_부분_정답(self) -> None:
        service = CourseEnrollmentService()
        result = service.grade_quiz(
            questions=self._questions(),
            answers={"Q1": "A", "Q2": "B", "Q3": "FALSE", "Q4": "A"},
            pass_score=Decimal(60),
        )
        assert result["score"] == Decimal(50)
        assert result["passed"] is False
        assert result["correct_count"] == 2

    def test_대소문자_무시(self) -> None:
        """객관식/O-X 정답 비교 시 대소문자/공백을 정규화한다."""
        service = CourseEnrollmentService()
        result = service.grade_quiz(
            questions=self._questions(),
            answers={"Q1": "a", "Q2": " B ", "Q3": "true", "Q4": "d"},
            pass_score=Decimal(60),
        )
        assert result["score"] == Decimal(100)

    def test_응시_횟수_초과(self) -> None:
        """EX-LMS-E005: BR-LMS-008 위반."""
        service = CourseEnrollmentService()
        with pytest.raises(OneERPError, match="ERR-LMS-034"):
            service.check_quiz_attempt_allowed(current_attempts=3, max_attempts=3)


class Test수강신청_통합:
    """EnrollmentRequest를 받아 복합 가드를 적용."""

    def test_정상_수강_신청(self) -> None:
        service = CourseEnrollmentService()
        result = service.enroll(
            EnrollmentRequest(
                course={
                    "_id": "CRS-001",
                    "status": "PUBLISHED",
                    "max_enrollments": 30,
                },
                current_enrolled=5,
                duplicate_exists=False,
                employee_id="EMP-001",
                employee_name="홍길동",
            )
        )
        assert result["status"] == "ENROLLED"
        assert result["employee_id"] == "EMP-001"
