"""렌탈 청구 서비스(RentalBillingService) 단위 테스트."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_reservation_app.rental.services.rental_billing_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch(
        "oneerp_reservation_app.rental.services.rental_billing_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_reservation_app.rental.services.rental_billing_service import (
            RentalBillingService,
        )

        service = RentalBillingService(tenant_id="test-tenant")
    return service, repos["rental_orders"], repos["rental_invoices"]


class Test렌탈금액계산:
    """렌탈 금액 계산 테스트."""

    def test_정상_기간_금액_계산(self) -> None:
        service, _order_repo, _inv_repo = _make_service()
        result = service.calculate_rental_amount(
            Decimal(10000),
            date(2026, 1, 1),
            date(2026, 1, 10),
        )
        # 10일 * 10,000 = 100,000
        assert result == Decimal("100000.00")

    def test_하루_렌탈_금액(self) -> None:
        service, _order_repo, _inv_repo = _make_service()
        result = service.calculate_rental_amount(
            Decimal(5000),
            date(2026, 3, 1),
            date(2026, 3, 1),
        )
        # 1일 * 5,000 = 5,000
        assert result == Decimal("5000.00")

    def test_종료일_시작일_이전_에러(self) -> None:
        service, _order_repo, _inv_repo = _make_service()
        with pytest.raises(ValueError, match="종료일이 시작일보다 이전"):
            service.calculate_rental_amount(
                Decimal(10000),
                date(2026, 1, 10),
                date(2026, 1, 1),
            )


class Test연체료계산:
    """연체료 계산 테스트."""

    def test_정상_반납_연체료_없음(self) -> None:
        service, _order_repo, _inv_repo = _make_service()
        result = service.calculate_late_fee(
            Decimal(10000),
            date(2026, 1, 10),
            date(2026, 1, 10),
        )
        assert result == Decimal(0)

    def test_연체_시_연체료_계산(self) -> None:
        service, _order_repo, _inv_repo = _make_service()
        result = service.calculate_late_fee(
            Decimal(10000),
            date(2026, 1, 10),
            date(2026, 1, 13),
        )
        # 3일 * 10,000 * 1.5 = 45,000
        assert result == Decimal("45000.00")

    def test_커스텀_연체_요율(self) -> None:
        service, _order_repo, _inv_repo = _make_service()
        result = service.calculate_late_fee(
            Decimal(10000),
            date(2026, 1, 10),
            date(2026, 1, 12),
            late_fee_rate=Decimal("2.0"),
        )
        # 2일 * 10,000 * 2.0 = 40,000
        assert result == Decimal("40000.00")


class Test청구서생성:
    """주문 기반 청구서 생성 테스트."""

    def test_정상_청구서_생성(self) -> None:
        service, order_repo, inv_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "customer_id": "CUST-001",
            "daily_rate": "10000",
            "start_date": "2026-01-01",
            "end_date": "2026-01-10",
        }

        result = service.create_invoice_from_order("RNORD-001")

        assert result["invoice_id"] == "RNINV-001"
        assert result["rental_amount"] == Decimal("100000.00")
        assert result["tax_amount"] == Decimal("10000.00")
        assert result["total_amount"] == Decimal("110000.00")
        inv_repo.insert.assert_called_once()

    def test_주문_미존재_에러(self) -> None:
        service, order_repo, _inv_repo = _make_service()
        order_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.create_invoice_from_order("RNORD-999")

    def test_청구기간_직접_지정(self) -> None:
        service, order_repo, _inv_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "customer_id": "CUST-001",
            "daily_rate": "20000",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        }

        result = service.create_invoice_from_order(
            "RNORD-001",
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 7),
            tax_rate=Decimal("0.1"),
        )

        # 7일 * 20,000 = 140,000 + 세금 14,000 = 154,000
        assert result["rental_amount"] == Decimal("140000.00")
        assert result["total_amount"] == Decimal("154000.00")

    def test_청구기간_없으면_에러(self) -> None:
        service, order_repo, _inv_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "customer_id": "CUST-001",
            "daily_rate": "10000",
        }

        with pytest.raises(ValueError, match="청구 기간"):
            service.create_invoice_from_order("RNORD-001")
