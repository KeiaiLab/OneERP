"""렌탈 생명주기 서비스 — 렌탈 주문의 시작·반납·연장 비즈니스 로직."""

from __future__ import annotations

import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class RentalLifecycleService:
    """렌탈 주문 생명주기 관리.

    렌탈 시작(품목 상태 변경), 반납 처리, 기간 연장을 담당한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._order_repo = Repository("rental_orders", tenant_id=tenant_id)
        self._item_repo = Repository("rental_items", tenant_id=tenant_id)
        self._return_repo = Repository("rental_returns", tenant_id=tenant_id)

    def start_rental(self, order_id: str) -> dict[str, Any]:
        """렌탈을 시작하고 품목 상태를 변경한다.

        주문 상태를 active로 변경하고, 품목 상태를 rented로 변경한다.

        Args:
            order_id: 렌탈 주문 ID

        Returns:
            시작 결과 요약

        Raises:
            ValueError: 주문/품목이 없거나 상태가 유효하지 않은 경우
        """
        order = self._order_repo.find_by_id(order_id)
        if not order:
            msg = f"렌탈 주문 '{order_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        order_status = order.get("status", "")
        if order_status not in ("draft", "confirmed"):
            msg = f"렌탈 주문 상태가 '{order_status}'이므로 시작할 수 없습니다"
            raise ValueError(msg)

        item_id = order.get("rental_item_id", "")
        if item_id:
            item = self._item_repo.find_by_id(item_id)
            if not item:
                msg = f"렌탈 품목 '{item_id}'을 찾을 수 없습니다"
                raise ValueError(msg)

            item_status = item.get("status", "")
            if item_status != "available":
                msg = f"렌탈 품목 상태가 '{item_status}'이므로 대여할 수 없습니다"
                raise ValueError(msg)

            self._item_repo.update_by_id(item_id, {"status": "rented"})

        self._order_repo.update_by_id(order_id, {"status": "active"})

        logger.info("렌탈 시작: %s (품목: %s)", order_id, item_id)

        return {
            "order_id": order_id,
            "rental_item_id": item_id,
            "status": "active",
        }

    def process_return(
        self,
        order_id: str,
        *,
        return_date: date | None = None,
        condition: str = "good",
        damage_charge: Decimal = Decimal(0),
    ) -> dict[str, Any]:
        """반납을 처리한다.

        반납 문서를 생성하고, 주문 상태를 returned로, 품목을 available로 변경한다.
        연체 시 연체료를 자동 계산한다.

        Args:
            order_id: 렌탈 주문 ID
            return_date: 실제 반납일 (미지정 시 오늘)
            condition: 반납 상태 (good/fair/damaged/lost)
            damage_charge: 손상 비용

        Returns:
            반납 처리 결과

        Raises:
            ValueError: 주문이 없거나 active 상태가 아닌 경우
        """
        order = self._order_repo.find_by_id(order_id)
        if not order:
            msg = f"렌탈 주문 '{order_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if order.get("status") != "active":
            msg = f"렌탈 주문 상태가 '{order.get('status')}'이므로 반납할 수 없습니다"
            raise ValueError(msg)

        actual_return = return_date or date.today()  # noqa: DTZ011

        # 연체료 계산
        late_fee = Decimal(0)
        end_date_raw = order.get("end_date")
        if end_date_raw:
            expected_end = (
                date.fromisoformat(end_date_raw) if isinstance(end_date_raw, str) else end_date_raw
            )
            if actual_return > expected_end:
                overdue_days = (actual_return - expected_end).days
                daily_rate = Decimal(str(order.get("daily_rate", 0)))
                late_fee = (daily_rate * overdue_days * Decimal("1.5")).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )

        # 보증금 환불 계산 (손상/분실이 아니면 전액 환불)
        deposit = Decimal(str(order.get("deposit_amount", 0)))
        deposit_refund = max(deposit - damage_charge, Decimal(0))
        if condition == "lost":
            deposit_refund = Decimal(0)

        # 반납 문서 생성
        return_id = generate_name("RNRET", tenant_id=self._tenant_id)
        self._return_repo.insert(
            {
                "_id": return_id,
                "rental_order_id": order_id,
                "return_date": actual_return,
                "condition": condition,
                "damage_charge": str(damage_charge),
                "late_fee": str(late_fee),
                "deposit_refund": str(deposit_refund),
                "tenant_id": self._tenant_id,
            }
        )

        # 주문 상태 업데이트
        self._order_repo.update_by_id(order_id, {"status": "returned"})

        # 품목 상태 복원 (분실이 아닌 경우)
        item_id = order.get("rental_item_id", "")
        if item_id and condition != "lost":
            new_status = "maintenance" if condition == "damaged" else "available"
            self._item_repo.update_by_id(item_id, {"status": new_status})
        elif item_id and condition == "lost":
            self._item_repo.update_by_id(item_id, {"status": "retired"})

        logger.info(
            "렌탈 반납 처리: %s (주문: %s, 연체료: %s)",
            return_id,
            order_id,
            late_fee,
        )

        return {
            "return_id": return_id,
            "order_id": order_id,
            "late_fee": late_fee,
            "damage_charge": damage_charge,
            "deposit_refund": deposit_refund,
            "status": "returned",
        }

    def extend_rental(
        self,
        order_id: str,
        *,
        new_end_date: date,
    ) -> dict[str, Any]:
        """렌탈 기간을 연장한다.

        주문의 종료일을 변경하고 총 금액을 재계산한다.

        Args:
            order_id: 렌탈 주문 ID
            new_end_date: 새로운 종료일

        Returns:
            연장 결과

        Raises:
            ValueError: 주문이 없거나 새 종료일이 현재 종료일보다 이전인 경우
        """
        order = self._order_repo.find_by_id(order_id)
        if not order:
            msg = f"렌탈 주문 '{order_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if order.get("status") not in ("active", "confirmed"):
            msg = f"렌탈 주문 상태가 '{order.get('status')}'이므로 연장할 수 없습니다"
            raise ValueError(msg)

        current_end_raw = order.get("end_date")
        if current_end_raw:
            current_end = (
                date.fromisoformat(current_end_raw)
                if isinstance(current_end_raw, str)
                else current_end_raw
            )
            if new_end_date <= current_end:
                msg = "새 종료일이 현재 종료일보다 이후여야 합니다"
                raise ValueError(msg)

        # 총 금액 재계산
        start_date_raw = order.get("start_date")
        daily_rate = Decimal(str(order.get("daily_rate", 0)))
        new_total = Decimal(0)
        if start_date_raw:
            start_date = (
                date.fromisoformat(start_date_raw)
                if isinstance(start_date_raw, str)
                else start_date_raw
            )
            rental_days = (new_end_date - start_date).days + 1
            new_total = (daily_rate * rental_days).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

        self._order_repo.update_by_id(
            order_id,
            {
                "end_date": new_end_date,
                "total_amount": str(new_total),
            },
        )

        logger.info(
            "렌탈 기간 연장: %s (새 종료일: %s, 새 금액: %s)",
            order_id,
            new_end_date,
            new_total,
        )

        return {
            "order_id": order_id,
            "new_end_date": new_end_date,
            "new_total_amount": new_total,
        }
