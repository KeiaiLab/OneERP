"""POS 거래(POSTransaction) 불변성(BR-SELL-011) 테스트.

제출된(docstatus=1) POS 거래는 수정/삭제가 차단되어야 한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from oneerp_core.document import DocStatus

_BASE_URL = "/api/v1/pos-transactions"


# ── 제출된 POS 거래 수정 차단 ──────────────────────────────────


def test_제출된_POS거래_수정_거부(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """PUT /{doc_id} -- 제출된(docstatus=1) POS 거래는 수정을 거부한다 (BR-SELL-011)."""
    mock_collection.find_one.return_value = {
        "_id": "PTXN-2026-00001",
        "tenant_id": "test-tenant",
        "docstatus": DocStatus.SUBMITTED,
        "items": [],
    }
    response = test_client.put(
        f"{_BASE_URL}/PTXN-2026-00001",
        json={"customer_name": "변경 시도"},
    )
    assert response.status_code == 400
    assert "수정/삭제할 수 없습니다" in response.json()["detail"]


def test_제출된_POS거래_삭제_거부(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """DELETE /{doc_id} -- 제출된(docstatus=1) POS 거래는 삭제를 거부한다 (BR-SELL-011)."""
    mock_collection.find_one.return_value = {
        "_id": "PTXN-2026-00001",
        "tenant_id": "test-tenant",
        "docstatus": DocStatus.SUBMITTED,
        "items": [],
    }
    response = test_client.delete(f"{_BASE_URL}/PTXN-2026-00001")
    assert response.status_code == 400
    assert "수정/삭제할 수 없습니다" in response.json()["detail"]


# ── 초안 POS 거래는 수정/삭제 허용 ──────────────────────────────


def test_초안_POS거래_수정_허용(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """PUT /{doc_id} -- 초안(docstatus=0) POS 거래는 수정을 허용한다."""
    mock_collection.find_one.return_value = {
        "_id": "PTXN-2026-00002",
        "tenant_id": "test-tenant",
        "docstatus": DocStatus.DRAFT,
        "items": [],
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = test_client.put(
        f"{_BASE_URL}/PTXN-2026-00002",
        json={"customer_name": "변경 허용"},
    )
    assert response.status_code == 200


def test_초안_POS거래_삭제_허용(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """DELETE /{doc_id} -- 초안(docstatus=0) POS 거래는 삭제를 허용한다."""
    mock_collection.find_one.return_value = {
        "_id": "PTXN-2026-00003",
        "tenant_id": "test-tenant",
        "docstatus": DocStatus.DRAFT,
        "items": [],
    }
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
    response = test_client.delete(f"{_BASE_URL}/PTXN-2026-00003")
    assert response.status_code == 204
