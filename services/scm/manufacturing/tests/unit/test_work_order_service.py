"""작업지시 서비스(WorkOrderService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_manufacturing_app.services.work_order_service.generate_name",
        side_effect=lambda prefix, **kw: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_manufacturing_app.services.work_order_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_manufacturing_app.services.work_order_service import WorkOrderService

        service = WorkOrderService(tenant_id="test-tenant")
    return (
        service,
        repos["work_orders"],
        repos["boms"],
        repos["stock_balances"],
        repos["by_products"],
    )


class Test작업지시생성:
    def test_BOM_기반_작업지시_생성(self) -> None:
        """BOM 조회 후 작업지시와 필요 자재를 생성한다."""
        service, _wo_repo, bom_repo, _stock, _bp = _make_service()
        bom_repo.find_by_id.return_value = {
            "_id": "BOM-001",
            "item_code": "PROD-A",
            "items": [
                {"item_code": "MAT-1", "qty": 2, "uom": "EA"},
                {"item_code": "MAT-2", "qty": 1, "uom": "KG"},
            ],
        }

        result = service.create_work_order("BOM-001", 10, "2026-03-01")

        assert result["bom_id"] == "BOM-001"
        assert result["planned_qty"] == 10
        assert len(result["required_materials"]) == 2
        assert result["required_materials"][0]["required_qty"] == 20  # 2 * 10

    def test_BOM_미존재_에러(self) -> None:
        """존재하지 않는 BOM이면 OneERPError(ERR-MFG-001)."""
        service, _wo, bom_repo, _stock, _bp = _make_service()
        bom_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="ERR-MFG-001"):
            service.create_work_order("BOM-999", 5, "2026-03-01")


class Test자재출고:
    def test_재고_충분하면_이벤트_발행(self) -> None:
        """재고가 충분하면 stock_balances 직접 수정 없이 MATERIAL_ISSUED 이벤트를 발행한다."""
        service, wo_repo, _bom, stock_repo, _bp = _make_service()
        wo_repo.find_by_id.return_value = {
            "_id": "WO-001",
            "required_materials": [
                {"item_code": "MAT-1", "required_qty": 20},
            ],
        }
        stock_repo.find_many.return_value = [{"_id": "STK-1", "qty": 100}]

        result = service.issue_materials("WO-001")

        assert len(result["issued_items"]) == 1
        # stock_balances 직접 수정이 없어야 한다
        stock_repo.update_by_id.assert_not_called()
        # 이벤트 발행 확인 (update_with_event 호출)
        wo_repo.update_with_event.assert_called_once()
        call_kwargs = wo_repo.update_with_event.call_args
        assert call_kwargs[0][0] == "WO-001"
        assert call_kwargs[0][1] == {"status": "in_progress"}
        assert call_kwargs[1]["event_data"]["items"] == [
            {"item_code": "MAT-1", "issued_qty": 20},
        ]

    def test_재고_부족하면_에러(self) -> None:
        """재고 부족 시 OneERPError(ERR-MFG-004)."""
        service, wo_repo, _bom, stock_repo, _bp = _make_service()
        wo_repo.find_by_id.return_value = {
            "_id": "WO-001",
            "required_materials": [
                {"item_code": "MAT-1", "required_qty": 200},
            ],
        }
        stock_repo.find_many.return_value = [{"_id": "STK-1", "qty": 10}]

        with pytest.raises(OneERPError, match="ERR-MFG-004"):
            service.issue_materials("WO-001")


class Test생산실적:
    def test_생산실적_보고(self) -> None:
        """생산 수량과 손실을 누적 기록한다."""
        service, wo_repo, _bom, _stock, _bp = _make_service()
        wo_repo.find_by_id.return_value = {
            "_id": "WO-001",
            "produced_qty": 10,
            "process_loss_qty": 1,
        }

        result = service.report_production("WO-001", 5, process_loss_qty=2)

        assert result["produced_qty"] == 15  # 10 + 5
        assert result["process_loss_qty"] == 3  # 1 + 2

    def test_부산물_기록(self) -> None:
        """부산물이 있으면 by_products 컬렉션에 저장한다."""
        service, wo_repo, _bom, _stock, bp_repo = _make_service()
        wo_repo.find_by_id.return_value = {
            "_id": "WO-001",
            "produced_qty": 0,
            "process_loss_qty": 0,
        }

        result = service.report_production(
            "WO-001",
            10,
            by_products=[{"item_code": "SCRAP-1", "qty": 2}],
        )

        assert result["by_product_count"] == 1
        bp_repo.insert.assert_called_once()


class Test작업지시완료:
    def test_정상_완료_이벤트_발행(self) -> None:
        """생산 수량이 있으면 WORK_ORDER_COMPLETED 이벤트를 발행한다."""
        service, wo_repo, _bom, stock_repo, _bp = _make_service()
        wo_repo.find_by_id.return_value = {
            "_id": "WO-001",
            "item_code": "PROD-A",
            "produced_qty": 50,
            "status": "in_progress",
        }

        result = service.complete_work_order("WO-001")

        assert result["status"] == "completed"
        assert result["produced_qty"] == 50
        # stock_balances 직접 수정이 없어야 한다
        stock_repo.update_by_id.assert_not_called()
        stock_repo.insert.assert_not_called()
        # 이벤트 발행 확인 (update_with_event 호출)
        wo_repo.update_with_event.assert_called_once()
        call_kwargs = wo_repo.update_with_event.call_args
        assert call_kwargs[0][0] == "WO-001"
        assert call_kwargs[0][1] == {"status": "completed"}
        assert call_kwargs[1]["event_data"]["item_code"] == "PROD-A"
        assert call_kwargs[1]["event_data"]["produced_qty"] == 50

    def test_생산수량_0이면_에러(self) -> None:
        """생산 수량 0이면 OneERPError(ERR-MFG-005)."""
        service, wo_repo, _bom, _stock, _bp = _make_service()
        wo_repo.find_by_id.return_value = {
            "_id": "WO-001",
            "item_code": "PROD-A",
            "produced_qty": 0,
            "status": "in_progress",
        }

        with pytest.raises(OneERPError, match="ERR-MFG-005"):
            service.complete_work_order("WO-001")

    def test_draft_상태에서_완료_불가(self) -> None:
        """BR-MFG-010: draft 상태에서는 완료할 수 없다."""
        service, wo_repo, _bom, _stock, _bp = _make_service()
        wo_repo.find_by_id.return_value = {
            "_id": "WO-002",
            "item_code": "PROD-A",
            "produced_qty": 10,
            "status": "draft",
        }

        with pytest.raises(OneERPError, match="ERR-MFG-010"):
            service.complete_work_order("WO-002")


def _make_service_with_plans() -> tuple:
    """create_from_production_plan 테스트용 서비스·리포 mock을 반환한다.

    create_from_production_plan은 메서드 내부에서 Repository를 생성하므로
    patch 스코프를 호출 시점까지 유지하는 헬퍼가 필요하다.
    반환된 mock_repo_cls.side_effect를 통해 repos dict에 자동 등록된다.
    """
    # 미리 production_plans 키를 등록하여 테스트에서 설정 가능하게 한다
    repos: dict[str, MagicMock] = {
        "production_plans": MagicMock(),
    }
    mock_repo_cls = patch("oneerp_manufacturing_app.services.work_order_service.Repository")
    patched = mock_repo_cls.start()

    def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
        if collection_name not in repos:
            repos[collection_name] = MagicMock()
        return repos[collection_name]

    patched.side_effect = _repo_factory

    from oneerp_manufacturing_app.services.work_order_service import WorkOrderService

    service = WorkOrderService(tenant_id="test-tenant")
    return service, repos, mock_repo_cls


class Test생산계획에서작업지시생성:
    """create_from_production_plan 메서드 테스트."""

    def test_생산계획에서_작업지시_일괄생성(self) -> None:
        """production_plan의 items 각각에 대해 WorkOrder가 생성된다."""
        service, repos, patcher = _make_service_with_plans()
        try:
            # 생산계획 조회 결과
            repos["production_plans"].find_by_id.return_value = {
                "_id": "PP-0001",
                "status": "draft",
                "planned_start": "2026-04-01",
                "items": [
                    {"bom_id": "BOM-001", "qty": 100},
                    {"bom_id": "BOM-002", "qty": 50},
                ],
            }

            # BOM 조회 결과 (create_work_order 내부에서 호출)
            bom_doc = {
                "_id": "BOM-001",
                "item_code": "PROD-A",
                "items": [{"item_code": "MAT-001", "qty": 2, "uom": "EA"}],
            }
            repos["boms"].find_by_id.return_value = bom_doc

            wo_ids = service.create_from_production_plan("PP-0001")

            assert len(wo_ids) == 2
            assert all(wid.startswith("WO-") for wid in wo_ids)
        finally:
            patcher.stop()

    def test_생산계획_미존재시_에러(self) -> None:
        """존재하지 않는 생산계획이면 OneERPError(ERR-MFG-006)."""
        service, repos, patcher = _make_service_with_plans()
        try:
            repos["production_plans"].find_by_id.return_value = None

            with pytest.raises(OneERPError, match="ERR-MFG-006"):
                service.create_from_production_plan("PP-9999")
        finally:
            patcher.stop()

    def test_유효하지_않은_항목_건너뜀(self) -> None:
        """bom_id가 비어있거나 qty가 0인 항목은 건너뛴다."""
        service, repos, patcher = _make_service_with_plans()
        try:
            repos["production_plans"].find_by_id.return_value = {
                "_id": "PP-0002",
                "planned_start": "2026-04-01",
                "items": [
                    {"bom_id": "", "qty": 100},  # bom_id 비어있음
                    {"bom_id": "BOM-001", "qty": 0},  # qty 0
                    {"bom_id": "BOM-002", "qty": 50},  # 유효
                ],
            }

            bom_doc = {
                "_id": "BOM-002",
                "item_code": "PROD-B",
                "items": [{"item_code": "MAT-002", "qty": 1, "uom": "KG"}],
            }
            repos["boms"].find_by_id.return_value = bom_doc

            wo_ids = service.create_from_production_plan("PP-0002")

            # 유효한 항목 1건만 생성
            assert len(wo_ids) == 1
        finally:
            patcher.stop()
