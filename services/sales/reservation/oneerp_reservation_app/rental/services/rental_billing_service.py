"""렌탈 청구 서비스 — 렌탈 주문 기반 청구서 생성 및 금액 계산 비즈니스 로직."""

from __future__ import annotations

import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 청구 주기별 요금 배수
_BILLING_MULTIPLIERS: dict[str, int] = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
}


class RentalBillingService:
    """렌탈 청구 비즈니스 로직.

    렌탈 주문 기반 청구서를 생성하고 금액을 계산한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._order_repo = Repository("rental_orders", tenant_id=tenant_id)
        self._invoice_repo = Repository("rental_invoices", tenant_id=tenant_id)

    def calculate_rental_amount(
        self,
        daily_rate: Decimal,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """렌탈 기간에 따른 총 렌탈 금액을 계산한다.

        Args:
            daily_rate: 일일 요금
            start_date: 시작일
            end_date: 종료일

        Returns:
            총 렌탈 금액 (소수점 2자리 반올림)

        Raises:
            ValueError: 종료일이 시작일보다 이전인 경우
        """
        if end_date < start_date:
            msg = "종료일이 시작일보다 이전일 수 없습니다"
            raise ValueError(msg)

        rental_days = (end_date - start_date).days + 1
        amount = daily_rate * rental_days
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_late_fee(
        self,
        daily_rate: Decimal,
        expected_end: date,
        actual_return: date,
        *,
        late_fee_rate: Decimal = Decimal("1.5"),
    ) -> Decimal:
        """연체료를 계산한다.

        연체일수 * 일일요금 * 연체요율로 계산한다.

        Args:
            daily_rate: 일일 요금
            expected_end: 예정 반납일
            actual_return: 실제 반납일
            late_fee_rate: 연체 요율 배수 (기본 1.5배)

        Returns:
            연체료 (연체 없으면 0)
        """
        if actual_return <= expected_end:
            return Decimal(0)

        overdue_days = (actual_return - expected_end).days
        fee = daily_rate * overdue_days * late_fee_rate
        return fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def create_invoice_from_order(
        self,
        order_id: str,
        *,
        billing_period_start: date | None = None,
        billing_period_end: date | None = None,
        tax_rate: Decimal = Decimal("0.1"),
    ) -> dict[str, Any]:
        """렌탈 주문 기반으로 청구서를 생성한다.

        Args:
            order_id: 렌탈 주문 ID
            billing_period_start: 청구 기간 시작일 (미지정 시 주문 시작일)
            billing_period_end: 청구 기간 종료일 (미지정 시 주문 종료일)
            tax_rate: 세율 (기본 10%)

        Returns:
            생성된 청구서 요약 정보

        Raises:
            ValueError: 주문을 찾을 수 없거나 날짜가 유효하지 않은 경우
        """
        order = self._order_repo.find_by_id(order_id)
        if not order:
            msg = f"렌탈 주문 '{order_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        # 청구 기간 결정
        period_start = billing_period_start or order.get("start_date")
        period_end = billing_period_end or order.get("end_date")

        if not period_start or not period_end:
            msg = "청구 기간 시작일과 종료일이 필요합니다"
            raise ValueError(msg)

        # 날짜 문자열 → date 변환
        if isinstance(period_start, str):
            period_start = date.fromisoformat(period_start)
        if isinstance(period_end, str):
            period_end = date.fromisoformat(period_end)

        daily_rate = Decimal(str(order.get("daily_rate", 0)))
        rental_amount = self.calculate_rental_amount(daily_rate, period_start, period_end)
        tax_amount = (rental_amount * tax_rate).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        total_amount = rental_amount + tax_amount

        invoice_id = generate_name("RNINV", tenant_id=self._tenant_id)
        self._invoice_repo.insert(
            {
                "_id": invoice_id,
                "rental_order_id": order_id,
                "customer_id": order.get("customer_id", ""),
                "invoice_date": date.today(),  # noqa: DTZ011
                "billing_period_start": period_start,
                "billing_period_end": period_end,
                "rental_amount": str(rental_amount),
                "tax_amount": str(tax_amount),
                "total_amount": str(total_amount),
                "status": "issued",
                "tenant_id": self._tenant_id,
            }
        )

        logger.info(
            "렌탈 청구서 생성: %s (주문: %s, 금액: %s)",
            invoice_id,
            order_id,
            total_amount,
        )

        return {
            "invoice_id": invoice_id,
            "rental_order_id": order_id,
            "rental_amount": rental_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
        }
