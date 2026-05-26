"""기간 마감 서비스(PeriodClosingService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    """generate_name을 테스트 전체 기간 동안 모킹한다."""
    with patch(
        "oneerp_accounting_app.services.period_closing_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """PeriodClosingService와 모킹된 Repository 인스턴스들을 반환한다."""
    with patch("oneerp_accounting_app.services.period_closing_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_accounting_app.services.period_closing_service import PeriodClosingService

        service = PeriodClosingService(tenant_id="test-tenant")

    return (
        service,
        repos["accounting_periods"],
        repos["fiscal_years"],
        repos["journal_entries"],
        repos["period_closing_vouchers"],
    )


def _open_period(period_id: str = "APD-001") -> dict:
    return {
        "_id": period_id,
        "period_name": "2026년 1월",
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "company": "COMP-001",
        "status": "open",
        "fiscal_year": "FY-2026",
    }


class Test기간마감검증:
    """validate_period_closeable 테스트."""

    def test_미제출전표_없으면_마감가능(self) -> None:
        service, period_repo, _fy, je_repo, _pcv = _make_service()
        period_repo.find_by_id.return_value = _open_period()
        je_repo.find_many.return_value = [
            {"_id": "JE-001", "docstatus": 1},  # SUBMITTED
            {"_id": "JE-002", "docstatus": 1},
        ]

        result = service.validate_period_closeable("APD-001")

        assert result["closeable"] is True
        assert result["draft_count"] == 0
        assert result["submitted_count"] == 2

    def test_미제출전표_있으면_마감불가(self) -> None:
        service, period_repo, _fy, je_repo, _pcv = _make_service()
        period_repo.find_by_id.return_value = _open_period()
        je_repo.find_many.return_value = [
            {"_id": "JE-001", "docstatus": 0},  # DRAFT
            {"_id": "JE-002", "docstatus": 1},
        ]

        result = service.validate_period_closeable("APD-001")

        assert result["closeable"] is False
        assert result["draft_count"] == 1

    def test_기간_미존재시_에러(self) -> None:
        service, period_repo, _fy, _je, _pcv = _make_service()
        period_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.validate_period_closeable("APD-999")


class Test기간마감:
    """close_period 테스트."""

    def test_기간마감_성공(self) -> None:
        service, period_repo, _fy, je_repo, pcv_repo = _make_service()
        period_repo.find_by_id.return_value = _open_period()
        # 미제출 전표 없음
        je_repo.find_many.return_value = [
            {
                "_id": "JE-001",
                "docstatus": 1,
                "items": [
                    {"account_type": "income", "debit": 0, "credit": 1000},
                    {"account_type": "expense", "debit": 600, "credit": 0},
                ],
            },
        ]

        result = service.close_period(
            period_id="APD-001",
            closing_account="ACC-이익잉여금",
        )

        assert result["status"] == "closed"
        assert result["pcv_id"].startswith("PCV-")
        assert result["net_income"] == 400  # 1000 - 600 (Decimal)
        # PCV 생성 검증
        pcv_repo.insert.assert_called_once()
        # 기간 상태 변경 검증 — Outbox 이벤트 포함
        period_repo.update_by_id.assert_called_once()
        call_args = period_repo.update_by_id.call_args
        assert call_args[0][0] == "APD-001"
        assert call_args[0][1]["status"] == "closed"
        assert "_outbox" in call_args[0][1]

    def test_이미마감된_기간_에러(self) -> None:
        service, period_repo, _fy, _je, _pcv = _make_service()
        closed_period = _open_period()
        closed_period["status"] = "closed"
        period_repo.find_by_id.return_value = closed_period

        with pytest.raises(OneERPError, match="ERR-ACCT-035"):
            service.close_period("APD-001", closing_account="ACC-001")

    def test_미제출전표_있으면_마감_실패(self) -> None:
        service, period_repo, _fy, je_repo, _pcv = _make_service()
        period_repo.find_by_id.return_value = _open_period()
        je_repo.find_many.return_value = [
            {"_id": "JE-001", "docstatus": 0},  # DRAFT
        ]

        with pytest.raises(OneERPError, match="ERR-ACCT-033"):
            service.close_period("APD-001", closing_account="ACC-001")


class Test회계연도결산:
    """close_fiscal_year 테스트."""

    def test_회계연도_결산_성공(self) -> None:
        service, period_repo, fy_repo, je_repo, _pcv = _make_service()
        fy_repo.find_by_id.return_value = {
            "_id": "FY-2026",
            "year_name": "2026",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "is_closed": False,
        }
        # 모든 기간 마감됨
        period_repo.find_many.return_value = [
            {"_id": "APD-001", "period_name": "1월", "status": "closed"},
            {"_id": "APD-002", "period_name": "2월", "status": "closed"},
        ]
        je_repo.find_many.return_value = []

        result = service.close_fiscal_year("FY-2026", closing_account="ACC-001")

        assert result["status"] == "closed"
        assert result["closed_periods"] == 2
        # Outbox 이벤트 포함한 update 검증
        fy_repo.update_by_id.assert_called_once()
        call_args = fy_repo.update_by_id.call_args
        assert call_args[0][0] == "FY-2026"
        assert call_args[0][1]["is_closed"] is True
        assert call_args[0][1]["closing_account"] == "ACC-001"
        assert "_outbox" in call_args[0][1]

    def test_미마감기간_있으면_에러(self) -> None:
        service, period_repo, fy_repo, _je, _pcv = _make_service()
        fy_repo.find_by_id.return_value = {
            "_id": "FY-2026",
            "is_closed": False,
        }
        period_repo.find_many.return_value = [
            {"_id": "APD-001", "period_name": "1월", "status": "closed"},
            {"_id": "APD-002", "period_name": "2월", "status": "open"},
        ]

        with pytest.raises(OneERPError, match="ERR-ACCT-034"):
            service.close_fiscal_year("FY-2026", closing_account="ACC-001")

    def test_이미결산된_연도_에러(self) -> None:
        service, _period, fy_repo, _je, _pcv = _make_service()
        fy_repo.find_by_id.return_value = {
            "_id": "FY-2026",
            "is_closed": True,
        }

        with pytest.raises(OneERPError, match="ERR-ACCT-035"):
            service.close_fiscal_year("FY-2026", closing_account="ACC-001")

    def test_연도_미존재_에러(self) -> None:
        service, _period, fy_repo, _je, _pcv = _make_service()
        fy_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.close_fiscal_year("FY-999", closing_account="ACC-001")


class Test손익계산:
    """BR-ACCT-020: 기간 손익 계산 테스트."""

    def test_적자_시나리오_음수_net_income(self) -> None:
        """BR-ACCT-020: 비용이 수익보다 크면 음수 net_income을 반환한다."""
        from decimal import Decimal

        service, period_repo, _fy, je_repo, _pcv = _make_service()
        period_repo.find_by_id.return_value = _open_period()
        # 수익 100,000 < 비용 150,000 → 적자 -50,000
        je_repo.find_many.return_value = [
            {
                "_id": "JE-001",
                "docstatus": 1,
                "items": [
                    {"account_type": "income", "debit": 0, "credit": 100000},
                    {"account_type": "expense", "debit": 150000, "credit": 0},
                ],
            },
        ]

        result = service.close_period("APD-001", closing_account="ACC-이익잉여금")

        assert result["net_income"] == Decimal(-50000)
        assert result["status"] == "closed"

    def test_복합분개_손익(self) -> None:
        """BR-ACCT-020: 수익/비용 계정에 차대변이 모두 있는 복합 분개."""
        from decimal import Decimal

        service, period_repo, _fy, je_repo, _pcv = _make_service()
        period_repo.find_by_id.return_value = _open_period()
        # 수익: credit 100,000 - debit 20,000 = 80,000
        # 비용: debit 80,000 - credit 10,000 = 70,000
        # net_income = 80,000 - 70,000 = 10,000
        je_repo.find_many.return_value = [
            {
                "_id": "JE-CPX",
                "docstatus": 1,
                "items": [
                    {"account_type": "income", "debit": 20000, "credit": 100000},
                    {"account_type": "expense", "debit": 80000, "credit": 10000},
                ],
            },
        ]

        result = service.close_period("APD-001", closing_account="ACC-이익잉여금")

        assert result["net_income"] == Decimal(10000)
