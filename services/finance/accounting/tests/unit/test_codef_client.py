"""CODEF 4대보험 API 클라이언트 단위 테스트."""

from __future__ import annotations

import pytest
from oneerp_accounting_app.config import AccountingSettings
from oneerp_accounting_app.services.codef_client import (
    MockCODEFClient,
    RealCODEFClient,
    create_codef_client,
)


@pytest.fixture
def mock_client() -> MockCODEFClient:
    """MockCODEFClient 인스턴스를 반환한다."""
    return MockCODEFClient()


@pytest.mark.anyio
async def test_mock_get_insurance_status(mock_client: MockCODEFClient) -> None:
    """가입 현황 Mock은 전체 가입 상태를 반환한다."""
    result = await mock_client.get_insurance_status("123-45-67890")
    assert result["business_no"] == "123-45-67890"
    assert result["national_pension"] == "가입"
    assert result["health_insurance"] == "가입"
    assert result["employment_insurance"] == "가입"
    assert result["industrial_accident"] == "가입"


@pytest.mark.anyio
async def test_mock_get_payment_history(mock_client: MockCODEFClient) -> None:
    """납부 내역 Mock은 빈 목록을 반환한다."""
    result = await mock_client.get_payment_history("123-45-67890", year="2026", month="01")
    assert result == []


@pytest.mark.anyio
async def test_mock_get_subscribers(mock_client: MockCODEFClient) -> None:
    """가입자 목록 Mock은 빈 목록을 반환한다."""
    result = await mock_client.get_subscribers("123-45-67890")
    assert result == []


def test_create_codef_client_returns_mock() -> None:
    """API URL 미설정 시 MockCODEFClient를 반환한다."""
    settings = AccountingSettings(codef_api_url="", codef_api_key="", codef_api_secret="")
    client = create_codef_client(settings=settings)
    assert isinstance(client, MockCODEFClient)


def test_create_codef_client_returns_real() -> None:
    """API URL 설정 시 RealCODEFClient를 반환한다."""
    settings = AccountingSettings(
        codef_api_url="https://api.codef.io",
        codef_api_key="test-key",
        codef_api_secret="test-secret",  # noqa: S106
    )
    client = create_codef_client(settings=settings)
    assert isinstance(client, RealCODEFClient)
