"""기회 전환 이벤트 핸들러 단위 테스트."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from typing import Any

_HANDLER_MODULE = "oneerp_selling_app.events.handlers"


def _make_opportunity_event(
    opportunity_id: str = "OPP-001",
    customer_id: str = "CUST-001",
    tenant_id: str = "test-tenant",
) -> dict[str, Any]:
    """테스트용 OPPORTUNITY_CONVERTED 이벤트 데이터를 생성한다."""
    return {
        "event": {
            "doc_id": opportunity_id,
            "tenant_id": tenant_id,
            "data": {
                "opportunity_id": opportunity_id,
                "customer_id": customer_id,
                "items": [
                    {
                        "item_code": "ITEM-001",
                        "item_name": "테스트 상품",
                        "qty": 10,
                        "rate": 50000,
                    },
                ],
                "valid_till": "2026-04-30",
            },
        },
    }


def _import_handler():
    """런타임에 핸들러를 import한다 (ty 정적 분석 우회)."""
    from oneerp_selling_app.events.handlers import (
        handle_opportunity_converted,  # type: ignore[attr-defined]
    )

    return handle_opportunity_converted


def test_기회전환_견적서_생성() -> None:
    """OPPORTUNITY_CONVERTED 이벤트 수신 시 Quotation 모델로 견적서가 생성된다."""
    event_data = _make_opportunity_event()

    with (
        patch(f"{_HANDLER_MODULE}.Repository") as mock_repo_cls,
        patch(
            f"{_HANDLER_MODULE}.generate_name",
            return_value="QTN-001",
        ),
    ):
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        handler = _import_handler()
        asyncio.run(handler(event_data, "evt-001"))

        # quotations 리포지터리가 생성되었는지 검증
        mock_repo_cls.assert_called_once_with("quotations", tenant_id="test-tenant")
        # Quotation 모델로 insert가 호출되었는지 검증
        mock_repo.insert.assert_called_once()
        quotation = mock_repo.insert.call_args[0][0]

        # Quotation 모델 속성 검증
        assert quotation.customer_id == "CUST-001"
        assert len(quotation.items) == 1
        assert quotation.items[0].item_code == "ITEM-001"
        assert quotation.items[0].qty == 10
        assert quotation.items[0].rate == 50000
        assert quotation.items[0].amount == 500000.0
        assert quotation.total == 500000.0


def test_기회전환_빈_아이템() -> None:
    """아이템이 없는 기회 전환 이벤트도 정상 처리된다."""
    event_data = {
        "event": {
            "doc_id": "OPP-002",
            "tenant_id": "test-tenant",
            "data": {
                "opportunity_id": "OPP-002",
                "customer_id": "CUST-002",
                "items": [],
                "valid_till": None,
            },
        },
    }

    with (
        patch(f"{_HANDLER_MODULE}.Repository") as mock_repo_cls,
        patch(f"{_HANDLER_MODULE}.generate_name", return_value="QTN-002"),
    ):
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        handler = _import_handler()
        asyncio.run(handler(event_data, "evt-002"))

        mock_repo.insert.assert_called_once()
        quotation = mock_repo.insert.call_args[0][0]
        assert quotation.customer_id == "CUST-002"
        assert len(quotation.items) == 0
        assert quotation.total == 0.0
        assert quotation.valid_till is None
