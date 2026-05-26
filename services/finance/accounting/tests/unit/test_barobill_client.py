"""바로빌 전자세금계산서 API 클라이언트 단위 테스트."""

from __future__ import annotations

import pytest
from oneerp_accounting_app.config import AccountingSettings
from oneerp_accounting_app.services.barobill_client import (
    MockBarobillClient,
    RealBarobillClient,
    create_barobill_client,
)


@pytest.fixture
def mock_client() -> MockBarobillClient:
    """MockBarobillClient 인스턴스를 반환한다."""
    return MockBarobillClient()


@pytest.mark.anyio
async def test_mock_issue_tax_invoice(mock_client: MockBarobillClient) -> None:
    """발급 Mock은 BB- 접두사 확인번호와 issued 상태를 반환한다."""
    result = await mock_client.issue_tax_invoice({"amount": 10000})
    assert result["status"] == "issued"
    assert result["confirmation_no"].startswith("BB-")
    assert result["message"] == "발급 완료"


@pytest.mark.anyio
async def test_mock_cancel_tax_invoice(mock_client: MockBarobillClient) -> None:
    """취소 Mock은 cancelled 상태를 반환한다."""
    result = await mock_client.cancel_tax_invoice("BB-test1234", "테스트 취소")
    assert result["status"] == "cancelled"
    assert result["confirmation_no"] == "BB-test1234"


@pytest.mark.anyio
async def test_mock_get_status(mock_client: MockBarobillClient) -> None:
    """상태 조회 Mock은 issued 상태를 반환한다."""
    result = await mock_client.get_status("BB-test1234")
    assert result["status"] == "issued"
    assert result["confirmation_no"] == "BB-test1234"


@pytest.mark.anyio
async def test_mock_list_invoices(mock_client: MockBarobillClient) -> None:
    """목록 조회 Mock은 빈 목록을 반환한다."""
    result = await mock_client.list_invoices(start_date="2026-01-01", end_date="2026-01-31")
    assert result == []


def test_create_barobill_client_returns_mock() -> None:
    """API URL 미설정 시 MockBarobillClient를 반환한다."""
    settings = AccountingSettings(barobill_api_url="", barobill_api_key="")
    client = create_barobill_client(settings=settings)
    assert isinstance(client, MockBarobillClient)


def test_create_barobill_client_returns_real() -> None:
    """API URL 설정 시 RealBarobillClient를 반환한다."""
    settings = AccountingSettings(
        barobill_api_url="https://api.barobill.co.kr",
        barobill_api_key="test-key",
    )
    client = create_barobill_client(settings=settings)
    assert isinstance(client, RealBarobillClient)
