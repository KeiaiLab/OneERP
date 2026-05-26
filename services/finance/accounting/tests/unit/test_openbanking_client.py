"""금융결제원 오픈뱅킹 API 클라이언트 단위 테스트."""

from __future__ import annotations

import pytest
from oneerp_accounting_app.config import AccountingSettings
from oneerp_accounting_app.services.openbanking_client import (
    MockOpenBankingClient,
    RealOpenBankingClient,
    create_openbanking_client,
)


@pytest.fixture
def mock_client() -> MockOpenBankingClient:
    """MockOpenBankingClient 인스턴스를 반환한다."""
    return MockOpenBankingClient()


@pytest.mark.anyio
async def test_mock_get_accounts(mock_client: MockOpenBankingClient) -> None:
    """계좌 목록 조회 Mock은 샘플 계좌 1건을 반환한다."""
    result = await mock_client.get_accounts("test-user-seq")
    assert len(result) == 1
    assert result[0]["bank_name"] == "KB국민은행"
    assert result[0]["fintech_use_num"].startswith("MOCK-")


@pytest.mark.anyio
async def test_mock_get_transactions(mock_client: MockOpenBankingClient) -> None:
    """거래내역 조회 Mock은 빈 목록을 반환한다."""
    result = await mock_client.get_transactions(
        "MOCK-fintech", from_date="2026-01-01", to_date="2026-01-31"
    )
    assert result == []


@pytest.mark.anyio
async def test_mock_get_balance(mock_client: MockOpenBankingClient) -> None:
    """잔액 조회 Mock은 0원 잔액을 반환한다."""
    result = await mock_client.get_balance("MOCK-fintech")
    assert result["balance_amount"] == 0
    assert result["currency"] == "KRW"


@pytest.mark.anyio
async def test_mock_transfer(mock_client: MockOpenBankingClient) -> None:
    """이체 Mock은 성공 응답과 이체번호를 반환한다."""
    result = await mock_client.transfer(
        from_fintech_use_num="MOCK-from",
        to_bank_code="004",
        to_account_num="1234567890",
        amount=50000,
        memo="테스트 이체",
    )
    assert result["status"] == "completed"
    assert result["transfer_no"].startswith("TRF-")
    assert result["amount"] == 50000


def test_create_openbanking_client_returns_mock() -> None:
    """API URL 미설정 시 MockOpenBankingClient를 반환한다."""
    settings = AccountingSettings(
        openbanking_api_url="",
        openbanking_client_id="",
        openbanking_client_secret="",
    )
    client = create_openbanking_client(settings=settings)
    assert isinstance(client, MockOpenBankingClient)


def test_create_openbanking_client_returns_real() -> None:
    """API URL 설정 시 RealOpenBankingClient를 반환한다."""
    settings = AccountingSettings(
        openbanking_api_url="https://openapi.openbanking.or.kr",
        openbanking_client_id="test-id",
        openbanking_client_secret="test-secret",  # noqa: S106
    )
    client = create_openbanking_client(settings=settings)
    assert isinstance(client, RealOpenBankingClient)
