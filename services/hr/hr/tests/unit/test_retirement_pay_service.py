"""퇴직금 산정 서비스(RetirementPayService) 단위 테스트.

한국 근로기준법/근로자퇴직급여 보장법 기반 케이스를 검증한다.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    """RetirementPayService와 레포지토리 mock 을 생성한다."""
    with patch("oneerp_hr_app.services.retirement_pay_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            if collection_name not in repos:
                repos[collection_name] = MagicMock()
            return repos[collection_name]

        mock_repo_cls.side_effect = _factory
        from oneerp_hr_app.services.retirement_pay_service import RetirementPayService

        service = RetirementPayService(tenant_id="test-tenant")
    return (
        service,
        repos.setdefault("employees", MagicMock()),
        repos.setdefault("employee_wage_records", MagicMock()),
        repos.setdefault("employee_retirement_pays", MagicMock()),
    )


class Test평균임금산정:
    """BR-HR-022: 근로기준법 제2조 제6호 평균임금 산정."""

    def test_3개월_임금_평균_계산(self) -> None:
        """이전 3개월 임금총액/총일수 = 1일 평균임금."""
        service, _emp_repo, wage_repo, _ret = _make_service()
        # 3개월 * 월 300만원 -> 총 900만원
        wage_repo.find_many.return_value = [
            {"payment_date": "2026-01-25", "amount": 3_000_000},
            {"payment_date": "2026-02-25", "amount": 3_000_000},
            {"payment_date": "2026-03-25", "amount": 3_000_000},
        ]

        result = service.calculate_average_wage(
            employee_id="EMP-001",
            termination_date=date(2026, 4, 1),
        )

        # period_days 는 약 92일
        assert result["employee_id"] == "EMP-001"
        assert result["period_days"] > 80
        assert Decimal(result["total_wage"]) == Decimal(9000000)
        # 일평균 ~ 9,000,000 / 92 ≈ 97,826원
        avg = Decimal(result["average_daily_wage"])
        assert Decimal(95000) < avg < Decimal(101000)

    def test_임금기록_없음_404(self) -> None:
        service, _emp, wage_repo, _ret = _make_service()
        wage_repo.find_many.return_value = []

        with pytest.raises(OneERPError) as exc_info:
            service.calculate_average_wage(
                employee_id="EMP-999",
                termination_date=date(2026, 4, 1),
            )
        assert exc_info.value.status_code == 404


class Test퇴직금산정:
    """BR-HR-021/023/024: 퇴직금 계산 공식."""

    def test_3년_근속_정상_계산(self) -> None:
        """3년 근속 + 일평균 10만원 -> 퇴직금 ≈ 10만 * 30일 * (3*365/365) = 900만원."""
        service, emp_repo, wage_repo, _ret = _make_service()
        emp_repo.find_by_id.return_value = {
            "_id": "EMP-002",
            "date_of_joining": "2023-04-01",
        }
        wage_repo.find_many.return_value = [
            {"payment_date": "2026-01-25", "amount": 3_000_000},
            {"payment_date": "2026-02-25", "amount": 3_000_000},
            {"payment_date": "2026-03-25", "amount": 3_000_000},
        ]

        result = service.calculate_retirement_pay(
            employee_id="EMP-002",
            termination_date=date(2026, 4, 1),
        )

        assert result["eligible"] is True
        # 근속 3년 ≈ 1096일
        assert result["service_days"] >= 1095
        # 퇴직금: 일급 * 30 * 근속일/365 — 약 900만원 근사
        pay = Decimal(result["retirement_pay"])
        assert Decimal(8500000) < pay < Decimal(10000000)

    def test_1년_미만_근속_지급대상_아님(self) -> None:
        """BR-HR-024: 계속근로기간 1년 미만 -> eligible=False, 퇴직금 0."""
        service, emp_repo, wage_repo, _ret = _make_service()
        emp_repo.find_by_id.return_value = {
            "_id": "EMP-003",
            "date_of_joining": "2025-06-01",
        }
        wage_repo.find_many.return_value = [
            {"payment_date": "2026-01-25", "amount": 3_000_000},
            {"payment_date": "2026-02-25", "amount": 3_000_000},
            {"payment_date": "2026-03-25", "amount": 3_000_000},
        ]

        result = service.calculate_retirement_pay(
            employee_id="EMP-003",
            termination_date=date(2026, 4, 1),
        )

        assert result["eligible"] is False
        assert Decimal(result["retirement_pay"]) == Decimal(0)

    def test_통상임금_더_높은_경우_통상임금_적용(self) -> None:
        """BR-HR-023: 통상임금 > 평균임금이면 통상임금 기준."""
        service, emp_repo, wage_repo, _ret = _make_service()
        emp_repo.find_by_id.return_value = {
            "_id": "EMP-004",
            "date_of_joining": "2023-04-01",
        }
        # 월 100만원 -> 일평균 약 33,000원
        wage_repo.find_many.return_value = [
            {"payment_date": "2026-01-25", "amount": 1_000_000},
            {"payment_date": "2026-02-25", "amount": 1_000_000},
            {"payment_date": "2026-03-25", "amount": 1_000_000},
        ]

        result = service.calculate_retirement_pay(
            employee_id="EMP-004",
            termination_date=date(2026, 4, 1),
            ordinary_daily_wage=Decimal(100000),
        )

        # 통상임금(10만원)이 평균임금(약 32,000원)보다 크므로 통상임금 적용
        assert result["applied_daily_wage"] == "100000"

    def test_직원_없음_404(self) -> None:
        service, emp_repo, _wage, _ret = _make_service()
        emp_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.calculate_retirement_pay(
                employee_id="EMP-NONE",
                termination_date=date(2026, 4, 1),
            )
        assert exc_info.value.status_code == 404

    def test_입사일_없음_422(self) -> None:
        service, emp_repo, _wage, _ret = _make_service()
        emp_repo.find_by_id.return_value = {"_id": "EMP-005"}

        with pytest.raises(OneERPError) as exc_info:
            service.calculate_retirement_pay(
                employee_id="EMP-005",
                termination_date=date(2026, 4, 1),
            )
        assert exc_info.value.status_code == 422

    def test_퇴직일이_입사일보다_이전_422(self) -> None:
        service, emp_repo, _wage, _ret = _make_service()
        emp_repo.find_by_id.return_value = {
            "_id": "EMP-006",
            "date_of_joining": "2026-06-01",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.calculate_retirement_pay(
                employee_id="EMP-006",
                termination_date=date(2026, 4, 1),
            )
        assert exc_info.value.status_code == 422


class Test퇴직금기록:
    def test_기록_저장(self) -> None:
        """record_retirement_pay 호출 시 employee_retirement_pays 에 insert 된다."""
        service, emp_repo, wage_repo, ret_repo = _make_service()
        emp_repo.find_by_id.return_value = {
            "_id": "EMP-007",
            "date_of_joining": "2023-04-01",
        }
        wage_repo.find_many.return_value = [
            {"payment_date": "2026-01-25", "amount": 3_000_000},
            {"payment_date": "2026-02-25", "amount": 3_000_000},
            {"payment_date": "2026-03-25", "amount": 3_000_000},
        ]

        result = service.record_retirement_pay(
            employee_id="EMP-007",
            termination_date=date(2026, 4, 1),
        )

        ret_repo.insert.assert_called_once()
        assert "retirement_pay" in result
        assert result["employee_id"] == "EMP-007"
