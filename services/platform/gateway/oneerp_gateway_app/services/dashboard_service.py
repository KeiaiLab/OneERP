"""대시보드 KPI 집계 서비스.

여러 서비스의 컬렉션에 직접 접근하여 크로스서비스 KPI를 집계한다.
Gateway는 크로스서비스 집계 역할을 담당한다.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class DashboardService:
    """대시보드 KPI 집계 서비스."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id

    def _repo(self, collection: str) -> Repository:
        """테넌트 스코프 Repository를 생성한다."""
        return Repository(collection, tenant_id=self._tenant_id)

    def get_kpis(self) -> dict[str, Any]:
        """현재 테넌트의 KPI를 집계한다.

        Returns:
            매출/구매/재고/결재/HR 카테고리별 KPI 딕셔너리.
        """
        now = datetime.now(tz=UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        return {
            "sales": self._aggregate_sales(month_start),
            "buying": self._aggregate_buying(month_start),
            "stock": self._aggregate_stock(),
            "approval": self._aggregate_approval(),
            "hr": self._aggregate_hr(month_start),
            "generated_at": now.isoformat(),
        }

    def _aggregate_sales(self, month_start: datetime) -> dict[str, Any]:
        """매출 KPI를 집계한다."""
        sales_repo = self._repo("sales_orders")

        # 이번 달 매출 합계
        monthly_orders = sales_repo.find_many(
            {"created_at": {"$gte": month_start}, "docstatus": 1},
            limit=0,
        )
        monthly_sales = sum(float(order.get("grand_total", 0)) for order in monthly_orders)

        # 전월 매출 (성장률 계산용)
        prev_month_start = month_start.replace(
            month=month_start.month - 1 if month_start.month > 1 else 12,
            year=month_start.year if month_start.month > 1 else month_start.year - 1,
        )
        prev_orders = sales_repo.find_many(
            {
                "created_at": {"$gte": prev_month_start, "$lt": month_start},
                "docstatus": 1,
            },
            limit=0,
        )
        prev_sales = sum(float(order.get("grand_total", 0)) for order in prev_orders)

        # 성장률 계산
        growth_rate = 0.0
        if prev_sales > 0:
            growth_rate = round((monthly_sales - prev_sales) / prev_sales * 100, 2)

        # 미수금
        ar_repo = self._repo("accounts_receivable")
        ar_docs = ar_repo.find_many({"status": "unpaid"}, limit=0)
        outstanding_receivables = sum(float(doc.get("outstanding_amount", 0)) for doc in ar_docs)

        return {
            "monthly_sales": monthly_sales,
            "growth_rate": growth_rate,
            "outstanding_receivables": outstanding_receivables,
        }

    def _aggregate_buying(self, month_start: datetime) -> dict[str, Any]:
        """구매 KPI를 집계한다."""
        po_repo = self._repo("purchase_orders")

        # 대기 중인 구매주문 수
        pending_purchase_orders = po_repo.count({"docstatus": 0})

        # 이번 달 구매 합계
        monthly_orders = po_repo.find_many(
            {"created_at": {"$gte": month_start}, "docstatus": 1},
            limit=0,
        )
        monthly_purchases = sum(float(order.get("grand_total", 0)) for order in monthly_orders)

        return {
            "pending_purchase_orders": pending_purchase_orders,
            "monthly_purchases": monthly_purchases,
        }

    def _aggregate_stock(self) -> dict[str, Any]:
        """재고 KPI를 집계한다."""
        stock_repo = self._repo("stock_balances")

        # 재고 부족 품목 수
        low_stock_items = stock_repo.count({"is_low_stock": True})

        # 재고 회전율 (간이 계산: 출고건수 / 총 품목수)
        item_count = stock_repo.count()
        entry_repo = self._repo("stock_entries")
        outgoing_count = entry_repo.count({"entry_type": "outgoing"})

        stock_turnover_rate = 0.0
        if item_count > 0:
            stock_turnover_rate = round(outgoing_count / item_count, 2)

        return {
            "low_stock_items": low_stock_items,
            "stock_turnover_rate": stock_turnover_rate,
        }

    def _aggregate_approval(self) -> dict[str, Any]:
        """결재 KPI를 집계한다."""
        approval_repo = self._repo("approval_requests")
        active_requests = approval_repo.find_many(
            {"status": {"$in": ["pending", "submitted"]}},
            limit=0,
        )

        return {
            "pending_approvals": len(active_requests),
            "my_pending_approvals": 0,
        }

    def _aggregate_approval_for_user(self, user_sub: str) -> dict[str, Any]:
        """특정 사용자의 결재 KPI를 집계한다."""
        approval_repo = self._repo("approval_requests")
        active_requests = approval_repo.find_many(
            {"status": {"$in": ["pending", "submitted"]}},
            limit=0,
        )
        my_pending_approvals = 0
        for request in active_requests:
            current_step = request.get("current_step", 1)
            current_lines = [
                line
                for line in request.get("approval_lines", [])
                if line.get("step") == current_step and line.get("status", "pending") == "pending"
            ]
            if any(line.get("approver") == user_sub for line in current_lines):
                my_pending_approvals += 1

        return {
            "pending_approvals": len(active_requests),
            "my_pending_approvals": my_pending_approvals,
        }

    def _aggregate_hr(self, month_start: datetime) -> dict[str, Any]:
        """HR KPI를 집계한다."""
        emp_repo = self._repo("employees")
        total_employees = emp_repo.count({"is_active": True})

        # 이번 달 급여 합계
        payroll_repo = self._repo("salary_slips")
        monthly_slips = payroll_repo.find_many(
            {"created_at": {"$gte": month_start}, "docstatus": 1},
            limit=0,
        )
        this_month_payroll = sum(float(slip.get("net_pay", 0)) for slip in monthly_slips)

        return {
            "total_employees": total_employees,
            "this_month_payroll": this_month_payroll,
        }

    def get_kpis_for_user(self, user_sub: str) -> dict[str, Any]:
        """특정 사용자 기준 KPI를 집계한다 (내 결재 포함).

        Args:
            user_sub: 현재 사용자 식별자.

        Returns:
            KPI 딕셔너리 (사용자별 결재 포함).
        """
        kpis = self.get_kpis()
        kpis["approval"] = self._aggregate_approval_for_user(user_sub)
        return kpis

    def get_monthly_sales_chart(self, months: int = 6) -> list[dict[str, Any]]:
        """최근 N개월 월별 매출 합계를 반환한다."""
        sales_repo = self._repo("sales_orders")
        orders = sales_repo.find_many({"docstatus": 1}, limit=0)

        monthly_totals: dict[str, float] = defaultdict(float)
        for order in orders:
            created_at = order.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except ValueError:
                    continue
            if not isinstance(created_at, datetime):
                continue
            month_key = created_at.astimezone(UTC).strftime("%Y-%m")
            monthly_totals[month_key] += float(order.get("grand_total", 0))

        return [
            {"month": month, "amount": int(amount)}
            for month, amount in sorted(monthly_totals.items())[-months:]
        ]

    def get_tenant_overview(self) -> list[dict[str, Any]]:
        """super_admin용 테넌트별 개요를 반환한다.

        각 테넌트의 사용자 수, 문서 수 등 기본 통계를 집계한다.
        """
        tenant_repo = Repository("tenants")
        tenants = tenant_repo.find_many(limit=100)

        overview: list[dict[str, Any]] = []
        for tenant in tenants:
            tid = tenant.get("_id", "")
            user_repo = Repository("users", tenant_id=tid)
            user_count = user_repo.count()

            overview.append(
                {
                    "tenant_id": tid,
                    "tenant_name": tenant.get("tenant_name", ""),
                    "plan": tenant.get("plan", "standard"),
                    "is_active": tenant.get("is_active", True),
                    "user_count": user_count,
                }
            )

        return overview
