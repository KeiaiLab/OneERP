"""MRP 순소요량 서비스(MRPNetRequirementService) 단위 테스트.

calculate_net_requirements, explode_single_item 메서드의
정상·예외·경계값·다단계 시나리오를 검증한다.
"""

from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@contextmanager
def _service_context(
    *,
    forecast: dict | None = None,
    boms_by_item: dict[str, list[dict]] | None = None,
    bins_by_item: dict[str, list[dict]] | None = None,
    pos: list[dict] | None = None,
    wos: list[dict] | None = None,
):
    """mock 컨텍스트와 서비스 인스턴스를 yield한다."""
    with patch(
        "oneerp_manufacturing_app.services.mrp_net_requirement_service.Repository",
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}
        bom_lookup = boms_by_item or {}
        bin_lookup = bins_by_item or {}
        po_list = pos or []
        wo_list = wos or []

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            if collection_name in repos:
                return repos[collection_name]
            repo = MagicMock()
            repos[collection_name] = repo

            if collection_name == "demand_forecasts":
                repo.find_by_id.return_value = forecast
            elif collection_name == "boms":

                def _bom_find(query, limit=1, **kwargs):
                    item = query.get("item_code", "")
                    return bom_lookup.get(item, [])

                repo.find_many.side_effect = _bom_find
            elif collection_name == "stock_bins":

                def _bin_find(query, limit=100, **kwargs):
                    item = query.get("item_code", "")
                    return bin_lookup.get(item, [])

                repo.find_many.side_effect = _bin_find
            elif collection_name == "purchase_orders":
                repo.find_many.return_value = po_list
            elif collection_name == "work_orders":

                def _wo_find(query, limit=200, **kwargs):
                    # status 필터에 따라 분기
                    status_filter = query.get("status")
                    if status_filter == "in_progress":
                        return [w for w in wo_list if w.get("status") == "in_progress"]
                    if isinstance(status_filter, dict) and "$in" in status_filter:
                        # scheduled receipts 조회: item_code+status
                        item_filter = query.get("item_code", "")
                        return [
                            w
                            for w in wo_list
                            if w.get("item_code") == item_filter
                            and w.get("status") in status_filter["$in"]
                        ]
                    return wo_list

                repo.find_many.side_effect = _wo_find

            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_manufacturing_app.services.mrp_net_requirement_service import (
            MRPNetRequirementService,
        )

        service = MRPNetRequirementService(tenant_id="test-tenant")
        yield service, repos


# ======================================================================
# 정상 케이스
# ======================================================================


class TestMRP순소요_정상:
    """순소요량 계산 정상 시나리오."""

    def test_단일_품목_BOM없음_구매(self) -> None:
        """BOM이 없는 자재는 구매로 분류."""
        forecast = {
            "_id": "DFST-001",
            "items": [{"item_code": "MAT-A", "qty": 100}],
        }
        bins_by_item = {"MAT-A": [{"current_qty": 30, "current_value": 0}]}

        with _service_context(forecast=forecast, bins_by_item=bins_by_item) as (
            service,
            _repos,
        ):
            result = service.calculate_net_requirements("DFST-001")

            assert len(result["net_requirements"]) == 1
            req = result["net_requirements"][0]
            assert req["item_code"] == "MAT-A"
            assert req["gross"] == Decimal(100)
            assert req["on_hand"] == Decimal(30)
            assert req["net"] == Decimal(70)
            assert req["action"] == "purchase"
            assert result["purchase_count"] == 1
            assert result["manufacture_count"] == 0

    def test_BOM있는_품목_제조(self) -> None:
        """BOM이 있는 품목은 제조로 분류 + 자재 폭발."""
        forecast = {
            "_id": "DFST-001",
            "items": [{"item_code": "FG-001", "qty": 10}],
        }
        boms_by_item = {
            "FG-001": [
                {
                    "_id": "BOM-001",
                    "item_code": "FG-001",
                    "quantity": 1,
                    "is_default": True,
                    "items": [{"item_code": "RAW-1", "qty": 5, "rate": 0}],
                }
            ]
        }

        with _service_context(forecast=forecast, boms_by_item=boms_by_item) as (
            service,
            _repos,
        ):
            result = service.calculate_net_requirements("DFST-001")

            # FG-001: 10개 (재고 0) → manufacture
            # RAW-1: 50개 (재고 0) → purchase
            codes = {req["item_code"]: req for req in result["net_requirements"]}
            assert "FG-001" in codes
            assert "RAW-1" in codes
            assert codes["FG-001"]["action"] == "manufacture"
            assert codes["FG-001"]["net"] == Decimal(10)
            assert codes["RAW-1"]["action"] == "purchase"
            assert codes["RAW-1"]["net"] == Decimal(50)

    def test_재고_충분시_제외(self) -> None:
        """on_hand >= gross이면 net <= 0이므로 제외 (BR-MFG-013)."""
        forecast = {
            "_id": "DFST-001",
            "items": [{"item_code": "MAT-A", "qty": 50}],
        }
        bins_by_item = {"MAT-A": [{"current_qty": 100, "current_value": 0}]}

        with _service_context(forecast=forecast, bins_by_item=bins_by_item) as (
            service,
            _repos,
        ):
            result = service.calculate_net_requirements("DFST-001")
            assert len(result["net_requirements"]) == 0


# ======================================================================
# Scheduled Receipts / Allocations
# ======================================================================


class TestMRP순소요_가용:
    """scheduled receipts와 allocations 처리."""

    def test_PO_미입고분_가용으로_가산(self) -> None:
        """PO의 미입고 라인을 scheduled에 가산."""
        forecast = {
            "_id": "DFST-001",
            "items": [{"item_code": "MAT-A", "qty": 100}],
        }
        bins_by_item = {"MAT-A": [{"current_qty": 30, "current_value": 0}]}
        pos = [
            {
                "status": "submitted",
                "items": [{"item_code": "MAT-A", "qty": 40}],
            }
        ]

        with _service_context(forecast=forecast, bins_by_item=bins_by_item, pos=pos) as (
            service,
            _repos,
        ):
            result = service.calculate_net_requirements("DFST-001")

            req = result["net_requirements"][0]
            assert req["scheduled"] == Decimal(40)
            # net = 100 - (30 + 40) = 30
            assert req["net"] == Decimal(30)

    def test_in_progress_WO_할당으로_가산(self) -> None:
        """진행 중 WO의 required_materials를 allocations에 가산."""
        forecast = {
            "_id": "DFST-001",
            "items": [{"item_code": "MAT-A", "qty": 100}],
        }
        bins_by_item = {"MAT-A": [{"current_qty": 100, "current_value": 0}]}
        wos = [
            {
                "_id": "WO-1",
                "status": "in_progress",
                "required_materials": [{"item_code": "MAT-A", "required_qty": 30}],
            }
        ]

        with _service_context(forecast=forecast, bins_by_item=bins_by_item, wos=wos) as (
            service,
            _repos,
        ):
            result = service.calculate_net_requirements("DFST-001")

            req = result["net_requirements"][0]
            assert req["allocated"] == Decimal(30)
            # net = (100+30) - (100+0) = 30
            assert req["net"] == Decimal(30)

    def test_옵션_비활성_시_무시(self) -> None:
        """consider_scheduled_receipts=False, consider_allocations=False."""
        forecast = {
            "_id": "DFST-001",
            "items": [{"item_code": "MAT-A", "qty": 100}],
        }
        bins_by_item = {"MAT-A": [{"current_qty": 30, "current_value": 0}]}
        pos = [
            {
                "status": "submitted",
                "items": [{"item_code": "MAT-A", "qty": 40}],
            }
        ]

        with _service_context(forecast=forecast, bins_by_item=bins_by_item, pos=pos) as (
            service,
            _repos,
        ):
            result = service.calculate_net_requirements(
                "DFST-001",
                consider_scheduled_receipts=False,
                consider_allocations=False,
            )

            req = result["net_requirements"][0]
            assert req["scheduled"] == Decimal(0)
            assert req["allocated"] == Decimal(0)
            # net = 100 - 30 = 70
            assert req["net"] == Decimal(70)


# ======================================================================
# 단일 폭발 (explode_single_item)
# ======================================================================


class TestMRP폭발:
    """explode_single_item 메서드."""

    def test_BOM없는_품목_자체만_누적(self) -> None:
        """BOM이 없으면 본인만 누적."""
        with _service_context() as (service, _repos):
            result = service.explode_single_item("MAT-A", Decimal(50))
            assert result == {"MAT-A": Decimal(50)}

    def test_BOM_있는_품목_재귀_폭발(self) -> None:
        """하위 자재까지 누적."""
        boms_by_item = {
            "FG-001": [
                {
                    "_id": "BOM-001",
                    "item_code": "FG-001",
                    "quantity": 1,
                    "is_default": True,
                    "items": [
                        {"item_code": "RAW-1", "qty": 2},
                        {"item_code": "RAW-2", "qty": 3},
                    ],
                }
            ]
        }

        with _service_context(boms_by_item=boms_by_item) as (service, _repos):
            result = service.explode_single_item("FG-001", Decimal(10))
            assert result["FG-001"] == Decimal(10)
            assert result["RAW-1"] == Decimal(20)
            assert result["RAW-2"] == Decimal(30)

    def test_qty_0_422(self) -> None:
        """qty 0이면 422."""
        with _service_context() as (service, _repos):
            with pytest.raises(OneERPError) as exc:
                service.explode_single_item("MAT", Decimal(0))
            assert exc.value.error == "ERR-MFG-NET-002"


# ======================================================================
# 예외 케이스
# ======================================================================


class TestMRP순소요_예외:
    """예외 시나리오."""

    def test_미존재_수요예측_404(self) -> None:
        """수요예측이 없으면 404."""
        with _service_context(forecast=None) as (service, _repos):
            with pytest.raises(OneERPError) as exc:
                service.calculate_net_requirements("DFST-NONE")
            assert exc.value.status_code == 404

    def test_빈_라인_422(self) -> None:
        """수요예측 items가 비어있으면 422."""
        with _service_context(forecast={"_id": "DFST-EMPTY", "items": []}) as (
            service,
            _repos,
        ):
            with pytest.raises(OneERPError) as exc:
                service.calculate_net_requirements("DFST-EMPTY")
            assert exc.value.error == "ERR-MFG-NET-001"
