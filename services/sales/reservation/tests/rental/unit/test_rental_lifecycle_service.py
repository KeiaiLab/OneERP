"""렌탈 생명주기 서비스(RentalLifecycleService) 단위 테스트."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_reservation_app.rental.services.rental_lifecycle_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch(
        "oneerp_reservation_app.rental.services.rental_lifecycle_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_reservation_app.rental.services.rental_lifecycle_service import (
            RentalLifecycleService,
        )

        service = RentalLifecycleService(tenant_id="test-tenant")
    return (
        service,
        repos["rental_orders"],
        repos["rental_items"],
        repos["rental_returns"],
    )


class Test렌탈시작:
    """렌탈 시작 처리 테스트."""

    def test_정상_렌탈_시작(self) -> None:
        service, order_repo, item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "rental_item_id": "RNITM-001",
            "status": "confirmed",
        }
        item_repo.find_by_id.return_value = {
            "_id": "RNITM-001",
            "status": "available",
        }

        result = service.start_rental("RNORD-001")

        assert result["status"] == "active"
        order_repo.update_by_id.assert_called_once_with("RNORD-001", {"status": "active"})
        item_repo.update_by_id.assert_called_once_with("RNITM-001", {"status": "rented"})

    def test_이미_활성_주문_시작_에러(self) -> None:
        service, order_repo, _item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "status": "active",
        }

        with pytest.raises(ValueError, match="시작할 수 없습니다"):
            service.start_rental("RNORD-001")

    def test_주문_미존재_에러(self) -> None:
        service, order_repo, _item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.start_rental("RNORD-999")

    def test_품목_비가용_에러(self) -> None:
        service, order_repo, item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "rental_item_id": "RNITM-001",
            "status": "draft",
        }
        item_repo.find_by_id.return_value = {
            "_id": "RNITM-001",
            "status": "rented",
        }

        with pytest.raises(ValueError, match="대여할 수 없습니다"):
            service.start_rental("RNORD-001")

    def test_품목_없는_주문_시작(self) -> None:
        service, order_repo, item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "rental_item_id": "",
            "status": "draft",
        }

        result = service.start_rental("RNORD-001")

        assert result["status"] == "active"
        item_repo.find_by_id.assert_not_called()


class Test반납처리:
    """반납 처리 테스트."""

    def test_정상_반납(self) -> None:
        service, order_repo, item_repo, return_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "rental_item_id": "RNITM-001",
            "status": "active",
            "end_date": "2026-01-10",
            "daily_rate": "10000",
            "deposit_amount": "50000",
        }

        result = service.process_return(
            "RNORD-001",
            return_date=date(2026, 1, 10),
        )

        assert result["return_id"] == "RNRET-001"
        assert result["late_fee"] == Decimal(0)
        assert result["deposit_refund"] == Decimal(50000)
        return_repo.insert.assert_called_once()
        order_repo.update_by_id.assert_called_once_with("RNORD-001", {"status": "returned"})
        item_repo.update_by_id.assert_called_once_with("RNITM-001", {"status": "available"})

    def test_연체_반납_연체료_계산(self) -> None:
        service, order_repo, _item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "rental_item_id": "RNITM-001",
            "status": "active",
            "end_date": "2026-01-10",
            "daily_rate": "10000",
            "deposit_amount": "50000",
        }

        result = service.process_return(
            "RNORD-001",
            return_date=date(2026, 1, 13),
        )

        # 3일 * 10,000 * 1.5 = 45,000
        assert result["late_fee"] == Decimal("45000.00")

    def test_손상_반납_품목_유지보수_상태(self) -> None:
        service, order_repo, item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "rental_item_id": "RNITM-001",
            "status": "active",
            "end_date": "2026-01-10",
            "daily_rate": "10000",
            "deposit_amount": "50000",
        }

        result = service.process_return(
            "RNORD-001",
            return_date=date(2026, 1, 10),
            condition="damaged",
            damage_charge=Decimal(20000),
        )

        assert result["deposit_refund"] == Decimal(30000)
        item_repo.update_by_id.assert_called_once_with("RNITM-001", {"status": "maintenance"})

    def test_분실_반납_보증금_미환불(self) -> None:
        service, order_repo, item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "rental_item_id": "RNITM-001",
            "status": "active",
            "end_date": "2026-01-10",
            "daily_rate": "10000",
            "deposit_amount": "50000",
        }

        result = service.process_return(
            "RNORD-001",
            return_date=date(2026, 1, 10),
            condition="lost",
        )

        assert result["deposit_refund"] == Decimal(0)
        item_repo.update_by_id.assert_called_once_with("RNITM-001", {"status": "retired"})

    def test_비활성_주문_반납_에러(self) -> None:
        service, order_repo, _item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "status": "draft",
        }

        with pytest.raises(ValueError, match="반납할 수 없습니다"):
            service.process_return("RNORD-001")


class Test기간연장:
    """렌탈 기간 연장 테스트."""

    def test_정상_연장(self) -> None:
        service, order_repo, _item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "status": "active",
            "start_date": "2026-01-01",
            "end_date": "2026-01-10",
            "daily_rate": "10000",
        }

        result = service.extend_rental("RNORD-001", new_end_date=date(2026, 1, 20))

        # 20일 * 10,000 = 200,000
        assert result["new_total_amount"] == Decimal("200000.00")
        assert result["new_end_date"] == date(2026, 1, 20)
        order_repo.update_by_id.assert_called_once()

    def test_이전_날짜_연장_에러(self) -> None:
        service, order_repo, _item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "status": "active",
            "start_date": "2026-01-01",
            "end_date": "2026-01-10",
            "daily_rate": "10000",
        }

        with pytest.raises(ValueError, match="이후여야 합니다"):
            service.extend_rental("RNORD-001", new_end_date=date(2026, 1, 5))

    def test_주문_미존재_에러(self) -> None:
        service, order_repo, _item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.extend_rental("RNORD-999", new_end_date=date(2026, 1, 20))

    def test_반납_상태_연장_에러(self) -> None:
        service, order_repo, _item_repo, _ret_repo = _make_service()
        order_repo.find_by_id.return_value = {
            "_id": "RNORD-001",
            "status": "returned",
        }

        with pytest.raises(ValueError, match="연장할 수 없습니다"):
            service.extend_rental("RNORD-001", new_end_date=date(2026, 1, 20))
