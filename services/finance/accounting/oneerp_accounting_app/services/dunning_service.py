"""독촉 서비스 — 연체 고객 독촉장 자동 생성 비즈니스 로직."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_accounting_app.models.dunning import Dunning

logger = logging.getLogger(__name__)

# 독촉 단계별 기준일 (연체일 기준)
_DUNNING_LEVEL_DAYS: dict[int, int] = {
    1: 30,  # 1단계: 30일 이상 연체
    2: 60,  # 2단계: 60일 이상 연체
    3: 90,  # 3단계: 90일 이상 연체
}

# 독촉 단계별 수수료율 (연체금액 대비)
_DUNNING_FEE_RATES: dict[int, float] = {
    1: 0.01,  # 1%
    2: 0.02,  # 2%
    3: 0.05,  # 5%
}


class DunningService:
    """독촉장 자동 생성 비즈니스 로직.

    연체 매출채권을 분석하여 단계별 독촉장을 자동 생성한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._dunning_repo = Repository("dunnings", tenant_id=tenant_id)
        self._ar_repo = Repository("accounts_receivable", tenant_id=tenant_id)

    def generate_dunnings(
        self,
        as_of_date: date | None = None,
    ) -> dict[str, Any]:
        """연체 고객에 대해 독촉장을 일괄 생성한다.

        Args:
            as_of_date: 기준일 (기본: 오늘)

        Returns:
            생성 결과 (created_count, dunnings)
        """
        if as_of_date is None:
            as_of_date = datetime.now(tz=UTC).date()

        # 미수금 조회 (미결제)
        receivables = self._ar_repo.find_many({}, limit=50000)

        # 고객별 연체 집계
        customer_overdue: dict[str, list[dict[str, Any]]] = {}
        for ar in receivables:
            outstanding = float(ar.get("outstanding_amount", 0))
            if outstanding <= 0:
                continue

            due_date = ar.get("due_date")
            if due_date is None:
                continue

            # due_date를 date 객체로 변환
            if isinstance(due_date, datetime):
                due_date = due_date.date()
            elif isinstance(due_date, str):
                due_date = date.fromisoformat(due_date)

            if due_date >= as_of_date:
                continue  # 아직 만기 전

            customer = ar.get("customer", "")
            if not customer:
                continue

            customer_overdue.setdefault(customer, []).append(
                {
                    "invoice_id": ar.get("invoice_id", ar.get("_id", "")),
                    "outstanding_amount": outstanding,
                    "due_date": due_date,
                    "overdue_days": (as_of_date - due_date).days,
                }
            )

        # 고객별 독촉장 생성
        created_dunnings: list[dict[str, Any]] = []
        for customer, overdue_items in customer_overdue.items():
            total_outstanding = sum(item["outstanding_amount"] for item in overdue_items)
            max_overdue_days = max(item["overdue_days"] for item in overdue_items)

            # 독촉 단계 결정
            dunning_level = self.calculate_dunning_level(max_overdue_days)
            if dunning_level == 0:
                continue  # 독촉 기준 미달

            # 기존 독촉장 확인 (동일 고객, 동일 단계 중복 방지)
            existing = self._dunning_repo.find_many(
                {
                    "customer": customer,
                    "dunning_level": dunning_level,
                    "docstatus": {"$ne": 2},  # 취소되지 않은 것
                },
                limit=1,
            )
            if existing:
                continue

            dunning_fee = self.calculate_dunning_fee(total_outstanding, dunning_level)
            dunning_fee_dec = Decimal(str(dunning_fee))

            dun_id = generate_name("DUN", tenant_id=self._tenant_id)
            doc = Dunning(
                _id=dun_id,
                customer=customer,
                outstanding_amount=Decimal(str(total_outstanding)),
                dunning_level=dunning_level,
                dunning_date=as_of_date,
                dunning_fee=dunning_fee_dec,
                tenant_id=self._tenant_id,
            )
            self._dunning_repo.insert(doc)

            created_dunnings.append(
                {
                    "dunning_id": dun_id,
                    "customer": customer,
                    "outstanding_amount": total_outstanding,
                    "dunning_level": dunning_level,
                    "dunning_fee": dunning_fee,
                    "overdue_days": max_overdue_days,
                }
            )

        logger.info(
            "독촉장 일괄 생성: %d건 (기준일: %s)",
            len(created_dunnings),
            as_of_date,
        )

        return {
            "as_of_date": str(as_of_date),
            "created_count": len(created_dunnings),
            "dunnings": created_dunnings,
        }

    @staticmethod
    def calculate_dunning_level(overdue_days: int) -> int:
        """연체일 수에 따른 독촉 단계를 결정한다.

        Returns:
            독촉 단계 (0: 독촉 불필요, 1~3: 단계)
        """
        level = 0
        for dunning_level, min_days in sorted(_DUNNING_LEVEL_DAYS.items()):
            if overdue_days >= min_days:
                level = dunning_level
        return level

    @staticmethod
    def calculate_dunning_fee(outstanding_amount: float, dunning_level: int) -> float:
        """독촉 수수료를 계산한다.

        단계별 수수료율 x 연체금액.

        Returns:
            독촉 수수료
        """
        rate = _DUNNING_FEE_RATES.get(dunning_level, 0)
        return round(outstanding_amount * rate, 2)
