"""구독 관리 서비스 — 구독 생성, 자동 청구, 갱신/해지 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-SELL-008: 구독 자동 청구 조건 (is_active + next_billing_date <= 현재)
- BR-SELL-009: 구독 next_billing_date 갱신 (청구 후 += billing_interval)
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class SubscriptionService:
    """구독/정기결제 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._plan_repo = Repository("subscription_plans", tenant_id=tenant_id)
        self._sub_repo = Repository("subscriptions", tenant_id=tenant_id)
        self._invoice_repo = Repository("subscription_invoices", tenant_id=tenant_id)

    def create_subscription(
        self,
        customer: str,
        plan_id: str,
        start_date: date,
    ) -> dict[str, Any]:
        """구독을 생성한다."""
        plan = self._plan_repo.find_by_id(plan_id)
        if not plan:
            msg = f"구독 플랜 '{plan_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        billing_interval = int(plan.get("billing_interval_days", 30))
        amount = float(plan.get("amount", 0))

        sub_id = generate_name("SUB", tenant_id=self._tenant_id)
        self._sub_repo.insert(
            {
                "_id": sub_id,
                "customer": customer,
                "plan": plan_id,
                "start_date": start_date,
                "next_billing_date": start_date + timedelta(days=billing_interval),
                "amount": amount,
                "status": "active",
                "tenant_id": self._tenant_id,
            }
        )

        logger.info("구독 생성: %s (고객: %s, 플랜: %s)", sub_id, customer, plan_id)
        return {"subscription_id": sub_id, "amount": amount, "status": "active"}

    def generate_invoices(
        self,
        as_of_date: date,
    ) -> dict[str, Any]:
        """BR-SELL-008/009: 만기 구독에 대해 청구서를 일괄 생성한다.

        BR-SELL-008: active이고 next_billing_date <= as_of_date인 구독만 대상.
        BR-SELL-009: 청구 생성 후 next_billing_date += billing_interval.
        """
        subscriptions = self._sub_repo.find_many(
            {"status": "active"},
            limit=50000,
        )

        created: list[dict[str, Any]] = []
        for sub in subscriptions:
            next_billing = sub.get("next_billing_date")
            if next_billing is None:
                continue

            if isinstance(next_billing, str):
                next_billing = date.fromisoformat(next_billing)

            if next_billing > as_of_date:
                continue

            inv_id = generate_name("SINV", tenant_id=self._tenant_id)
            amount = float(sub.get("amount", 0))
            self._invoice_repo.insert(
                {
                    "_id": inv_id,
                    "subscription": sub["_id"],
                    "customer": sub.get("customer", ""),
                    "amount": amount,
                    "billing_date": as_of_date,
                    "status": "pending",
                    "tenant_id": self._tenant_id,
                }
            )

            # 다음 청구일 업데이트
            plan = self._plan_repo.find_by_id(sub.get("plan", ""))
            interval = int(plan.get("billing_interval_days", 30)) if plan else 30
            self._sub_repo.update_by_id(
                sub["_id"],
                {"next_billing_date": as_of_date + timedelta(days=interval)},
            )

            created.append({"invoice_id": inv_id, "subscription": sub["_id"], "amount": amount})

        logger.info("구독 청구 생성: %d건 (기준일: %s)", len(created), as_of_date)
        return {"created_count": len(created), "invoices": created}

    def cancel_subscription(
        self,
        subscription_id: str,
        reason: str = "",
    ) -> dict[str, Any]:
        """구독을 해지한다."""
        sub = self._sub_repo.find_by_id(subscription_id)
        if not sub:
            msg = f"구독 '{subscription_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        self._sub_repo.update_by_id(
            subscription_id, {"status": "cancelled", "cancel_reason": reason}
        )
        logger.info("구독 해지: %s (사유: %s)", subscription_id, reason)
        return {"subscription_id": subscription_id, "status": "cancelled"}
