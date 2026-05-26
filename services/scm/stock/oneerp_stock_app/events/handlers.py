"""Stock 서비스 이벤트 핸들러 — 구매주문/판매주문/납품/입고/제조 이벤트 처리.

app_factory._build_event_lifespan에서 핸들러를 호출할 때
시그니처는 (data: dict, event_id: str) 형태이다.
data는 EventEnvelope JSON 전체이며, tenant_id는 data["event"]["tenant_id"]에서 추출한다.

L2 비즈니스 룰 매핑:
- BR-STK-010: 입고 금액 자동 계산 (receipt_handler)
- BR-STK-012: 제조 자재 출고 (MATERIAL_ISSUED 이벤트)
- BR-STK-013: 제조 완제품 입고 (WORK_ORDER_COMPLETED 이벤트)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from oneerp_core.events.handler_registry import EventHandlerRegistry
from oneerp_core.events.schemas import EventType
from oneerp_core.events.utils import extract_tenant_and_doc

logger = logging.getLogger(__name__)

event_registry = EventHandlerRegistry()


@event_registry.on(EventType.PURCHASE_ORDER_SUBMITTED, description="구매주문 → 입고 예정 등록")
async def handle_purchase_order_submitted(data: dict[str, Any], event_id: str) -> None:
    """구매주문 제출 시 입고 예정 기록을 생성한다.

    buying 서비스에서 PO 제출 시 발행하는 이벤트를 처리하여,
    해당 품목의 expected_receipts를 갱신한다.
    """
    from oneerp_core.repository import Repository

    tenant_id, doc_id = extract_tenant_and_doc(data)
    event_payload = data.get("event", {}).get("data", {})
    items = event_payload.get("items", [])

    repo = Repository("expected_receipts", tenant_id=tenant_id)
    for item in items:
        repo.insert(
            {
                "purchase_order_id": doc_id,
                "item_code": item.get("item_code", ""),
                "expected_qty": float(item.get("qty", 0)),
                "expected_date": item.get("expected_date", ""),
                "status": "pending",
                "tenant_id": tenant_id,
            }
        )

    logger.info(
        "입고 예정 등록: po_id=%s, items=%d, event_id=%s",
        doc_id,
        len(items),
        event_id,
    )


@event_registry.on(EventType.SALES_ORDER_SUBMITTED, description="판매주문 → 재고 예약")
async def handle_sales_order_submitted(data: dict[str, Any], event_id: str) -> None:
    """판매주문 제출 시 재고를 예약한다."""
    from oneerp_stock_app.services.stock_reservation_service import StockReservationService

    tenant_id, doc_id = extract_tenant_and_doc(data)
    svc = StockReservationService(tenant_id)
    svc.reserve_for_sales_order(doc_id)
    logger.info("재고 예약 완료: doc_id=%s, event_id=%s", doc_id, event_id)


@event_registry.on(EventType.DELIVERY_NOTE_SUBMITTED, description="납품서 → 재고 차감")
async def handle_delivery_note_submitted(data: dict[str, Any], event_id: str) -> None:
    """납품서 제출 시 재고를 차감하고 원장을 기록한다."""
    from oneerp_stock_app.services.stock_ledger_service import StockLedgerService
    from oneerp_stock_app.services.stock_reservation_service import StockReservationService

    tenant_id, doc_id = extract_tenant_and_doc(data)
    ledger_svc = StockLedgerService(tenant_id)
    ledger_svc.process_delivery(doc_id)
    reservation_svc = StockReservationService(tenant_id)
    reservation_svc.release_reservation(doc_id)
    logger.info("재고 차감 + 예약 해제: doc_id=%s, event_id=%s", doc_id, event_id)


@event_registry.on(EventType.PURCHASE_RECEIPT_SUBMITTED, description="입고전표 → 재고 증가")
async def handle_purchase_receipt_submitted(data: dict[str, Any], event_id: str) -> None:
    """입고전표 제출 시 재고를 증가시키고 원장을 기록한다."""
    from oneerp_stock_app.services.stock_ledger_service import StockLedgerService

    tenant_id, doc_id = extract_tenant_and_doc(data)
    svc = StockLedgerService(tenant_id)
    svc.process_receipt(doc_id)
    logger.info("입고 재고 반영: doc_id=%s, event_id=%s", doc_id, event_id)


@event_registry.on(EventType.STOCK_ENTRY_SUBMITTED, description="재고이동 → 재고 원장 반영")
async def handle_stock_entry_submitted(data: dict[str, Any], event_id: str) -> None:
    """재고이동 제출 시 재고 원장과 stock_bins를 갱신한다."""
    from oneerp_stock_app.services.stock_ledger_service import StockLedgerService

    tenant_id, doc_id = extract_tenant_and_doc(data)
    svc = StockLedgerService(tenant_id)
    svc.process_stock_entry(doc_id)
    logger.info("재고이동 재고 반영: doc_id=%s, event_id=%s", doc_id, event_id)


@event_registry.on(EventType.MATERIAL_ISSUED, description="자재출고 → 재고 차감")
async def handle_material_issued(data: dict[str, Any], event_id: str) -> None:
    """자재 출고 이벤트 수신 시 재고를 차감하고 원장을 기록한다.

    manufacturing 서비스에서 작업지시 자재 출고 시 발행하는 이벤트를 처리한다.
    페이로드의 items 목록에 대해 각각 SLE를 생성하여 재고를 차감한다.
    """
    from oneerp_stock_app.services.stock_ledger_service import StockLedgerService

    tenant_id, _doc_id = extract_tenant_and_doc(data)
    event_payload = data.get("event", {}).get("data", {})
    work_order_id = event_payload.get("work_order_id", "")
    items = event_payload.get("items", [])

    svc = StockLedgerService(tenant_id)
    svc.process_material_issue(work_order_id, items)
    logger.info(
        "자재 출고 재고 차감 완료: work_order_id=%s, event_id=%s",
        work_order_id,
        event_id,
    )


@event_registry.on(EventType.WORK_ORDER_COMPLETED, description="작업완료 → 완제품 입고")
async def handle_work_order_completed(data: dict[str, Any], event_id: str) -> None:
    """작업지시 완료 이벤트 수신 시 완제품을 입고하고 원장을 기록한다.

    manufacturing 서비스에서 작업지시 완료 시 발행하는 이벤트를 처리한다.
    생산된 완제품에 대해 SLE를 생성하여 재고를 증가시킨다.
    """
    from oneerp_stock_app.services.stock_ledger_service import StockLedgerService

    tenant_id, _doc_id = extract_tenant_and_doc(data)
    event_payload = data.get("event", {}).get("data", {})
    work_order_id = event_payload.get("work_order_id", "")
    item_code = event_payload.get("item_code", "")
    produced_qty = Decimal(str(event_payload.get("produced_qty", 0)))

    svc = StockLedgerService(tenant_id)
    svc.process_production_receipt(work_order_id, item_code, produced_qty)
    logger.info(
        "완제품 입고 완료: work_order_id=%s, item_code=%s, qty=%s, event_id=%s",
        work_order_id,
        item_code,
        produced_qty,
        event_id,
    )
