"""재고 관리 서비스(InventoryControlService) 단위 테스트.

BR-STK-016(안전재고), BR-STK-017(리오더), BR-STK-018(순환재고조사)
각 메서드의 정상·예외·경계값 시나리오를 검증한다.
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
    safety_rules: list[dict] | None = None,
    reorder_rules: list[dict] | None = None,
    cycle_count_doc: dict | None = None,
    bin_docs: list[dict] | None = None,
):
    """mock을 유지하며 서비스 인스턴스와 리포지토리를 제공한다."""
    with patch(
        "oneerp_stock_app.services.inventory_control_service.Repository",
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            if collection_name in repos:
                return repos[collection_name]
            repo = MagicMock()
            repos[collection_name] = repo

            if collection_name == "safety_stock_rules":
                repo.find_many.return_value = safety_rules if safety_rules is not None else []
            elif collection_name == "reorder_levels":
                repo.find_many.return_value = reorder_rules if reorder_rules is not None else []
            elif collection_name == "cycle_counts":
                repo.find_by_id.return_value = cycle_count_doc
            elif collection_name == "stock_bins":
                repo.find_many.return_value = bin_docs if bin_docs is not None else []

            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_stock_app.services.inventory_control_service import InventoryControlService

        service = InventoryControlService(tenant_id="test-tenant")
        yield service, repos


# ======================================================================
# BR-STK-016: 안전재고 알림
# ======================================================================


class Test안전재고_정상:
    """BR-STK-016: 안전재고 미달 품목 감지."""

    def test_미달_품목_감지(self) -> None:
        """현재 수량이 안전재고 미만이면 알림 목록에 포함된다."""
        safety_rules = [
            {
                "item_code": "ITEM-A",
                "warehouse_id": "WH-01",
                "minimum_qty": 100,
            },
        ]
        bin_docs = [{"current_qty": 50}]

        with _service_context(safety_rules=safety_rules, bin_docs=bin_docs) as (
            service,
            _repos,
        ):
            alerts = service.check_safety_stock_alerts()

            assert len(alerts) == 1
            assert alerts[0]["item_code"] == "ITEM-A"
            assert alerts[0]["current_qty"] == Decimal(50)
            assert alerts[0]["minimum_qty"] == Decimal(100)
            assert alerts[0]["shortfall"] == Decimal(50)

    def test_충분한_재고는_알림_제외(self) -> None:
        """현재 수량이 안전재고 이상이면 알림 대상이 아니다."""
        safety_rules = [
            {
                "item_code": "ITEM-A",
                "warehouse_id": "WH-01",
                "minimum_qty": 50,
            },
        ]
        bin_docs = [{"current_qty": 100}]

        with _service_context(safety_rules=safety_rules, bin_docs=bin_docs) as (
            service,
            _repos,
        ):
            alerts = service.check_safety_stock_alerts()
            assert len(alerts) == 0

    def test_다중_품목_필터링(self) -> None:
        """여러 규칙 중 미달 품목만 반환된다."""
        safety_rules = [
            {"item_code": "ITEM-A", "warehouse_id": "WH-01", "minimum_qty": 100},
            {"item_code": "ITEM-B", "warehouse_id": "WH-01", "minimum_qty": 30},
        ]

        with patch(
            "oneerp_stock_app.services.inventory_control_service.Repository",
        ) as mock_repo_cls:
            repos: dict[str, MagicMock] = {}
            call_count = {"bin": 0}

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                if collection_name in repos:
                    return repos[collection_name]
                repo = MagicMock()
                repos[collection_name] = repo

                if collection_name == "safety_stock_rules":
                    repo.find_many.return_value = safety_rules
                elif collection_name == "stock_bins":
                    # 첫 번째 호출: ITEM-A = 50 (미달), 두 번째 호출: ITEM-B = 50 (충분)
                    def _bin_find(*args, **kwargs):
                        call_count["bin"] += 1
                        if call_count["bin"] == 1:
                            return [{"current_qty": 50}]
                        return [{"current_qty": 50}]

                    repo.find_many.side_effect = _bin_find

                return repo

            mock_repo_cls.side_effect = _repo_factory
            from oneerp_stock_app.services.inventory_control_service import InventoryControlService

            service = InventoryControlService(tenant_id="test-tenant")
            alerts = service.check_safety_stock_alerts()

            # ITEM-A는 50 < 100이므로 미달, ITEM-B는 50 > 30이므로 충분
            assert len(alerts) == 1
            assert alerts[0]["item_code"] == "ITEM-A"


class Test안전재고_경계값:
    """BR-STK-016: 경계값 시나리오."""

    def test_규칙_없으면_빈_목록(self) -> None:
        """안전재고 규칙이 없으면 빈 목록을 반환한다."""
        with _service_context(safety_rules=[]) as (service, _repos):
            alerts = service.check_safety_stock_alerts()
            assert alerts == []

    def test_현재_수량_동일하면_알림_제외(self) -> None:
        """current_qty == minimum_qty이면 미달이 아니므로 알림 대상이 아니다."""
        safety_rules = [
            {"item_code": "ITEM-A", "warehouse_id": "WH-01", "minimum_qty": 100},
        ]
        bin_docs = [{"current_qty": 100}]

        with _service_context(safety_rules=safety_rules, bin_docs=bin_docs) as (
            service,
            _repos,
        ):
            alerts = service.check_safety_stock_alerts()
            assert len(alerts) == 0

    def test_재고_없는_품목_미달_감지(self) -> None:
        """stock_bins에 기록이 없는 품목(수량 0)은 미달로 감지된다."""
        safety_rules = [
            {"item_code": "ITEM-NEW", "warehouse_id": "WH-01", "minimum_qty": 10},
        ]

        with _service_context(safety_rules=safety_rules, bin_docs=[]) as (
            service,
            _repos,
        ):
            alerts = service.check_safety_stock_alerts()
            assert len(alerts) == 1
            assert alerts[0]["current_qty"] == Decimal(0)
            assert alerts[0]["shortfall"] == Decimal(10)

    def test_minimum_qty_0이면_알림_없음(self) -> None:
        """안전재고가 0이면 어떤 수량이든 미달이 아니다."""
        safety_rules = [
            {"item_code": "ITEM-A", "warehouse_id": "WH-01", "minimum_qty": 0},
        ]

        with _service_context(safety_rules=safety_rules, bin_docs=[]) as (
            service,
            _repos,
        ):
            alerts = service.check_safety_stock_alerts()
            assert len(alerts) == 0


# ======================================================================
# BR-STK-017: 리오더 포인트
# ======================================================================


class Test리오더_정상:
    """BR-STK-017: 리오더 포인트 도달 품목 감지."""

    def test_리오더_포인트_도달(self) -> None:
        """현재 수량이 reorder_level 이하이면 재발주 대상이다."""
        reorder_rules = [
            {
                "item_code": "ITEM-A",
                "warehouse": "WH-01",
                "reorder_level": 100,
                "reorder_qty": 200,
            },
        ]
        bin_docs = [{"current_qty": 80}]

        with _service_context(reorder_rules=reorder_rules, bin_docs=bin_docs) as (
            service,
            _repos,
        ):
            items = service.check_reorder_points()

            assert len(items) == 1
            assert items[0]["item_code"] == "ITEM-A"
            assert items[0]["current_qty"] == Decimal(80)
            assert items[0]["reorder_level"] == Decimal(100)
            assert items[0]["reorder_qty"] == Decimal(200)

    def test_리오더_정확히_동일_수량(self) -> None:
        """current_qty == reorder_level이면 재발주 대상이다 (<=)."""
        reorder_rules = [
            {
                "item_code": "ITEM-A",
                "warehouse": "WH-01",
                "reorder_level": 100,
                "reorder_qty": 50,
            },
        ]
        bin_docs = [{"current_qty": 100}]

        with _service_context(reorder_rules=reorder_rules, bin_docs=bin_docs) as (
            service,
            _repos,
        ):
            items = service.check_reorder_points()
            assert len(items) == 1

    def test_충분한_재고는_재발주_제외(self) -> None:
        """현재 수량이 reorder_level 초과이면 재발주 대상이 아니다."""
        reorder_rules = [
            {
                "item_code": "ITEM-A",
                "warehouse": "WH-01",
                "reorder_level": 50,
                "reorder_qty": 100,
            },
        ]
        bin_docs = [{"current_qty": 80}]

        with _service_context(reorder_rules=reorder_rules, bin_docs=bin_docs) as (
            service,
            _repos,
        ):
            items = service.check_reorder_points()
            assert len(items) == 0


class Test리오더_경계값:
    """BR-STK-017: 경계값 시나리오."""

    def test_규칙_없으면_빈_목록(self) -> None:
        """리오더 규칙이 없으면 빈 목록을 반환한다."""
        with _service_context(reorder_rules=[]) as (service, _repos):
            items = service.check_reorder_points()
            assert items == []

    def test_재고_없는_품목_재발주_대상(self) -> None:
        """stock_bins에 기록이 없는 품목(수량 0)은 재발주 대상이다."""
        reorder_rules = [
            {
                "item_code": "ITEM-NEW",
                "warehouse": "WH-01",
                "reorder_level": 10,
                "reorder_qty": 50,
            },
        ]

        with _service_context(reorder_rules=reorder_rules, bin_docs=[]) as (
            service,
            _repos,
        ):
            items = service.check_reorder_points()
            assert len(items) == 1
            assert items[0]["current_qty"] == Decimal(0)

    def test_reorder_level_0이면_재고0만_대상(self) -> None:
        """reorder_level이 0이면 재고 0인 경우만 재발주 대상이다."""
        reorder_rules = [
            {
                "item_code": "ITEM-A",
                "warehouse": "WH-01",
                "reorder_level": 0,
                "reorder_qty": 100,
            },
        ]
        # 현재 수량 0 → 0 <= 0이므로 대상
        with _service_context(reorder_rules=reorder_rules, bin_docs=[]) as (
            service,
            _repos,
        ):
            items = service.check_reorder_points()
            assert len(items) == 1

        # 현재 수량 1 → 1 > 0이므로 대상 아님
        bin_docs = [{"current_qty": 1}]
        with _service_context(reorder_rules=reorder_rules, bin_docs=bin_docs) as (
            service,
            _repos,
        ):
            items = service.check_reorder_points()
            assert len(items) == 0


# ======================================================================
# BR-STK-018: 순환재고조사
# ======================================================================


class Test순환재고조사_정상:
    """BR-STK-018: 순환재고조사 차이 계산."""

    def test_양수_차이_계산(self) -> None:
        """실사 수량 > 시스템 수량이면 양수 variance를 반환한다."""
        cc_doc = {
            "_id": "CC-001",
            "status": "in_progress",
            "item_code": "ITEM-A",
            "warehouse_id": "WH-01",
            "actual_qty": 120,
        }
        bin_docs = [{"current_qty": 100}]

        with _service_context(cycle_count_doc=cc_doc, bin_docs=bin_docs) as (
            service,
            repos,
        ):
            result = service.execute_cycle_count("CC-001")

            assert result["cycle_count_id"] == "CC-001"
            assert len(result["items"]) == 1
            assert result["items"][0]["system_qty"] == Decimal(100)
            assert result["items"][0]["counted_qty"] == Decimal(120)
            assert result["items"][0]["variance"] == Decimal(20)
            assert result["total_variance"] == Decimal(20)

            # 문서 업데이트 검증
            cycle_repo = repos["cycle_counts"]
            cycle_repo.update_by_id.assert_called_once_with(
                "CC-001",
                {
                    "system_qty": Decimal(100),
                    "variance": Decimal(20),
                    "status": "completed",
                },
            )

    def test_음수_차이_계산(self) -> None:
        """실사 수량 < 시스템 수량이면 음수 variance를 반환한다."""
        cc_doc = {
            "_id": "CC-002",
            "status": "draft",
            "item_code": "ITEM-A",
            "warehouse_id": "WH-01",
            "actual_qty": 80,
        }
        bin_docs = [{"current_qty": 100}]

        with _service_context(cycle_count_doc=cc_doc, bin_docs=bin_docs) as (
            service,
            _repos,
        ):
            result = service.execute_cycle_count("CC-002")

            assert result["items"][0]["variance"] == Decimal(-20)
            assert result["total_variance"] == Decimal(-20)

    def test_차이_없음(self) -> None:
        """실사 수량 == 시스템 수량이면 variance 0을 반환한다."""
        cc_doc = {
            "_id": "CC-003",
            "status": "in_progress",
            "item_code": "ITEM-A",
            "warehouse_id": "WH-01",
            "actual_qty": 100,
        }
        bin_docs = [{"current_qty": 100}]

        with _service_context(cycle_count_doc=cc_doc, bin_docs=bin_docs) as (
            service,
            _repos,
        ):
            result = service.execute_cycle_count("CC-003")

            assert result["items"][0]["variance"] == Decimal(0)
            assert result["total_variance"] == Decimal(0)


class Test순환재고조사_예외:
    """BR-STK-018: 예외 시나리오."""

    def test_미존재_문서_404(self) -> None:
        """존재하지 않는 순환재고조사 문서는 404를 발생시킨다."""
        with _service_context(cycle_count_doc=None) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.execute_cycle_count("CC-NONE")
            assert exc_info.value.status_code == 404

    def test_완료된_조사_재실행_422(self) -> None:
        """이미 완료된 순환재고조사를 재실행하면 422를 발생시킨다."""
        cc_doc = {
            "_id": "CC-DONE",
            "status": "completed",
            "item_code": "ITEM-A",
            "warehouse_id": "WH-01",
            "actual_qty": 100,
        }

        with _service_context(cycle_count_doc=cc_doc) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.execute_cycle_count("CC-DONE")
            assert exc_info.value.status_code == 422
            assert exc_info.value.error == "ERR-STK-003"


class Test순환재고조사_경계값:
    """BR-STK-018: 경계값 시나리오."""

    def test_시스템_재고_없는_품목(self) -> None:
        """stock_bins에 기록 없는 품목은 system_qty=0으로 계산한다."""
        cc_doc = {
            "_id": "CC-004",
            "status": "draft",
            "item_code": "ITEM-NEW",
            "warehouse_id": "WH-01",
            "actual_qty": 50,
        }

        with _service_context(cycle_count_doc=cc_doc, bin_docs=[]) as (
            service,
            _repos,
        ):
            result = service.execute_cycle_count("CC-004")

            assert result["items"][0]["system_qty"] == Decimal(0)
            assert result["items"][0]["counted_qty"] == Decimal(50)
            assert result["items"][0]["variance"] == Decimal(50)

    def test_실사_수량_0(self) -> None:
        """실사 수량이 0이면 시스템 수량만큼 음수 차이가 발생한다."""
        cc_doc = {
            "_id": "CC-005",
            "status": "in_progress",
            "item_code": "ITEM-A",
            "warehouse_id": "WH-01",
            "actual_qty": 0,
        }
        bin_docs = [{"current_qty": 100}]

        with _service_context(cycle_count_doc=cc_doc, bin_docs=bin_docs) as (
            service,
            _repos,
        ):
            result = service.execute_cycle_count("CC-005")

            assert result["items"][0]["variance"] == Decimal(-100)
            assert result["total_variance"] == Decimal(-100)

    def test_draft_상태에서_실행_가능(self) -> None:
        """draft 상태의 순환재고조사는 실행 가능하다."""
        cc_doc = {
            "_id": "CC-006",
            "status": "draft",
            "item_code": "ITEM-A",
            "warehouse_id": "WH-01",
            "actual_qty": 100,
        }
        bin_docs = [{"current_qty": 100}]

        with _service_context(cycle_count_doc=cc_doc, bin_docs=bin_docs) as (
            service,
            repos,
        ):
            result = service.execute_cycle_count("CC-006")

            assert result["cycle_count_id"] == "CC-006"
            # 상태가 completed로 업데이트됨
            cycle_repo = repos["cycle_counts"]
            update_call = cycle_repo.update_by_id.call_args[0]
            assert update_call[1]["status"] == "completed"
