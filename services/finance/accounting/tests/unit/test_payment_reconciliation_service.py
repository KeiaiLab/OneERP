"""수금/지급 대사 서비스(PaymentReconciliationService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    """generate_name을 테스트 전체 기간 동안 모킹한다."""
    with patch(
        "oneerp_accounting_app.services.payment_reconciliation_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """PaymentReconciliationService와 모킹된 Repository를 반환한다."""
    with patch(
        "oneerp_accounting_app.services.payment_reconciliation_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_accounting_app.services.payment_reconciliation_service import (
            PaymentReconciliationService,
        )

        service = PaymentReconciliationService(tenant_id="test-tenant")

    return (
        service,
        repos["payment_reconciliations"],
        repos["accounts_receivable"],
        repos["accounts_payable"],
        repos["journal_entries"],
    )


class Test매출채권대사:
    """reconcile_receivables 테스트."""

    def test_금액일치_자동매칭(self) -> None:
        """미수금과 입금 금액이 일치하면 자동 매칭된다."""
        service, prec_repo, ar_repo, _ap, je_repo = _make_service()
        ar_repo.find_many.return_value = [
            {
                "_id": "AREC-001",
                "customer": "CUST-001",
                "outstanding_amount": 1000,
                "invoice_id": "SI-001",
            },
            {
                "_id": "AREC-002",
                "customer": "CUST-001",
                "outstanding_amount": 2000,
                "invoice_id": "SI-002",
            },
        ]
        je_repo.find_many.return_value = [
            {
                "_id": "JE-P01",
                "total_credit": 1000,
                "party": "CUST-001",
                "docstatus": 1,
                "voucher_type": "payment_entry",
            },
        ]

        result = service.reconcile_receivables(
            party="CUST-001",
            from_date="2026-01-01",
            to_date="2026-01-31",
        )

        assert result["matched_count"] == 1
        assert result["total_reconciled"] == 1000.0
        assert len(result["unmatched_invoices"]) == 1  # 2000원 미매칭
        assert len(result["unmatched_payments"]) == 0
        prec_repo.insert.assert_called_once()

    def test_모두매칭(self) -> None:
        """미수금과 입금이 모두 매칭된다."""
        service, _prec, ar_repo, _ap, je_repo = _make_service()
        ar_repo.find_many.return_value = [
            {"_id": "AREC-001", "outstanding_amount": 500, "invoice_id": "SI-001"},
        ]
        je_repo.find_many.return_value = [
            {"_id": "JE-P01", "total_credit": 500, "docstatus": 1, "voucher_type": "payment_entry"},
        ]

        result = service.reconcile_receivables(
            party="CUST-001",
            from_date="2026-01-01",
            to_date="2026-01-31",
        )

        assert result["matched_count"] == 1
        assert result["total_reconciled"] == 500.0
        assert len(result["unmatched_invoices"]) == 0
        assert len(result["unmatched_payments"]) == 0

    def test_미수금_0원_건너뜀(self) -> None:
        """잔액 0원인 미수금은 매칭 대상에서 제외."""
        service, _prec, ar_repo, _ap, je_repo = _make_service()
        ar_repo.find_many.return_value = [
            {"_id": "AREC-001", "outstanding_amount": 0, "invoice_id": "SI-001"},
        ]
        je_repo.find_many.return_value = []

        result = service.reconcile_receivables(
            party="CUST-001",
            from_date="2026-01-01",
            to_date="2026-01-31",
        )

        assert result["matched_count"] == 0


class Test매입채무대사:
    """reconcile_payables 테스트."""

    def test_공급사_자동매칭(self) -> None:
        """미지급금과 출금 금액이 일치하면 자동 매칭된다."""
        service, prec_repo, _ar, ap_repo, je_repo = _make_service()
        ap_repo.find_many.return_value = [
            {
                "_id": "AP-001",
                "supplier": "SUP-001",
                "outstanding_amount": 3000,
                "invoice_id": "PI-001",
            },
        ]
        je_repo.find_many.return_value = [
            {
                "_id": "JE-P01",
                "total_debit": 3000,
                "party": "SUP-001",
                "docstatus": 1,
                "voucher_type": "payment_entry",
            },
        ]

        result = service.reconcile_payables(
            party="SUP-001",
            from_date="2026-01-01",
            to_date="2026-01-31",
        )

        assert result["party_type"] == "Supplier"
        assert result["matched_count"] == 1
        assert result["total_reconciled"] == 3000.0
        prec_repo.insert.assert_called_once()


class Test미대사송장조회:
    """get_unreconciled_invoices 테스트."""

    def test_미수금_미대사_송장(self) -> None:
        service, _prec, ar_repo, _ap, _je = _make_service()
        ar_repo.find_many.return_value = [
            {"_id": "AREC-001", "outstanding_amount": 1000},
            {"_id": "AREC-002", "outstanding_amount": 0},
        ]

        result = service.get_unreconciled_invoices("Customer", "CUST-001")

        assert len(result) == 1
        assert result[0]["_id"] == "AREC-001"

    def test_미지급_미대사_송장(self) -> None:
        service, _prec, _ar, ap_repo, _je = _make_service()
        ap_repo.find_many.return_value = [
            {"_id": "AP-001", "outstanding_amount": 5000},
        ]

        result = service.get_unreconciled_invoices("Supplier", "SUP-001")

        assert len(result) == 1
