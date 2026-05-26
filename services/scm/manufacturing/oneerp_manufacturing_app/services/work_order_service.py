"""작업지시 서비스 — BOM 기반 자재 출고/생산실적/완료 처리.

재고 변동은 stock_balances를 직접 수정하지 않고,
도메인 이벤트를 발행하여 stock 서비스가 SLE를 통해 처리하도록 한다.

L2 비즈니스 룰 매핑:
- BR-MFG-006: 작업지시 BOM 필수 (bom_ref 필수)
- BR-MFG-007: 자재 출고 재고 확인 (stock_balances 검증)
- BR-MFG-008: 완료 조건 (produced_qty > 0)
- BR-MFG-009: 수정 조건 (DRAFT만)
- BR-MFG-010: 취소 조건 (SUBMITTED만)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class WorkOrderService:
    """작업지시(Work Order) 비즈니스 로직.

    BOM 조회 → 작업지시 생성 → 자재 출고 → 생산실적 → 완료(입고).
    재고 쓰기는 이벤트 발행으로 위임하며, 읽기는 stock_balances 참조.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._wo_repo = Repository("work_orders", tenant_id=tenant_id)
        self._bom_repo = Repository("boms", tenant_id=tenant_id)
        self._stock_repo = Repository("stock_balances", tenant_id=tenant_id)
        self._by_product_repo = Repository("by_products", tenant_id=tenant_id)

    def create_work_order(
        self,
        bom_id: str,
        qty: float,
        planned_start: str,
    ) -> dict[str, Any]:
        """BOM 조회 후 작업지시를 생성한다.

        Args:
            bom_id: BOM 문서 ID
            qty: 생산 수량
            planned_start: 계획 시작일 (ISO 문자열)

        Returns:
            생성된 작업지시 문서
        """
        bom = self._bom_repo.find_by_id(bom_id)
        if not bom:
            raise OneERPError(
                status_code=404,
                error="ERR-MFG-001",
                detail=f"BOM '{bom_id}'을 찾을 수 없습니다",
            )

        # BOM 자재 목록에서 필요 수량 계산
        bom_items = bom.get("items", [])
        required_materials = [
            {
                "item_code": item.get("item_code", ""),
                "required_qty": float(item.get("qty", 0)) * qty,
                "uom": item.get("uom", ""),
            }
            for item in bom_items
        ]

        wo_id = generate_name("WO", tenant_id=self._tenant_id)
        wo_doc = {
            "_id": wo_id,
            "bom_id": bom_id,
            "item_code": bom.get("item_code", ""),
            "planned_qty": qty,
            "produced_qty": 0,
            "process_loss_qty": 0,
            "planned_start": planned_start,
            "status": "draft",
            "required_materials": required_materials,
            "tenant_id": self._tenant_id,
        }
        self._wo_repo.insert(wo_doc)

        logger.info("작업지시 생성: %s (BOM: %s, 수량: %s)", wo_id, bom_id, qty)
        return wo_doc

    def _get_work_order(self, work_order_id: str) -> dict[str, Any]:
        """작업지시를 조회한다. 미존재 시 에러."""
        wo = self._wo_repo.find_by_id(work_order_id)
        if not wo:
            raise OneERPError(
                status_code=404,
                error="ERR-MFG-003",
                detail=f"작업지시 '{work_order_id}'을 찾을 수 없습니다",
            )
        return wo

    def _check_draft_status(self, wo: dict[str, Any]) -> None:
        """BR-MFG-009: Draft 상태에서만 수정 가능."""
        if wo.get("status", "draft") != "draft":
            raise OneERPError(
                status_code=400,
                error="ERR-MFG-009",
                detail="초안(draft) 상태에서만 수정할 수 있습니다",
            )

    def issue_materials(self, work_order_id: str) -> dict[str, Any]:
        """BR-MFG-007: 자재 출고 — 재고 확인 후 MATERIAL_ISSUED 이벤트 발행.

        재고 잔고를 읽기 전용으로 확인한 뒤, 실제 차감은
        MATERIAL_ISSUED 이벤트를 발행하여 stock 서비스가 SLE를 통해 처리한다.

        Args:
            work_order_id: 작업지시 ID

        Returns:
            자재 출고 결과

        Raises:
            OneERPError: 작업지시 미존재 또는 재고 부족
        """
        wo = self._get_work_order(work_order_id)

        issued_items: list[dict[str, Any]] = []
        for material in wo.get("required_materials", []):
            item_code = material.get("item_code", "")
            required_qty = float(material.get("required_qty", 0))

            # 현재 재고 읽기 전용 확인 (stock_balances 참조)
            stocks = self._stock_repo.find_many({"item_code": item_code}, limit=1)
            current_qty = float(stocks[0].get("qty", 0)) if stocks else 0

            if current_qty < required_qty:
                raise OneERPError(
                    status_code=422,
                    error="ERR-MFG-004",
                    detail=f"자재 '{item_code}' 재고 부족: 필요 {required_qty}, 현재 {current_qty}",
                )

            issued_items.append(
                {
                    "item_code": item_code,
                    "issued_qty": required_qty,
                }
            )

        # 작업지시 상태 변경 + 자재 출고 이벤트 발행 (stock 서비스가 SLE 생성)
        self._wo_repo.update_with_event(
            work_order_id,
            {"status": "in_progress"},
            event_type=EventType.MATERIAL_ISSUED,
            event_data={
                "work_order_id": work_order_id,
                "items": issued_items,
                "tenant_id": self._tenant_id,
            },
        )

        logger.info("자재 출고 이벤트 발행: %s (%d건)", work_order_id, len(issued_items))
        return {"work_order_id": work_order_id, "issued_items": issued_items}

    def report_production(
        self,
        work_order_id: str,
        produced_qty: float,
        by_products: list[dict[str, Any]] | None = None,
        process_loss_qty: float = 0,
    ) -> dict[str, Any]:
        """생산실적을 보고한다.

        Args:
            work_order_id: 작업지시 ID
            produced_qty: 생산 수량
            by_products: 부산물 목록 [{item_code, qty}]
            process_loss_qty: 공정 손실 수량

        Returns:
            갱신된 생산실적 요약
        """
        wo = self._get_work_order(work_order_id)

        current_produced = float(wo.get("produced_qty", 0))
        current_loss = float(wo.get("process_loss_qty", 0))
        new_produced = current_produced + produced_qty
        new_loss = current_loss + process_loss_qty

        self._wo_repo.update_by_id(
            work_order_id,
            {
                "produced_qty": new_produced,
                "process_loss_qty": new_loss,
            },
        )

        # 부산물 기록
        if by_products:
            for bp in by_products:
                bp_id = generate_name("BYPD", tenant_id=self._tenant_id)
                self._by_product_repo.insert(
                    {
                        "_id": bp_id,
                        "work_order_id": work_order_id,
                        "item_code": bp.get("item_code", ""),
                        "qty": float(bp.get("qty", 0)),
                        "tenant_id": self._tenant_id,
                    }
                )

        logger.info(
            "생산실적 보고: %s (생산: %s, 손실: %s)",
            work_order_id,
            new_produced,
            new_loss,
        )
        return {
            "work_order_id": work_order_id,
            "produced_qty": new_produced,
            "process_loss_qty": new_loss,
            "by_product_count": len(by_products) if by_products else 0,
        }

    def create_from_production_plan(self, production_plan_id: str) -> list[str]:
        """생산계획에서 작업지시를 일괄 생성한다.

        생산계획의 items 각 항목에 대해 create_work_order()를 호출하고
        생성된 WO ID 목록을 반환한다.

        Args:
            production_plan_id: 생산계획 문서 ID

        Returns:
            생성된 작업지시 ID 목록

        Raises:
            OneERPError: 생산계획이 존재하지 않을 때
        """
        plan_repo = Repository("production_plans", tenant_id=self._tenant_id)
        plan = plan_repo.find_by_id(production_plan_id)
        if not plan:
            raise OneERPError(
                status_code=404,
                error="ERR-MFG-006",
                detail=f"생산계획 '{production_plan_id}'를 찾을 수 없습니다",
            )

        items: list[dict[str, Any]] = plan.get("items", [])
        planned_start: str = plan.get("planned_start", "")
        wo_ids: list[str] = []

        for item in items:
            bom_id = item.get("bom_id", "")
            qty = float(item.get("qty", 0))
            if not bom_id or qty <= 0:
                logger.warning("유효하지 않은 생산계획 항목 건너뜀: %s", item)
                continue

            wo = self.create_work_order(bom_id, qty, planned_start)
            wo_ids.append(wo["_id"])

        logger.info(
            "생산계획 기반 작업지시 %d건 생성: %s",
            len(wo_ids),
            production_plan_id,
        )
        return wo_ids

    def complete_work_order(self, work_order_id: str) -> dict[str, Any]:
        """작업지시를 완료하고 완제품 입고 이벤트를 발행한다.

        stock_balances를 직접 수정하지 않고 WORK_ORDER_COMPLETED 이벤트를
        발행하여 stock 서비스가 SLE를 통해 완제품 입고를 처리한다.

        Args:
            work_order_id: 작업지시 ID

        Returns:
            완료된 작업지시 요약

        Raises:
            OneERPError: 생산 수량이 0이면 완료 불가
        """
        wo = self._get_work_order(work_order_id)

        # BR-MFG-010: submitted 상태에서만 취소/완료 가능
        status = wo.get("status", "draft")
        if status not in ("in_progress", "submitted"):
            raise OneERPError(
                status_code=400,
                error="ERR-MFG-010",
                detail=f"진행 중(in_progress) 상태에서만 완료할 수 있습니다 (현재: {status})",
            )

        produced_qty = float(wo.get("produced_qty", 0))
        if produced_qty <= 0:
            raise OneERPError(
                status_code=422,
                error="ERR-MFG-005",
                detail="생산 수량이 0인 작업지시는 완료할 수 없습니다",
            )

        item_code = wo.get("item_code", "")

        # 작업지시 완료 + 완제품 입고 이벤트 발행 (stock 서비스가 SLE 생성)
        self._wo_repo.update_with_event(
            work_order_id,
            {"status": "completed"},
            event_type=EventType.WORK_ORDER_COMPLETED,
            event_data={
                "work_order_id": work_order_id,
                "item_code": item_code,
                "produced_qty": produced_qty,
                "tenant_id": self._tenant_id,
            },
        )

        logger.info(
            "작업지시 완료 이벤트 발행: %s (품목: %s, 수량: %s)",
            work_order_id,
            item_code,
            produced_qty,
        )
        return {
            "work_order_id": work_order_id,
            "item_code": item_code,
            "produced_qty": produced_qty,
            "status": "completed",
        }
