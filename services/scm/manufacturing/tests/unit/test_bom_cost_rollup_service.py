"""BOM 원가 집계 서비스(BOMCostRollupService) 단위 테스트.

rollup_cost, save_production_cost 메서드의
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
    boms: dict[str, dict] | None = None,
    routings: dict[str, dict] | None = None,
    workstations: dict[str, dict] | None = None,
):
    """mock 컨텍스트 + 서비스 인스턴스를 yield한다."""
    with (
        patch(
            "oneerp_manufacturing_app.services.bom_cost_rollup_service.Repository",
        ) as mock_repo_cls,
    ):
        repos: dict[str, MagicMock] = {}
        bom_lookup = boms or {}
        routing_lookup = routings or {}
        ws_lookup = workstations or {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            if collection_name in repos:
                return repos[collection_name]
            repo = MagicMock()
            repos[collection_name] = repo

            if collection_name == "boms":
                repo.find_by_id.side_effect = lambda bid: bom_lookup.get(bid)
            elif collection_name == "routings":

                def _route_find(query, limit=1, **kwargs):
                    item = query.get("item_code", "")
                    return [routing_lookup[item]] if item in routing_lookup else []

                repo.find_many.side_effect = _route_find
            elif collection_name == "workstations":

                def _ws_find(query, limit=1, **kwargs):
                    wid = query.get("_id", "")
                    return [ws_lookup[wid]] if wid in ws_lookup else []

                repo.find_many.side_effect = _ws_find

            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_manufacturing_app.services.bom_cost_rollup_service import BOMCostRollupService

        service = BOMCostRollupService(tenant_id="test-tenant")
        yield service, repos


# ======================================================================
# 단순 단계 (자재만)
# ======================================================================


class TestBOM원가_단일단계:
    """단일 단계 BOM 자재비 계산."""

    def test_단일_BOM_자재비만(self) -> None:
        """라우팅 없이 자재비만 계산."""
        boms = {
            "BOM-001": {
                "_id": "BOM-001",
                "item_code": "FG-001",
                "quantity": 1,
                "items": [
                    {"item_code": "MAT-A", "qty": 2, "rate": 100},  # 200
                    {"item_code": "MAT-B", "qty": 3, "rate": 50},  # 150
                ],
            }
        }

        with _service_context(boms=boms) as (service, _repos):
            result = service.rollup_cost("BOM-001")

            assert result["material_cost"] == Decimal(350)
            assert result["labour_cost"] == Decimal(0)
            assert result["overhead_cost"] == Decimal(0)
            assert result["total_cost"] == Decimal(350)

    def test_생산수량_배수_적용(self) -> None:
        """qty=2이면 자재비도 2배."""
        boms = {
            "BOM-001": {
                "_id": "BOM-001",
                "item_code": "FG-001",
                "quantity": 1,
                "items": [{"item_code": "MAT-A", "qty": 1, "rate": 100}],
            }
        }

        with _service_context(boms=boms) as (service, _repos):
            result = service.rollup_cost("BOM-001", qty=Decimal(5))
            assert result["material_cost"] == Decimal(500)
            assert result["total_cost"] == Decimal(500)

    def test_BOM_기준수량_나눔(self) -> None:
        """BOM quantity=10인 경우 단가는 10기준이므로 1개 생산 시 1/10."""
        boms = {
            "BOM-001": {
                "_id": "BOM-001",
                "item_code": "FG-001",
                "quantity": 10,  # 10개 기준 자재 100
                "items": [{"item_code": "MAT-A", "qty": 100, "rate": 1}],
            }
        }

        with _service_context(boms=boms) as (service, _repos):
            # 1개 생산 → 자재 10
            result = service.rollup_cost("BOM-001", qty=Decimal(1))
            assert result["material_cost"] == Decimal(10)


# ======================================================================
# 다단계 BOM
# ======================================================================


class TestBOM원가_다단계:
    """하위 BOM 재귀 전개 검증."""

    def test_2단계_BOM_원가_누적(self) -> None:
        """상위 BOM이 하위 BOM을 참조하면 sub-cost가 합산된다."""
        boms = {
            "BOM-PARENT": {
                "_id": "BOM-PARENT",
                "item_code": "FG",
                "quantity": 1,
                "items": [
                    {
                        "item_code": "SUB-A",
                        "qty": 2,
                        "rate": 0,
                        "bom_id": "BOM-SUB-A",
                    },
                    {"item_code": "MAT-DIRECT", "qty": 1, "rate": 50},
                ],
            },
            "BOM-SUB-A": {
                "_id": "BOM-SUB-A",
                "item_code": "SUB-A",
                "quantity": 1,
                "items": [{"item_code": "RAW-1", "qty": 5, "rate": 10}],  # 50
            },
        }

        with _service_context(boms=boms) as (service, _repos):
            result = service.rollup_cost("BOM-PARENT")

            # SUB-A 1개당 50, 2개 = 100
            # MAT-DIRECT 50
            # 총 150
            assert result["material_cost"] == Decimal(150)
            assert result["total_cost"] == Decimal(150)

    def test_breakdown_구조_포함(self) -> None:
        """breakdown에 모든 단계의 원가가 기록된다."""
        boms = {
            "BOM-X": {
                "_id": "BOM-X",
                "item_code": "X",
                "quantity": 1,
                "items": [{"item_code": "MAT", "qty": 1, "rate": 100}],
            }
        }

        with _service_context(boms=boms) as (service, _repos):
            result = service.rollup_cost("BOM-X")
            assert len(result["breakdown"]) >= 1
            top = result["breakdown"][-1]  # 최상위가 마지막
            assert top["item_code"] == "X"
            assert top["material"] == Decimal(100)


class TestBOM원가_라우팅:
    """라우팅 기반 노무비와 경비 계산."""

    def test_라우팅_기반_노무비(self) -> None:
        """공정 시간 x 시간당 단가."""
        boms = {
            "BOM-001": {
                "_id": "BOM-001",
                "item_code": "FG-001",
                "quantity": 1,
                "items": [{"item_code": "M", "qty": 1, "rate": 100}],
            }
        }
        routings = {
            "FG-001": {
                "item_code": "FG-001",
                "operations": [
                    {"workstation": "WS-1", "time_in_mins": 60},  # 1시간
                ],
            }
        }
        workstations = {"WS-1": {"_id": "WS-1", "hourly_rate": 30000, "hourly_overhead": 5000}}

        with _service_context(boms=boms, routings=routings, workstations=workstations) as (
            service,
            _repos,
        ):
            result = service.rollup_cost("BOM-001")

            assert result["material_cost"] == Decimal(100)
            assert result["labour_cost"] == Decimal(30000)
            assert result["overhead_cost"] == Decimal(5000)
            assert result["total_cost"] == Decimal(35100)

    def test_overhead_ratio_적용(self) -> None:
        """overhead_ratio=0.10이면 자재비의 10%가 추가 간접비."""
        boms = {
            "BOM-001": {
                "_id": "BOM-001",
                "item_code": "FG",
                "quantity": 1,
                "items": [{"item_code": "M", "qty": 1, "rate": 1000}],
            }
        }

        with _service_context(boms=boms) as (service, _repos):
            result = service.rollup_cost(
                "BOM-001",
                overhead_ratio=Decimal("0.10"),
            )
            assert result["material_cost"] == Decimal(1000)
            assert result["overhead_cost"] == Decimal(100)
            assert result["total_cost"] == Decimal(1100)


# ======================================================================
# 부산물 차감
# ======================================================================


class TestBOM원가_부산물:
    """include_byproducts=True 시 부산물 가치 차감."""

    def test_부산물_차감(self) -> None:
        """by_products 필드에 명시된 부산물 가치가 총원가에서 차감된다."""
        boms = {
            "BOM-001": {
                "_id": "BOM-001",
                "item_code": "FG",
                "quantity": 1,
                "items": [{"item_code": "M", "qty": 1, "rate": 1000}],
                "by_products": [{"item_code": "BYP", "qty": 1, "rate": 200}],
            }
        }

        with _service_context(boms=boms) as (service, _repos):
            result = service.rollup_cost("BOM-001", include_byproducts=True)
            assert result["byproduct_credit"] == Decimal(200)
            assert result["total_cost"] == Decimal(800)

    def test_부산물_옵션_미적용(self) -> None:
        """include_byproducts=False면 byproduct_credit=0."""
        boms = {
            "BOM-001": {
                "_id": "BOM-001",
                "item_code": "FG",
                "quantity": 1,
                "items": [{"item_code": "M", "qty": 1, "rate": 1000}],
                "by_products": [{"item_code": "BYP", "qty": 1, "rate": 200}],
            }
        }

        with _service_context(boms=boms) as (service, _repos):
            result = service.rollup_cost("BOM-001")
            assert result["byproduct_credit"] == Decimal(0)
            assert result["total_cost"] == Decimal(1000)


# ======================================================================
# 예외 케이스
# ======================================================================


class TestBOM원가_예외:
    """예외 시나리오."""

    def test_미존재_BOM_404(self) -> None:
        """BOM이 없으면 404."""
        with _service_context(boms={}) as (service, _repos):
            with pytest.raises(OneERPError) as exc:
                service.rollup_cost("BOM-NONE")
            assert exc.value.status_code == 404

    def test_qty_0_422(self) -> None:
        """qty가 0이면 422."""
        with _service_context(boms={"BOM-X": {}}) as (service, _repos):
            with pytest.raises(OneERPError) as exc:
                service.rollup_cost("BOM-X", qty=Decimal(0))
            assert exc.value.error == "ERR-MFG-COST-001"

    def test_overhead_ratio_음수_422(self) -> None:
        """overhead_ratio가 음수면 422."""
        with _service_context(boms={"BOM-X": {}}) as (service, _repos):
            with pytest.raises(OneERPError) as exc:
                service.rollup_cost("BOM-X", overhead_ratio=Decimal("-0.1"))
            assert exc.value.error == "ERR-MFG-COST-002"
