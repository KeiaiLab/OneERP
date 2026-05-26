"""부가세 신고(VAT Return) 워크벤치 엔드포인트 단위 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from oneerp_accounting_app.main import app
from oneerp_core.document import DocStatus

client = TestClient(app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)


_BASE_URL = "/api/v1/vat-returns"


def _make_cursor(items: list[dict]) -> MagicMock:
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.sort.return_value = cursor
    cursor.__iter__.return_value = iter(items)
    return cursor


def test_부가세신고_생성은_워크벤치_요약과_제출가이드를_반환한다(
    mock_collection: MagicMock,
) -> None:
    """POST /api/v1/vat-returns — 생성 시 자동 합계/제출 가이드를 함께 반환해야 한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="VAT-2026-00001")
    mock_collection.find.return_value = _make_cursor([])
    mock_collection.find_one.return_value = {
        "_id": "VAT-2026-00001",
        "period": "2026-Q1",
        "output_tax": 3000000,
        "input_tax": 2000000,
        "net_tax": 1000000,
        "tax_amount": 1000000,
        "status": "draft",
        "tenant_id": "test-tenant",
        "docstatus": DocStatus.DRAFT,
    }
    response = client.post(
        _BASE_URL,
        json={
            "period": "2026-Q1",
            "output_tax": 3000000,
            "input_tax": 2000000,
            "net_tax": 1000000,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == "VAT-2026-00001"
    assert payload["period"] == "2026-Q1"
    assert payload["status_badge"] == "draft_payable"
    assert payload["recommended_action"] == "submit_vat_return"
    assert payload["period_scope_summary"] == {
        "period": "2026-Q1",
        "period_start": "2026-01-01",
        "period_end": "2026-03-31",
        "filing_cycle": "quarterly",
        "due_date": "2026-04-25",
    }
    assert payload["tax_summary"] == {
        "output_tax": 3000000.0,
        "input_tax": 2000000.0,
        "net_tax": 1000000.0,
        "payable_tax": 1000000.0,
        "refundable_tax": 0.0,
    }
    assert payload["invoice_sync_summary"] == {
        "issued_count": 0,
        "transmitted_count": 0,
        "pending_count": 0,
        "failed_count": 0,
    }
    assert payload["available_actions"] == [
        "edit",
        "preview_filing",
        "submit",
        "open_etax_invoices",
    ]


def test_부가세신고_목록은_워크벤치_요약과_상태배지를_반환한다(
    mock_collection: MagicMock,
) -> None:
    """GET /api/v1/vat-returns — 목록은 신고 요약/상태 배지/필터 결과를 제공해야 한다."""
    mock_collection.find.side_effect = [
        _make_cursor(
            [
                {
                    "_id": "VAT-2026-00001",
                    "period": "2026-Q1",
                    "output_tax": 3000000,
                    "input_tax": 2000000,
                    "net_tax": 1000000,
                    "tax_amount": 1000000,
                    "status": "draft",
                    "tenant_id": "test-tenant",
                    "docstatus": DocStatus.DRAFT,
                },
                {
                    "_id": "VAT-2026-00002",
                    "period": "2026-Q2",
                    "output_tax": 1500000,
                    "input_tax": 1800000,
                    "net_tax": -300000,
                    "tax_amount": -300000,
                    "status": "submitted",
                    "filing_date": date(2026, 7, 20),
                    "tenant_id": "test-tenant",
                    "docstatus": DocStatus.SUBMITTED,
                },
            ]
        ),
        _make_cursor([]),
        _make_cursor([]),
    ]
    mock_collection.count_documents.return_value = 2
    response = client.get(f"{_BASE_URL}?page=1&page_size=10&status_badge=draft_payable")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"] == {
        "draft_count": 1,
        "submitted_count": 0,
        "cancelled_count": 0,
        "payable_count": 1,
        "refund_count": 0,
        "overdue_count": 0,
    }
    assert payload["data"][0]["_id"] == "VAT-2026-00001"
    assert payload["data"][0]["status_badge"] == "draft_payable"
    assert payload["data"][0]["recommended_action"] == "submit_vat_return"


def test_부가세신고_상세는_전자세금계산서_연계와_권장액션을_반환한다(
    mock_collection: MagicMock,
) -> None:
    """GET /api/v1/vat-returns/{doc_id}/summary — 신고 상세는 세액/전자세금계산서/가이드를 노출해야 한다."""
    mock_collection.find_one.return_value = {
        "_id": "VAT-2026-00001",
        "period": "2026-Q1",
        "net_tax": 1000000,
        "output_tax": 3000000,
        "input_tax": 2000000,
        "tax_amount": 1000000,
        "status": "submitted",
        "filing_date": date(2026, 4, 23),
        "tenant_id": "test-tenant",
        "docstatus": DocStatus.SUBMITTED,
    }
    mock_collection.find.return_value = _make_cursor(
        [
            {"_id": "ETAX-001", "transmission_status": "pending"},
            {"_id": "ETAX-002", "transmission_status": "transmitted"},
        ]
    )
    response = client.get(f"{_BASE_URL}/VAT-2026-00001/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "submitted_payable"
    assert payload["recommended_action"] == "schedule_tax_payment"
    assert payload["tax_summary"]["payable_tax"] == 1000000.0
    assert payload["invoice_sync_summary"] == {
        "issued_count": 2,
        "transmitted_count": 1,
        "pending_count": 1,
        "failed_count": 0,
    }
    assert payload["available_actions"] == [
        "view_filing_history",
        "open_etax_invoices",
        "schedule_tax_payment",
        "cancel",
    ]


def test_부가세신고_요약_조회_404(mock_collection: MagicMock) -> None:
    """GET /api/v1/vat-returns/{doc_id}/summary — 미존재 시 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = client.get(f"{_BASE_URL}/NONEXISTENT/summary")
    assert response.status_code == 404


def test_부가세신고_제출(mock_collection: MagicMock) -> None:
    """POST /api/v1/vat-returns/{doc_id}/submit — 초안 신고를 제출한다."""
    mock_collection.find_one.return_value = {
        "_id": "VAT-2026-00001",
        "period": "2026-Q1",
        "net_tax": 1000000,
        "output_tax": 3000000,
        "input_tax": 2000000,
        "status": "draft",
        "docstatus": DocStatus.DRAFT,
        "tenant_id": "test-tenant",
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    mock_collection.find.side_effect = [_make_cursor([]), _make_cursor([])]
    response = client.post(f"{_BASE_URL}/VAT-2026-00001/submit")
    assert response.status_code == 200
    payload = response.json()
    assert payload["docstatus"] == DocStatus.SUBMITTED
    assert payload["status"] == "submitted"
    assert payload["status_badge"] == "submitted_payable"


def test_부가세신고_취소(mock_collection: MagicMock) -> None:
    """POST /api/v1/vat-returns/{doc_id}/cancel — 제출된 신고를 취소한다."""
    mock_collection.find_one.return_value = {
        "_id": "VAT-2026-00001",
        "period": "2026-Q1",
        "net_tax": 1000000,
        "output_tax": 3000000,
        "input_tax": 2000000,
        "status": "submitted",
        "docstatus": DocStatus.SUBMITTED,
        "tenant_id": "test-tenant",
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    mock_collection.find.side_effect = [_make_cursor([]), _make_cursor([])]
    response = client.post(f"{_BASE_URL}/VAT-2026-00001/cancel")
    assert response.status_code == 200
    payload = response.json()
    assert payload["docstatus"] == DocStatus.CANCELLED
    assert payload["status"] == "cancelled"
    assert payload["status_badge"] == "cancelled"
