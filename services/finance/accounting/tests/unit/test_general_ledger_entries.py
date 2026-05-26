"""총계정원장(General Ledger) 조회 엔드포인트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from oneerp_accounting_app.main import app

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


_BASE_URL = "/api/v1/general-ledger-entries"


def _cursor_with_docs(*docs: dict) -> MagicMock:
    """Repository.find_many 응답용 커서를 구성한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(return_value=iter(list(docs)))
    return mock_cursor


def test_총계정원장_목록은_제출된_분개전표에서_파생되고_잔액을_계산한다(
    mock_collection: MagicMock,
) -> None:
    """GET /api/v1/general-ledger-entries — 계정/기간 필터와 running balance를 계산한다."""
    mock_collection.find.return_value = _cursor_with_docs(
        {
            "_id": "JE-2026-00001",
            "posting_date": "2026-02-28",
            "voucher_type": "journal_entry",
            "voucher_no": "MANUAL-OPEN",
            "remark": "이월",
            "docstatus": 1,
            "items": [
                {"idx": 1, "account": "현금", "debit": 300, "credit": 0},
                {"idx": 2, "account": "이익잉여금", "debit": 0, "credit": 300},
            ],
        },
        {
            "_id": "JE-2026-00002",
            "posting_date": "2026-03-05",
            "voucher_type": "sales_invoice",
            "voucher_no": "SI-2026-00001",
            "remark": "매출 인식",
            "docstatus": 1,
            "items": [
                {"idx": 1, "account": "현금", "debit": 0, "credit": 120},
                {"idx": 2, "account": "매출", "debit": 120, "credit": 0},
            ],
        },
        {
            "_id": "JE-2026-00003",
            "posting_date": "2026-03-10",
            "voucher_type": "journal_entry",
            "voucher_no": "JE-2026-00003",
            "remark": "현금 유입",
            "docstatus": 1,
            "items": [
                {
                    "idx": 1,
                    "account": "현금",
                    "debit": 500,
                    "credit": 0,
                    "cost_center": "CC-001",
                    "party_type": "customer",
                    "party": "CUST-001",
                },
                {"idx": 2, "account": "매출", "debit": 0, "credit": 500},
            ],
        },
        {
            "_id": "JE-2026-00004",
            "posting_date": "2026-03-15",
            "voucher_type": "journal_entry",
            "voucher_no": "JE-2026-00004",
            "remark": "초안 전표",
            "docstatus": 0,
            "items": [
                {"idx": 1, "account": "현금", "debit": 999, "credit": 0},
                {"idx": 2, "account": "매출", "debit": 0, "credit": 999},
            ],
        },
    )
    response = client.get(
        f"{_BASE_URL}?account=현금&posting_date_from=2026-03-01&posting_date_to=2026-03-31"
        "&page=1&page_size=10"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["data"]) == 2
    assert data["summary"] == {
        "opening_balance": 300.0,
        "total_debit": 500.0,
        "total_credit": 120.0,
        "closing_balance": 680.0,
    }

    first, second = data["data"]
    assert first["entry_id"] == "JE-2026-00002:1"
    assert first["voucher_no"] == "SI-2026-00001"
    assert first["running_balance"] == 180.0
    assert second["entry_id"] == "JE-2026-00003:1"
    assert second["cost_center"] == "CC-001"
    assert second["running_balance"] == 680.0


def test_총계정원장_목록은_원천유형과_원가센터로_필터한다(
    mock_collection: MagicMock,
) -> None:
    """GET /api/v1/general-ledger-entries — 다축 필터로 대상 라인만 조회한다."""
    mock_collection.find.return_value = _cursor_with_docs(
        {
            "_id": "JE-2026-00011",
            "posting_date": "2026-03-20",
            "voucher_type": "journal_entry",
            "voucher_no": "JE-2026-00011",
            "remark": "본사 조정",
            "docstatus": 1,
            "items": [
                {"idx": 1, "account": "현금", "debit": 100, "credit": 0, "cost_center": "CC-HQ"},
                {"idx": 2, "account": "매출", "debit": 0, "credit": 100, "cost_center": "CC-HQ"},
            ],
        },
        {
            "_id": "JE-2026-00012",
            "posting_date": "2026-03-21",
            "voucher_type": "sales_invoice",
            "voucher_no": "SI-2026-00012",
            "remark": "프로젝트 매출",
            "docstatus": 1,
            "items": [
                {"idx": 1, "account": "현금", "debit": 220, "credit": 0, "cost_center": "CC-PRJ"},
                {"idx": 2, "account": "매출", "debit": 0, "credit": 220, "cost_center": "CC-PRJ"},
            ],
        },
        {
            "_id": "JE-2026-00013",
            "posting_date": "2026-03-22",
            "voucher_type": "sales_invoice",
            "voucher_no": "SI-2026-00013",
            "remark": "다른 거래처 매출",
            "docstatus": 1,
            "items": [
                {"idx": 1, "account": "현금", "debit": 330, "credit": 0, "cost_center": "CC-OPS"},
                {"idx": 2, "account": "매출", "debit": 0, "credit": 330, "cost_center": "CC-OPS"},
            ],
        },
    )

    response = client.get(f"{_BASE_URL}?account=현금&voucher_type=sales_invoice&cost_center=CC-PRJ")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"] == {
        "opening_balance": 0.0,
        "total_debit": 220.0,
        "total_credit": 0.0,
        "closing_balance": 220.0,
    }
    assert payload["data"][0]["journal_entry_id"] == "JE-2026-00012"
    assert payload["data"][0]["voucher_type"] == "sales_invoice"
    assert payload["data"][0]["cost_center"] == "CC-PRJ"


def test_총계정원장_단건_조회는_전표라인_드릴다운을_지원한다(mock_collection: MagicMock) -> None:
    """GET /api/v1/general-ledger-entries/{entry_id} — JE 라인 상세를 반환한다."""
    mock_collection.find.return_value = _cursor_with_docs(
        {
            "_id": "JE-2026-00021",
            "posting_date": "2026-03-18",
            "voucher_type": "journal_entry",
            "voucher_no": "JE-2026-00021",
            "remark": "현금 조정",
            "docstatus": 1,
            "items": [
                {"idx": 1, "account": "현금", "debit": 1000, "credit": 0},
                {"idx": 2, "account": "잡이익", "debit": 0, "credit": 1000},
            ],
        }
    )
    response = client.get(f"{_BASE_URL}/JE-2026-00021:1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["entry_id"] == "JE-2026-00021:1"
    assert payload["journal_entry_id"] == "JE-2026-00021"
    assert payload["account"] == "현금"
    assert payload["running_balance"] == 1000.0


def test_총계정원장_조회_404(mock_collection: MagicMock) -> None:
    """GET /api/v1/general-ledger-entries/{entry_id} — 미존재 시 404를 반환한다."""
    mock_collection.find.return_value = _cursor_with_docs()
    response = client.get(f"{_BASE_URL}/NONEXISTENT")
    assert response.status_code == 404


def test_총계정원장은_수동_생성을_허용하지_않는다() -> None:
    """POST /api/v1/general-ledger-entries — 읽기 전용 조회 기능이므로 405를 반환한다."""
    response = client.post(_BASE_URL, json={})
    assert response.status_code == 405
