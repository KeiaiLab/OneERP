"""연차 산정 서비스(AnnualLeaveAccrualService) 단위 테스트.

한국 근로기준법 제60조 전체 조항을 케이스별로 검증한다.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from oneerp_core.errors import OneERPError
from oneerp_hr_app.services.annual_leave_accrual_service import AnnualLeaveAccrualService


@pytest.fixture
def svc() -> AnnualLeaveAccrualService:
    return AnnualLeaveAccrualService(tenant_id="test-tenant")


class Test근속기간계산:
    def test_동일월_근속(self, svc: AnnualLeaveAccrualService) -> None:
        years, months = svc.compute_service_duration(
            hire_date=date(2026, 1, 1),
            reference_date=date(2026, 3, 1),
        )
        assert years == 0
        assert months == 2

    def test_만_5년_근속(self, svc: AnnualLeaveAccrualService) -> None:
        years, months = svc.compute_service_duration(
            hire_date=date(2021, 4, 10),
            reference_date=date(2026, 4, 10),
        )
        assert years == 5
        assert months == 60

    def test_기준일이_입사일보다_이전_422(self, svc: AnnualLeaveAccrualService) -> None:
        with pytest.raises(OneERPError) as exc_info:
            svc.compute_service_duration(
                hire_date=date(2026, 4, 10),
                reference_date=date(2026, 1, 1),
            )
        assert exc_info.value.status_code == 422


class Test출근률계산:
    """BR-HR-033: 출근률 = 출근일 / 근무일 * 100."""

    def test_정상_출근률(self, svc: AnnualLeaveAccrualService) -> None:
        rate = svc.compute_attendance_rate(working_days=200, present_days=180)
        assert rate == Decimal("90.00")

    def test_근무일_0인_경우(self, svc: AnnualLeaveAccrualService) -> None:
        rate = svc.compute_attendance_rate(working_days=0, present_days=0)
        assert rate == Decimal("0.00")

    def test_출근일_근무일_초과_422(self, svc: AnnualLeaveAccrualService) -> None:
        with pytest.raises(OneERPError) as exc_info:
            svc.compute_attendance_rate(working_days=100, present_days=150)
        assert exc_info.value.status_code == 422

    def test_음수_입력_422(self, svc: AnnualLeaveAccrualService) -> None:
        with pytest.raises(OneERPError) as exc_info:
            svc.compute_attendance_rate(working_days=-1, present_days=0)
        assert exc_info.value.status_code == 422


class Test근속1년미만_월차:
    """BR-HR-030: 1년 미만은 근속 월수 * 1일, 최대 11일."""

    def test_6개월_근속_6일(self, svc: AnnualLeaveAccrualService) -> None:
        result = svc.accrue_leave(
            employee_id="EMP-001",
            hire_date=date(2025, 10, 1),
            reference_date=date(2026, 4, 1),
            working_days=100,
            present_days=100,
        )
        assert result.total_days == 6
        assert result.rule_applied == "under_1_year"

    def test_11개월_근속_11일(self, svc: AnnualLeaveAccrualService) -> None:
        result = svc.accrue_leave(
            employee_id="EMP-002",
            hire_date=date(2025, 5, 1),
            reference_date=date(2026, 4, 1),
            working_days=200,
            present_days=200,
        )
        assert result.total_days == 11
        assert result.rule_applied == "under_1_year"


class Test근속1년이상_15일:
    """BR-HR-031: 1년 이상 + 출근률 80% 이상 -> 15일."""

    def test_1년_만근_15일(self, svc: AnnualLeaveAccrualService) -> None:
        result = svc.accrue_leave(
            employee_id="EMP-003",
            hire_date=date(2025, 4, 1),
            reference_date=date(2026, 4, 1),
            working_days=250,
            present_days=240,  # 96%
        )
        assert result.total_days == 15
        assert result.rule_applied == "annual_80_over"
        assert result.base_days == 15
        assert result.additional_days == 0

    def test_2년_근속_15일(self, svc: AnnualLeaveAccrualService) -> None:
        """2년차는 가산 없이 15일."""
        result = svc.accrue_leave(
            employee_id="EMP-004",
            hire_date=date(2024, 4, 1),
            reference_date=date(2026, 4, 1),
            working_days=250,
            present_days=250,
        )
        assert result.total_days == 15

    def test_출근률_80미만_월차방식(self, svc: AnnualLeaveAccrualService) -> None:
        """근속 1년 이상이어도 출근률 80% 미만이면 월차 방식."""
        result = svc.accrue_leave(
            employee_id="EMP-005",
            hire_date=date(2025, 4, 1),
            reference_date=date(2026, 4, 1),
            working_days=250,
            present_days=150,  # 60%
        )
        assert result.rule_applied == "annual_80_under"
        assert result.total_days == 11  # 월차 최대


class Test3년이상_가산휴가:
    """BR-HR-032: 3년 이상 + 매 2년마다 1일 가산, 총 25일 한도."""

    def test_3년_근속_16일(self, svc: AnnualLeaveAccrualService) -> None:
        """3년차: 15 + (3-1)//2 = 15 + 1 = 16일."""
        result = svc.accrue_leave(
            employee_id="EMP-010",
            hire_date=date(2023, 4, 1),
            reference_date=date(2026, 4, 1),
            working_days=250,
            present_days=250,
        )
        assert result.total_days == 16
        assert result.base_days == 15
        assert result.additional_days == 1
        assert result.rule_applied == "with_additional"

    def test_5년_근속_17일(self, svc: AnnualLeaveAccrualService) -> None:
        """5년차: 15 + (5-1)//2 = 15 + 2 = 17일."""
        result = svc.accrue_leave(
            employee_id="EMP-011",
            hire_date=date(2021, 4, 1),
            reference_date=date(2026, 4, 1),
            working_days=250,
            present_days=250,
        )
        assert result.total_days == 17

    def test_21년_근속_25일_한도(self, svc: AnnualLeaveAccrualService) -> None:
        """21년차: 15 + (21-1)//2 = 15+10 = 25일 (한도)."""
        result = svc.accrue_leave(
            employee_id="EMP-012",
            hire_date=date(2005, 4, 1),
            reference_date=date(2026, 4, 1),
            working_days=250,
            present_days=250,
        )
        assert result.total_days == 25
        assert result.base_days == 15

    def test_25년_근속_25일_한도_유지(self, svc: AnnualLeaveAccrualService) -> None:
        """25년차: 15 + (25-1)//2 = 15+12 = 27 -> 25 한도."""
        result = svc.accrue_leave(
            employee_id="EMP-013",
            hire_date=date(2001, 4, 1),
            reference_date=date(2026, 4, 1),
            working_days=250,
            present_days=250,
        )
        assert result.total_days == 25


class Test소멸일_계산:
    """BR-HR-034: 연차 소멸일은 발생일 + 1년."""

    def test_정상_소멸일(self, svc: AnnualLeaveAccrualService) -> None:
        expiry = svc.compute_expiry_date(date(2026, 4, 1))
        assert expiry == date(2027, 3, 31)

    def test_윤년_2월_29일(self, svc: AnnualLeaveAccrualService) -> None:
        """윤년 2월 29일에 발생한 연차의 소멸일."""
        # 2024는 윤년
        expiry = svc.compute_expiry_date(date(2024, 2, 29))
        # 소멸일은 2025-02-28 (평년이라 보정)
        assert expiry == date(2025, 2, 28)
