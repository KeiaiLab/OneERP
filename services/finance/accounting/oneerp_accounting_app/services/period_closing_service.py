"""기간 마감 서비스 — 회계기간 마감, 회계연도 결산 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-ACCT-011: 기간 마감 조건 (Draft 전표 0건)
- BR-ACCT-012: 연도 결산 조건 (모든 기간 closed)
- BR-ACCT-016: 이중 마감 금지
- BR-ACCT-017: 이중 결산 금지
- BR-ACCT-020: 손익 계산 (수익 - 비용)
"""

from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, cast

from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.events.outbox import OutboxMixin
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_accounting_app.models.period_closing_voucher import PeriodClosingVoucher

logger = logging.getLogger(__name__)

# 원화 반올림 단위
_KRW_QUANT = Decimal(1)


class PeriodClosingService:
    """기간 마감 비즈니스 로직.

    회계기간 마감 → 기간마감전표 생성 → 회계연도 결산 프로세스를 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._period_repo = Repository("accounting_periods", tenant_id=tenant_id)
        self._fy_repo = Repository("fiscal_years", tenant_id=tenant_id)
        self._je_repo = Repository("journal_entries", tenant_id=tenant_id)
        self._pcv_repo = Repository("period_closing_vouchers", tenant_id=tenant_id)

    def validate_period_closeable(self, period_id: str) -> dict[str, Any]:
        """BR-ACCT-011: 기간 마감 가능 여부를 검증한다.

        미제출(DRAFT) 분개전표가 있으면 마감할 수 없다.

        Returns:
            검증 결과 (closeable, draft_count, submitted_count)
        """
        period = self._get_period(period_id)

        start_date = period["start_date"]
        end_date = period["end_date"]

        # 기간 내 분개전표 조회
        all_entries = self._je_repo.find_many(
            {
                "posting_date": {"$gte": start_date, "$lte": end_date},
            },
            limit=10000,
        )

        draft_count = sum(1 for je in all_entries if je.get("docstatus", 0) == DocStatus.DRAFT)
        submitted_count = sum(
            1 for je in all_entries if je.get("docstatus", 0) == DocStatus.SUBMITTED
        )

        return {
            "period_id": period_id,
            "closeable": draft_count == 0,
            "draft_count": draft_count,
            "submitted_count": submitted_count,
            "total_entries": len(all_entries),
        }

    def close_period(
        self,
        period_id: str,
        closing_account: str,
        remarks: str = "",
    ) -> dict[str, Any]:
        """회계기간을 마감하고 기간마감전표를 생성한다.

        BR-ACCT-016: 이미 마감된 기간 재마감 금지
        BR-ACCT-011: Draft 전표 0건이어야 마감 가능
        BR-ACCT-020: 손익 = 수익 합계 - 비용 합계

        이벤트 발행: PERIOD_CLOSED

        Raises:
            OneERPError(ERR-ACCT-035): 이중 마감
            OneERPError(ERR-ACCT-033): 미제출 전표 존재
        """
        period = self._get_period(period_id)

        # BR-ACCT-016: 이중 마감 금지
        if period.get("status") == "closed":
            raise_unprocessable(
                "ERR-ACCT-035",
                f"이미 마감된 회계기간입니다 (ID: {period_id})",
            )

        # BR-ACCT-011: 마감 가능 여부 검증
        validation = self.validate_period_closeable(period_id)
        if not validation["closeable"]:
            raise_unprocessable(
                "ERR-ACCT-033",
                f"미제출 분개전표 {validation['draft_count']}건이 있어 "
                f"마감할 수 없습니다. 먼저 제출하거나 삭제하세요.",
            )

        # BR-ACCT-020: 기간 내 손익 집계
        net_income = self._calculate_net_income(
            period["start_date"],
            period["end_date"],
        )

        # 기간마감전표 생성
        pcv_id = generate_name("PCV", tenant_id=self._tenant_id)
        pcv = PeriodClosingVoucher(
            _id=pcv_id,
            fiscal_year=period.get("fiscal_year", ""),
            closing_account=closing_account,
            posting_date=period["end_date"],
            remarks=remarks or f"{period.get('period_name', '')} 기간 마감",
            tenant_id=self._tenant_id,
            docstatus=DocStatus.SUBMITTED,
        )
        self._pcv_repo.insert(pcv)

        # 회계기간 마감 처리 + PERIOD_CLOSED 이벤트 발행
        outbox_entry = OutboxMixin.create_outbox_entry(
            event_type=EventType.PERIOD_CLOSED,
            doc_id=period_id,
            tenant_id=self._tenant_id,
            data={
                "period_name": period.get("period_name", ""),
                "pcv_id": pcv_id,
                "net_income": str(net_income),
            },
        )
        self._period_repo.update_by_id(
            period_id,
            {"status": "closed", "_outbox": [outbox_entry]},
        )

        logger.info(
            "회계기간 마감: %s (전표: %s, 손익: %s)",
            period_id,
            pcv_id,
            net_income,
        )

        return {
            "period_id": period_id,
            "pcv_id": pcv_id,
            "net_income": net_income,
            "status": "closed",
        }

    def close_fiscal_year(
        self,
        fiscal_year_id: str,
        closing_account: str,
    ) -> dict[str, Any]:
        """회계연도를 결산한다.

        BR-ACCT-017: 이중 결산 금지
        BR-ACCT-012: 모든 회계기간이 마감되어야 결산 가능

        이벤트 발행: FISCAL_YEAR_CLOSED

        Raises:
            OneERPError(ERR-ACCT-035): 이미 결산됨
            OneERPError(ERR-ACCT-034): 미마감 기간 존재
        """
        fy = self._fy_repo.find_by_id(fiscal_year_id)
        if not fy:
            raise_not_found(f"회계연도 '{fiscal_year_id}'을 찾을 수 없습니다")
        fy = cast("dict[str, Any]", fy)

        # BR-ACCT-017: 이중 결산 금지
        if fy.get("is_closed"):
            raise_unprocessable(
                "ERR-ACCT-035",
                f"이미 결산된 회계연도입니다 (ID: {fiscal_year_id})",
            )

        # BR-ACCT-012: 모든 기간 마감 확인
        periods = self._period_repo.find_many(
            {"fiscal_year": fiscal_year_id},
            limit=100,
        )

        open_periods = [p for p in periods if p.get("status") != "closed"]
        if open_periods:
            names = [p.get("period_name", p["_id"]) for p in open_periods]
            raise_unprocessable(
                "ERR-ACCT-034",
                f"미마감 회계기간이 있습니다: {', '.join(names)}",
            )

        # 연간 손익 집계
        net_income = self._calculate_net_income(
            fy["start_date"],
            fy["end_date"],
        )

        # 회계연도 결산 + FISCAL_YEAR_CLOSED 이벤트 발행
        outbox_entry = OutboxMixin.create_outbox_entry(
            event_type=EventType.FISCAL_YEAR_CLOSED,
            doc_id=fiscal_year_id,
            tenant_id=self._tenant_id,
            data={
                "net_income": str(net_income),
                "closing_account": closing_account,
                "closed_periods": len(periods),
            },
        )
        self._fy_repo.update_by_id(
            fiscal_year_id,
            {
                "is_closed": True,
                "closing_account": closing_account,
                "_outbox": [outbox_entry],
            },
        )

        logger.info(
            "회계연도 결산: %s (연간 손익: %s, 마감계정: %s)",
            fiscal_year_id,
            net_income,
            closing_account,
        )

        return {
            "fiscal_year_id": fiscal_year_id,
            "net_income": net_income,
            "closed_periods": len(periods),
            "status": "closed",
        }

    # -- 내부 헬퍼 --

    def _get_period(self, period_id: str) -> dict[str, Any]:
        """회계기간을 조회한다."""
        period = self._period_repo.find_by_id(period_id)
        if not period:
            raise_not_found(f"회계기간 '{period_id}'을 찾을 수 없습니다")
        return cast("dict[str, Any]", period)

    def _calculate_net_income(
        self,
        start_date: Any,
        end_date: Any,
    ) -> Decimal:
        """BR-ACCT-020: 기간 내 손익(수익 - 비용)을 Decimal로 계산한다.

        제출된 분개전표의 수익/비용 계정 잔액을 집계한다.
        수익: credit - debit (순액)
        비용: debit - credit (순액)
        """
        entries = self._je_repo.find_many(
            {
                "posting_date": {"$gte": start_date, "$lte": end_date},
                "docstatus": DocStatus.SUBMITTED,
            },
            limit=50000,
        )

        total_income = Decimal(0)
        total_expense = Decimal(0)

        for je in entries:
            for item in je.get("items", []):
                account_type = item.get("account_type", "")
                debit = Decimal(str(item.get("debit", 0)))
                credit = Decimal(str(item.get("credit", 0)))

                if account_type == "income":
                    total_income += credit - debit
                elif account_type == "expense":
                    total_expense += debit - credit

        return (total_income - total_expense).quantize(_KRW_QUANT, rounding=ROUND_HALF_UP)
