"""재무제표 보고서 API 라우터.

L2 API 계약:
- GET /api/v1/reports/balance-sheet — 재무상태표 조회
- GET /api/v1/reports/income-statement — 손익계산서 조회
- GET /api/v1/reports/trial-balance — 시산표 조회
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..services.kifrs_service import KIFRSService

router = APIRouter(prefix="/api/v1/reports", tags=["보고서"])


@router.get(
    "/balance-sheet",
    dependencies=[Depends(require_permission("report:read"))],
)
def get_balance_sheet(
    period_start: date,
    period_end: date,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """K-IFRS 기준 재무상태표를 생성한다.

    Query Params:
        period_start: 기간 시작일 (YYYY-MM-DD)
        period_end: 기간 종료일 (YYYY-MM-DD)
    """
    svc = KIFRSService(tenant_id=user.tenant_id)
    return svc.generate_financial_statement(period_start, period_end, "balance_sheet")


@router.get(
    "/income-statement",
    dependencies=[Depends(require_permission("report:read"))],
)
def get_income_statement(
    period_start: date,
    period_end: date,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """K-IFRS 기준 손익계산서를 생성한다.

    Query Params:
        period_start: 기간 시작일 (YYYY-MM-DD)
        period_end: 기간 종료일 (YYYY-MM-DD)
    """
    svc = KIFRSService(tenant_id=user.tenant_id)
    return svc.generate_financial_statement(period_start, period_end, "income_statement")


@router.get(
    "/trial-balance",
    dependencies=[Depends(require_permission("report:read"))],
)
def get_trial_balance(
    period_start: date,
    period_end: date,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """기간 내 시산표(계정별 차변/대변 합계)를 생성한다.

    제출(SUBMITTED) 상태의 분개전표만 집계한다.

    Query Params:
        period_start: 기간 시작일 (YYYY-MM-DD)
        period_end: 기간 종료일 (YYYY-MM-DD)
    """
    repo = Repository("journal_entries", tenant_id=user.tenant_id)

    start_dt = datetime(period_start.year, period_start.month, period_start.day, tzinfo=UTC)
    end_dt = datetime(period_end.year, period_end.month, period_end.day, 23, 59, 59, tzinfo=UTC)

    journals = repo.find_many(
        {
            "posting_date": {"$gte": start_dt, "$lte": end_dt},
            "docstatus": DocStatus.SUBMITTED,
        },
        limit=10000,
    )

    # 계정별 차변/대변 합계 집계
    account_totals: dict[str, dict[str, float]] = {}
    for journal in journals:
        for item in journal.get("items", []):
            account = item.get("account", "")
            debit = item.get("debit", 0.0)
            credit = item.get("credit", 0.0)
            if account not in account_totals:
                account_totals[account] = {"debit": 0.0, "credit": 0.0}
            account_totals[account]["debit"] += debit
            account_totals[account]["credit"] += credit

    items = [
        {
            "account": account,
            "debit": round(totals["debit"], 2),
            "credit": round(totals["credit"], 2),
            "balance": round(totals["debit"] - totals["credit"], 2),
        }
        for account, totals in sorted(account_totals.items())
    ]

    total_debit = round(float(sum((i["debit"] for i in items), 0.0)), 2)
    total_credit = round(float(sum((i["credit"] for i in items), 0.0)), 2)

    return {
        "report_type": "trial_balance",
        "period": {
            "start": period_start.isoformat(),
            "end": period_end.isoformat(),
        },
        "items": items,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": abs(total_debit - total_credit) < 1e-9,
    }
