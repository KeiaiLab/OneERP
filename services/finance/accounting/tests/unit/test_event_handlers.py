"""Accounting 이벤트 핸들러 단위 테스트."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

# Accounting 핸들러는 모듈 레벨에서 JournalAutoService를 import하므로
# patch 대상은 "oneerp_accounting_app.events.handlers.JournalAutoService" (import된 위치)
_PATCH_TARGET = "oneerp_accounting_app.events.handlers.JournalAutoService"


def _make_event_data(doc_id: str, tenant_id: str = "test") -> dict:
    """테스트용 EventEnvelope 데이터를 생성한다."""
    return {"event": {"doc_id": doc_id, "tenant_id": tenant_id}}


def test_매출전표_이벤트_분개_호출() -> None:
    """매출전표 제출 이벤트 수신 시 매출 분개 생성이 호출되는지 검증."""
    event_data = _make_event_data("SINV-001")

    with patch(_PATCH_TARGET) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.create_sales_invoice_journal.return_value = "JE-001"
        mock_cls.return_value = mock_instance

        from oneerp_accounting_app.events.handlers import handle_sales_invoice_submitted

        asyncio.run(handle_sales_invoice_submitted(event_data, "evt-001"))

        mock_cls.assert_called_once_with("test")
        mock_instance.create_sales_invoice_journal.assert_called_once_with("SINV-001")


def test_매입전표_이벤트_분개_호출() -> None:
    """매입전표 제출 이벤트 수신 시 매입 분개 생성이 호출되는지 검증."""
    event_data = _make_event_data("PINV-001")

    with patch(_PATCH_TARGET) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.create_purchase_invoice_journal.return_value = "JE-002"
        mock_cls.return_value = mock_instance

        from oneerp_accounting_app.events.handlers import handle_purchase_invoice_submitted

        asyncio.run(handle_purchase_invoice_submitted(event_data, "evt-002"))

        mock_cls.assert_called_once_with("test")
        mock_instance.create_purchase_invoice_journal.assert_called_once_with("PINV-001")


def test_결제_이벤트_분개_호출() -> None:
    """수금/지급 전표 제출 이벤트 수신 시 수금/지급 분개 생성이 호출되는지 검증."""
    event_data = _make_event_data("PE-001")

    with patch(_PATCH_TARGET) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.create_payment_journal.return_value = "JE-003"
        mock_cls.return_value = mock_instance

        from oneerp_accounting_app.events.handlers import handle_payment_entry_submitted

        asyncio.run(handle_payment_entry_submitted(event_data, "evt-003"))

        mock_cls.assert_called_once_with("test")
        mock_instance.create_payment_journal.assert_called_once_with("PE-001")


def test_경비승인_이벤트_분개_호출() -> None:
    """경비 청구 승인 이벤트 수신 시 이벤트 기반 경비 분개 생성이 호출되는지 검증."""
    event_data = {
        "event": {
            "doc_id": "EC-001",
            "tenant_id": "test",
            "data": {"total_amount": 350000.0, "posting_date": "2026-03-10"},
        },
    }

    with patch(_PATCH_TARGET) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.create_expense_claim_journal_from_event.return_value = "JE-004"
        mock_cls.return_value = mock_instance

        from oneerp_accounting_app.events.handlers import handle_expense_claim_approved

        asyncio.run(handle_expense_claim_approved(event_data, "evt-004"))

        mock_cls.assert_called_once_with("test")
        mock_instance.create_expense_claim_journal_from_event.assert_called_once()
        # doc_id가 이벤트 데이터에 주입되었는지 검증
        call_data = mock_instance.create_expense_claim_journal_from_event.call_args[0][0]
        assert call_data["doc_id"] == "EC-001"


def test_급여_이벤트_분개_호출() -> None:
    """급여 제출 이벤트 수신 시 이벤트 기반 급여 분개 생성이 호출되는지 검증."""
    event_data = {
        "event": {
            "doc_id": "PAYROLL-001",
            "tenant_id": "test",
            "data": {
                "total_gross": 9000000.0,
                "total_net": 7398000.0,
                "total_employee_insurance": 810000.0,
                "total_employer_insurance": 900000.0,
                "total_income_tax": 720000.0,
                "total_local_income_tax": 72000.0,
                "posting_date": "2026-03-25",
            },
        },
    }

    with patch(_PATCH_TARGET) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.create_payroll_journal_from_event.return_value = "JE-005"
        mock_cls.return_value = mock_instance

        from oneerp_accounting_app.events.handlers import handle_payroll_entry_submitted

        asyncio.run(handle_payroll_entry_submitted(event_data, "evt-005"))

        mock_cls.assert_called_once_with("test")
        mock_instance.create_payroll_journal_from_event.assert_called_once()
        # doc_id가 이벤트 데이터에 주입되었는지 검증
        call_data = mock_instance.create_payroll_journal_from_event.call_args[0][0]
        assert call_data["doc_id"] == "PAYROLL-001"
