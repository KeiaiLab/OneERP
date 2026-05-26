"""자금관리 서비스(TreasuryService) 단위 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_accounting_app.services.treasury_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_accounting_app.services.treasury_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_accounting_app.services.treasury_service import TreasuryService

        service = TreasuryService(tenant_id="test-tenant")
    return (
        service,
        repos["cash_flow_forecasts"],
        repos["loan_applications"],
        repos["loan_repayment_schedules"],
        repos["accounts_receivable"],
        repos["accounts_payable"],
    )


class Test자금예측:
    def test_30_60_90일_예측(self) -> None:
        service, _cf, _loan, _sched, ar_repo, ap_repo = _make_service()
        ar_repo.find_many.return_value = [
            {"outstanding_amount": 1000000, "due_date": "2026-04-10"},
        ]
        ap_repo.find_many.return_value = [
            {"outstanding_amount": 500000, "due_date": "2026-04-15"},
        ]

        result = service.forecast_cash_flow(as_of_date=date(2026, 3, 20))

        assert len(result["periods"]) == 3
        # 30일 기간: 3/20~4/19 내에 4/10, 4/15 모두 포함
        p30 = result["periods"][0]
        assert p30["expected_inflow"] == 1000000.0
        assert p30["expected_outflow"] == 500000.0
        assert p30["net_cash_flow"] == 500000.0

    def test_데이터_없으면_0(self) -> None:
        service, _cf, _loan, _sched, ar_repo, ap_repo = _make_service()
        ar_repo.find_many.return_value = []
        ap_repo.find_many.return_value = []

        result = service.forecast_cash_flow(as_of_date=date(2026, 3, 20))

        for period in result["periods"]:
            assert period["net_cash_flow"] == 0.0


class Test대출상환:
    def test_상환_스케줄_생성(self) -> None:
        service, _cf, loan_repo, sched_repo, _ar, _ap = _make_service()
        loan_repo.find_by_id.return_value = {
            "_id": "LOAN-001",
            "loan_amount": 12000000,
            "interest_rate": 5.0,
            "term_months": 12,
            "start_date": date(2026, 1, 1),
        }

        result = service.generate_repayment_schedule("LOAN-001")

        assert result["term_months"] == 12
        assert result["installment_count"] == 12
        assert result["monthly_payment"] > 0
        assert result["total_interest"] > 0
        sched_repo.insert.assert_called_once()

    def test_대출_미존재_에러(self) -> None:
        service, _cf, loan_repo, _sched, _ar, _ap = _make_service()
        loan_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.generate_repayment_schedule("LOAN-999")

    def test_무이자_대출(self) -> None:
        service, _cf, loan_repo, _sched_repo, _ar, _ap = _make_service()
        loan_repo.find_by_id.return_value = {
            "_id": "LOAN-002",
            "loan_amount": 1200000,
            "interest_rate": 0,
            "term_months": 12,
            "start_date": date(2026, 1, 1),
        }

        result = service.generate_repayment_schedule("LOAN-002")

        assert result["monthly_payment"] == 100000.0
        assert result["total_interest"] == 0
