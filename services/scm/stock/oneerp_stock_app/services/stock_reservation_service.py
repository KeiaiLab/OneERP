"""재고 예약 서비스 — 판매주문 기반 재고 선점.

판매주문 확정 시 재고를 예약하고, 납품 시 예약을 해제한다.

L2 비즈니스 룰 매핑:
- BR-STK-005: 재고 예약 가용성 검증 (available = current - reserved)
- BR-STK-006: 예약 해제 (reserved -> released)
"""

from __future__ import annotations

import logging
from decimal import Decimal

from oneerp_core.document import BaseDocument
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class _StockReservation(BaseDocument):
    """재고 예약 레코드 모델."""

    item_code: str = ""
    warehouse: str = ""
    reserved_qty: Decimal = Decimal(0)
    sales_order_id: str = ""
    status: str = "reserved"  # reserved | released


class StockReservationService:
    """재고 예약 서비스.

    판매주문의 각 아이템에 대해 재고를 예약하고,
    납품 완료 시 예약을 해제한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._rsv_repo = Repository("stock_reservations", tenant_id=tenant_id)

    def check_availability(self, item_code: str, warehouse: str) -> dict[str, Decimal]:
        """품목/창고별 가용 재고를 조회한다.

        Returns:
            {"current_qty": 실재고, "reserved_qty": 예약합계, "available_qty": 가용재고}
        """
        bin_repo = Repository("stock_bins", tenant_id=self._tenant_id)
        bins = bin_repo.find_many(
            {"item_code": item_code, "warehouse": warehouse},
            limit=1,
        )
        current_qty = Decimal(str(bins[0].get("current_qty", 0))) if bins else Decimal(0)

        existing = self._rsv_repo.find_many(
            {"item_code": item_code, "warehouse": warehouse, "status": "reserved"},
            limit=0,
        )
        reserved_total = sum((Decimal(str(r.get("reserved_qty", 0))) for r in existing), Decimal(0))
        available = current_qty - reserved_total

        return {
            "current_qty": current_qty,
            "reserved_qty": reserved_total,
            "available_qty": available,
        }

    def reserve_for_sales_order(self, sales_order_id: str) -> list[str]:
        """판매주문의 각 아이템에 대해 예약 레코드를 생성한다.

        Returns:
            생성된 예약 ID 목록
        """
        so_repo = Repository("sales_orders", tenant_id=self._tenant_id)
        so_doc = so_repo.find_by_id(sales_order_id)
        if not so_doc:
            msg = f"판매주문을 찾을 수 없습니다: {sales_order_id}"
            raise_not_found(msg)

        reservation_ids: list[str] = []

        for item in so_doc.get("items", []):
            item_code = item.get("item_code", "")
            warehouse = item.get("warehouse", "") or so_doc.get("warehouse", "")
            qty = Decimal(str(item.get("qty", 0)))

            availability = self.check_availability(item_code, warehouse)
            available = availability["available_qty"]

            if available < qty:
                msg = (
                    f"예약 가용 재고 부족: {item_code} @ {warehouse} "
                    f"(가용: {available}, 요청: {qty})"
                )
                raise_unprocessable("ERR-STK-006", msg)

            rsv_id = generate_name("SRSV", tenant_id=self._tenant_id)
            reservation = _StockReservation(
                _id=rsv_id,
                tenant_id=self._tenant_id,
                item_code=item_code,
                warehouse=warehouse,
                reserved_qty=qty,
                sales_order_id=sales_order_id,
                status="reserved",
            )
            self._rsv_repo.insert(reservation)
            reservation_ids.append(rsv_id)

        logger.info(
            "재고 예약 완료: %s (예약 %d건)",
            sales_order_id,
            len(reservation_ids),
        )
        return reservation_ids

    def release_reservation(self, delivery_note_id: str) -> list[str]:
        """납품전표와 연결된 판매주문의 예약을 해제한다.

        Returns:
            해제된 예약 ID 목록
        """
        dn_repo = Repository("delivery_notes", tenant_id=self._tenant_id)
        dn_doc = dn_repo.find_by_id(delivery_note_id)
        if not dn_doc:
            msg = f"납품전표를 찾을 수 없습니다: {delivery_note_id}"
            raise_not_found(msg)

        sales_order_id = dn_doc.get("sales_order_id", "")
        if not sales_order_id:
            logger.warning("납품전표에 판매주문 ID가 없습니다: %s", delivery_note_id)
            return []

        reservations = self._rsv_repo.find_many(
            {"sales_order_id": sales_order_id, "status": "reserved"},
            limit=100,
        )

        released_ids: list[str] = []
        for rsv in reservations:
            rsv_id = rsv["_id"]
            self._rsv_repo.update_by_id(rsv_id, {"status": "released"})
            released_ids.append(rsv_id)

        logger.info(
            "예약 해제 완료: %s → %s (해제 %d건)",
            delivery_note_id,
            sales_order_id,
            len(released_ids),
        )
        return released_ids
