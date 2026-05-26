"""자금관리 서비스 — 자금 예측, 대출 관리 비즈니스 로직."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class TreasuryService:
    """자금관리 비즈니스 로직.

    자금 흐름 예측, 대출 상환 스케줄 생성을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._forecast_repo = Repository("cash_flow_forecasts", tenant_id=tenant_id)
        self._loan_repo = Repository("loan_applications", tenant_id=tenant_id)
        self._schedule_repo = Repository("loan_repayment_schedules", tenant_id=tenant_id)
        self._ar_repo = Repository("accounts_receivable", tenant_id=tenant_id)
        self._ap_repo = Repository("accounts_payable", tenant_id=tenant_id)

    def forecast_cash_flow(
        self,
        as_of_date: date,
        periods: int = 3,
    ) -> dict[str, Any]:
        """30/60/90일 자금 흐름을 예측한다.

        Args:
            as_of_date: 기준일
            periods: 예측 기간 수 (기본 3 = 30/60/90일)

        Returns:
            기간별 예측 현금 흐름
        """
        # 미수금(유입 예상) 조회
        receivables = self._ar_repo.find_many({}, limit=50000)
        # 미지급금(유출 예상) 조회
        payables = self._ap_repo.find_many({}, limit=50000)

        forecasts: list[dict[str, Any]] = []
        for period_idx in range(1, periods + 1):
            days = period_idx * 30
            period_end = as_of_date + timedelta(days=days)
            period_start = as_of_date + timedelta(days=(period_idx - 1) * 30)

            # 해당 기간 내 만기 미수금 합계
            inflow = sum(
                float(ar.get("outstanding_amount", 0))
                for ar in receivables
                if _date_in_range(ar.get("due_date"), period_start, period_end)
            )

            # 해당 기간 내 만기 미지급금 합계
            outflow = sum(
                float(ap.get("outstanding_amount", 0))
                for ap in payables
                if _date_in_range(ap.get("due_date"), period_start, period_end)
            )

            forecasts.append(
                {
                    "period": f"{days}일",
                    "period_end": str(period_end),
                    "expected_inflow": round(inflow, 2),
                    "expected_outflow": round(outflow, 2),
                    "net_cash_flow": round(inflow - outflow, 2),
                }
            )

        logger.info("자금 예측 생성: %d개 기간 (기준일: %s)", len(forecasts), as_of_date)

        return {
            "as_of_date": str(as_of_date),
            "periods": forecasts,
        }

    def generate_repayment_schedule(
        self,
        loan_id: str,
    ) -> dict[str, Any]:
        """대출 상환 스케줄을 생성한다.

        원리금균등 상환 방식으로 스케줄 생성.

        Args:
            loan_id: 대출 ID

        Returns:
            상환 스케줄 (installments)
        """
        loan = self._loan_repo.find_by_id(loan_id)
        if not loan:
            msg = f"대출 '{loan_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        principal = float(loan.get("loan_amount", 0))
        annual_rate = float(loan.get("interest_rate", 0)) / 100
        term_months = int(loan.get("term_months", 12))

        if principal <= 0 or term_months <= 0:
            msg = "대출 금액과 기간은 0보다 커야 합니다"
            raise ValueError(msg)

        # 원리금균등 상환 계산
        monthly_rate = annual_rate / 12
        if monthly_rate > 0:
            monthly_payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** -term_months)
        else:
            monthly_payment = principal / term_months

        installments: list[dict[str, Any]] = []
        remaining = principal
        start_date = loan.get("start_date", datetime.now(tz=UTC).date())

        for month in range(1, term_months + 1):
            interest = round(remaining * monthly_rate, 2)
            principal_payment = round(monthly_payment - interest, 2)
            remaining = round(max(remaining - principal_payment, 0), 2)

            if isinstance(start_date, date):
                due = start_date + timedelta(days=30 * month)
            else:
                due = str(start_date)

            installments.append(
                {
                    "installment": month,
                    "due_date": str(due),
                    "principal": principal_payment,
                    "interest": interest,
                    "payment": round(monthly_payment, 2),
                    "remaining_balance": remaining,
                }
            )

        # 스케줄 저장
        schedule_id = generate_name("LRS", tenant_id=self._tenant_id)
        self._schedule_repo.insert(
            {
                "_id": schedule_id,
                "loan_id": loan_id,
                "installments": installments,
                "total_interest": round(sum(i["interest"] for i in installments), 2),
                "total_payment": round(sum(i["payment"] for i in installments), 2),
                "tenant_id": self._tenant_id,
            }
        )

        logger.info(
            "상환 스케줄 생성: %s (대출: %s, %d개월)",
            schedule_id,
            loan_id,
            term_months,
        )

        return {
            "schedule_id": schedule_id,
            "loan_id": loan_id,
            "term_months": term_months,
            "monthly_payment": round(monthly_payment, 2),
            "total_interest": round(sum(i["interest"] for i in installments), 2),
            "installment_count": len(installments),
        }


def _date_in_range(
    value: Any,
    start: date,
    end: date,
) -> bool:
    """값이 날짜 범위 내인지 확인한다."""
    if value is None:
        return False
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value)
        except ValueError:
            return False
    if isinstance(value, date):
        return start <= value <= end
    return False
