"""법정의무교육 스케줄링/이수율/미이수자 서비스 단위 테스트.

SC-LMS-L001 ~ SC-LMS-L010: 법정교육 시나리오.

대상 비즈니스 룰:
- BR-LMS-009: 법정의무교육 미이수자 알림
- BR-LMS-010: 법정의무교육 이수율 자동 계산
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from oneerp_learning_app.lms.services.legal_mandatory_training_service import (
    KOREAN_MANDATORY_TRAININGS,
    ComplianceStatus,
    LegalMandatoryTrainingService,
    TrainingScheduleItem,
)


class Test한국법정교육_카탈로그:
    """한국 5대 법정의무교육 카탈로그 검증."""

    def test_카탈로그_5종_이상(self) -> None:
        """산안법/남녀고평법/개보법/장애인법/근기법 등 5종 이상."""
        assert len(KOREAN_MANDATORY_TRAININGS) >= 5

    def test_필수_교육_존재(self) -> None:
        codes = {t.code for t in KOREAN_MANDATORY_TRAININGS}
        assert "SAFETY" in codes
        assert "HARASSMENT" in codes
        assert "PRIVACY" in codes
        assert "DISABILITY" in codes

    def test_산업안전보건교육_사무직_시간(self) -> None:
        """산안법: 사무직 근로자는 매반기 6시간."""
        service = LegalMandatoryTrainingService()
        hours = service.get_required_hours(
            compliance_type="SAFETY",
            job_category="office",
        )
        assert hours == Decimal(6)

    def test_산업안전보건교육_생산직_시간(self) -> None:
        """산안법: 사무직·판매직 외 근로자는 매반기 12시간."""
        service = LegalMandatoryTrainingService()
        hours = service.get_required_hours(
            compliance_type="SAFETY",
            job_category="production",
        )
        assert hours == Decimal(12)

    def test_성희롱예방교육_연1시간(self) -> None:
        service = LegalMandatoryTrainingService()
        hours = service.get_required_hours(
            compliance_type="HARASSMENT",
            job_category="office",
        )
        assert hours == Decimal(1)


class Test스케줄생성:
    """BR-LMS-009 연동: 연간 스케줄 생성."""

    def test_연간_스케줄_생성(self) -> None:
        """성희롱예방/개보/장애인: 연 1회 → 1개 스케줄 생성."""
        service = LegalMandatoryTrainingService()
        schedule: list[TrainingScheduleItem] = service.generate_annual_schedule(
            year=2026,
            compliance_type="HARASSMENT",
        )
        assert len(schedule) == 1
        assert schedule[0].year == 2026
        assert schedule[0].compliance_type == "HARASSMENT"
        # 연 1회 교육이라 기한은 해당 연말
        assert schedule[0].deadline == date(2026, 12, 31)

    def test_산안교육_반기별_2회(self) -> None:
        """산업안전: 매반기 → 상반기/하반기 2개 스케줄 생성."""
        service = LegalMandatoryTrainingService()
        schedule = service.generate_annual_schedule(year=2026, compliance_type="SAFETY")
        assert len(schedule) == 2
        deadlines = sorted(s.deadline for s in schedule)
        assert deadlines[0] == date(2026, 6, 30)
        assert deadlines[1] == date(2026, 12, 31)


class Test이수율_계산:
    """BR-LMS-010: 이수율 자동 계산."""

    def test_정상_이수율(self) -> None:
        service = LegalMandatoryTrainingService()
        result = service.calculate_completion_rate(
            total_target=200,
            completed_count=180,
        )
        assert result == Decimal("90.0")

    def test_전원_이수(self) -> None:
        service = LegalMandatoryTrainingService()
        assert service.calculate_completion_rate(
            total_target=100,
            completed_count=100,
        ) == Decimal("100.0")

    def test_대상자_0명_ZeroDivision_방지(self) -> None:
        service = LegalMandatoryTrainingService()
        assert service.calculate_completion_rate(
            total_target=0,
            completed_count=0,
        ) == Decimal("0.0")

    def test_이수자가_대상자보다_많을수_없음(self) -> None:
        service = LegalMandatoryTrainingService()
        with pytest.raises(ValueError, match="이수자 수"):
            service.calculate_completion_rate(
                total_target=10,
                completed_count=15,
            )


class Test미이수자_식별:
    """BR-LMS-009: 미이수자 알림 대상 계산."""

    def test_미이수자_목록_추출(self) -> None:
        service = LegalMandatoryTrainingService()
        non_completers = service.identify_non_completers(
            target_employees=["EMP-001", "EMP-002", "EMP-003", "EMP-004"],
            completed_employees=["EMP-001", "EMP-003"],
        )
        assert set(non_completers) == {"EMP-002", "EMP-004"}

    def test_전원_이수시_빈_리스트(self) -> None:
        service = LegalMandatoryTrainingService()
        non_completers = service.identify_non_completers(
            target_employees=["EMP-001", "EMP-002"],
            completed_employees=["EMP-001", "EMP-002"],
        )
        assert non_completers == []

    def test_알림_단계_30일전(self) -> None:
        """기한 30일 전 → WARNING 단계."""
        service = LegalMandatoryTrainingService()
        status = service.evaluate_status(
            deadline=date(2026, 5, 1),
            today=date(2026, 4, 1),
        )
        assert status == ComplianceStatus.WARNING

    def test_알림_단계_7일전(self) -> None:
        """기한 7일 전 → URGENT 단계."""
        service = LegalMandatoryTrainingService()
        status = service.evaluate_status(
            deadline=date(2026, 4, 15),
            today=date(2026, 4, 10),
        )
        assert status == ComplianceStatus.URGENT

    def test_알림_단계_기한경과(self) -> None:
        """기한 경과 → OVERDUE 단계."""
        service = LegalMandatoryTrainingService()
        status = service.evaluate_status(
            deadline=date(2026, 3, 1),
            today=date(2026, 4, 10),
        )
        assert status == ComplianceStatus.OVERDUE

    def test_알림_단계_여유(self) -> None:
        """기한 30일 이상 → ON_TRACK."""
        service = LegalMandatoryTrainingService()
        status = service.evaluate_status(
            deadline=date(2026, 12, 31),
            today=date(2026, 4, 10),
        )
        assert status == ComplianceStatus.ON_TRACK
