"""구독 라이프사이클 서비스 — 구독 활성화·일시정지·해지·갱신을 관리한다."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 유효한 구독 상태 전환 맵
_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "activate": frozenset({"draft"}),
    "pause": frozenset({"active"}),
    "resume": frozenset({"paused"}),
    "cancel": frozenset({"active", "paused"}),
}

# 청구 주기별 일수
_INTERVAL_DAYS: dict[str, int] = {
    "monthly": 30,
    "quarterly": 90,
    "yearly": 365,
}

_SINV_PREFIX = "SINV"


class SubscriptionLifecycleService:
    """구독 라이프사이클 서비스.

    구독 상태 전환, 갱신, 청구 생성을 담당한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._sub_repo = Repository("subscriptions", tenant_id=tenant_id)
        self._plan_repo = Repository("subscription_plans", tenant_id=tenant_id)
        self._invoice_repo = Repository("subscription_invoices", tenant_id=tenant_id)

    def _transition(self, sub_id: str, action: str, extra: dict[str, Any] | None = None) -> dict:
        """구독 상태를 전환한다."""
        sub = self._sub_repo.find_by_id(sub_id)
        if not sub:
            msg = f"구독 '{sub_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        current = sub.get("status", "")
        allowed = _STATUS_TRANSITIONS.get(action, frozenset())
        if current not in allowed:
            msg = f"'{action}' 불가: 현재 상태 '{current}'"
            raise ValueError(msg)

        new_status_map = {
            "activate": "active",
            "pause": "paused",
            "resume": "active",
            "cancel": "cancelled",
        }
        new_status = new_status_map[action]

        update: dict[str, Any] = {
            "status": new_status,
            "updated_at": datetime.now(tz=UTC).isoformat(),
        }
        if extra:
            update.update(extra)

        self._sub_repo.update_by_id(sub_id, update)
        logger.info("구독 상태 전환: %s [%s → %s]", sub_id, current, new_status)
        return {"subscription_id": sub_id, "status": new_status}

    def activate(self, sub_id: str) -> dict[str, Any]:
        """구독을 활성화한다.

        draft → active 전환, 기간 및 다음 청구일을 설정한다.
        """
        sub = self._sub_repo.find_by_id(sub_id)
        if not sub:
            msg = f"구독 '{sub_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        plan = self._plan_repo.find_by_id(sub.get("plan_id", ""))
        interval = plan.get("billing_interval", "monthly") if plan else "monthly"
        days = _INTERVAL_DAYS.get(interval, 30)

        today = datetime.now(tz=UTC).date()
        period_end = today + timedelta(days=days)

        extra = {
            "start_date": today.isoformat(),
            "current_period_start": today.isoformat(),
            "current_period_end": period_end.isoformat(),
            "next_billing_date": period_end.isoformat(),
        }
        return self._transition(sub_id, "activate", extra)

    def pause(self, sub_id: str) -> dict[str, Any]:
        """구독을 일시정지한다."""
        return self._transition(sub_id, "pause")

    def resume(self, sub_id: str) -> dict[str, Any]:
        """구독을 재개한다."""
        return self._transition(sub_id, "resume")

    def cancel(self, sub_id: str, reason: str = "") -> dict[str, Any]:
        """구독을 해지한다."""
        extra = {"cancel_reason": reason, "end_date": datetime.now(tz=UTC).date().isoformat()}
        return self._transition(sub_id, "cancel", extra)

    def generate_invoice(self, sub_id: str) -> dict[str, Any]:
        """구독 청구서를 생성한다.

        Args:
            sub_id: 구독 ID

        Returns:
            생성된 청구서 정보

        Raises:
            ValueError: 구독이 없거나 active 상태가 아닌 경우
        """
        sub = self._sub_repo.find_by_id(sub_id)
        if not sub:
            msg = f"구독 '{sub_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if sub.get("status") != "active":
            msg = f"청구 생성 불가: 현재 상태 '{sub.get('status')}'"
            raise ValueError(msg)

        plan = self._plan_repo.find_by_id(sub.get("plan_id", ""))
        price = Decimal(str(plan.get("price", "0"))) if plan else Decimal(0)

        invoice_id = generate_name(_SINV_PREFIX, tenant_id=self._tenant_id)
        doc: dict[str, Any] = {
            "_id": invoice_id,
            "tenant_id": self._tenant_id,
            "subscription_id": sub_id,
            "billing_period": {
                "start": sub.get("current_period_start", ""),
                "end": sub.get("current_period_end", ""),
            },
            "amount": str(price),
            "status": "draft",
            "company": sub.get("company", ""),
        }
        self._invoice_repo.insert(doc)

        logger.info("구독 청구 생성: %s → %s", sub_id, invoice_id)
        return {
            "invoice_id": invoice_id,
            "subscription_id": sub_id,
            "amount": str(price),
            "status": "draft",
        }
