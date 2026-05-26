"""부가세 신고 자동 세액 계산 서비스.

L2 비즈니스 룰 매핑:
- BR-KTAX-003: 부가세 세율 10%
- BR-KTAX-004: 부가세 신고 기간 (1기예정/1기확정/2기예정/2기확정)
- BR-KTAX-005: net_tax = output_tax - input_tax (양수=납부, 음수=환급)
- BR-KTAX-016: 마감된 기간 세무 변경 금지
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import ROUND_DOWN, Decimal
from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_unprocessable
from oneerp_core.repository import Repository

from oneerp_accounting_app.models.vat_return import VATReturn

logger = logging.getLogger(__name__)

# 매출세액 계정과목 키워드
_OUTPUT_TAX_KEYWORDS = ("매출세액", "output_tax", "부가세예수금")
# 매입세액 계정과목 키워드
_INPUT_TAX_KEYWORDS = ("매입세액", "input_tax", "부가세대급금")
# 원화 절사 단위
_KRW_QUANT = Decimal(1)

# BR-KTAX-004: 부가세 신고 기간 분류
_VAT_PERIODS = {
    (1, 3): "1기 예정",
    (4, 6): "1기 확정",
    (7, 9): "2기 예정",
    (10, 12): "2기 확정",
}


def classify_vat_period(period_start: date) -> str:
    """BR-KTAX-004: 부가세 신고 기간을 분류한다.

    부가가치세법 제48~49조에 따라 분기별 예정/확정으로 분류.
    """
    month = period_start.month
    for (start_month, end_month), label in _VAT_PERIODS.items():
        if start_month <= month <= end_month:
            return f"{period_start.year}년 {label}"
    return f"{period_start.year}년"


class VATService:
    """부가세 신고 자동 계산 서비스.

    기간 내 제출된(submitted) 분개전표를 집계하여
    매출세액/매입세액/납부세액을 Decimal로 산출하고 VATReturn 문서를 생성한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._journal_repo = Repository("journal_entries", tenant_id)
        self._vat_repo = Repository("vat_returns", tenant_id)

    def calculate_vat(self, period_start: date, period_end: date) -> dict[str, Any]:
        """BR-KTAX-005: 기간 내 분개전표를 집계하여 부가세를 산출한다.

        계정과목 규칙:
        - "매출세액"/"output_tax"/"부가세예수금" 계정의 credit 합계 = output_tax
        - "매입세액"/"input_tax"/"부가세대급금" 계정의 debit 합계 = input_tax
        - net_tax = output_tax - input_tax (원 단위 절사)

        Returns:
            {"output_tax": Decimal, "input_tax": Decimal, "net_tax": Decimal, "journal_count": int}
        """
        start_dt = datetime(period_start.year, period_start.month, period_start.day, tzinfo=UTC)
        end_dt = datetime(period_end.year, period_end.month, period_end.day, 23, 59, 59, tzinfo=UTC)

        query = {
            "posting_date": {"$gte": start_dt, "$lte": end_dt},
            "docstatus": DocStatus.SUBMITTED,
        }
        journals = self._journal_repo.find_many(query, limit=10000)
        logger.info(
            "부가세 계산: %s ~ %s 기간 전표 %d건 조회", period_start, period_end, len(journals)
        )

        output_tax = Decimal(0)
        input_tax = Decimal(0)

        for journal in journals:
            items = journal.get("items", [])
            for item in items:
                account = item.get("account", "")
                account_lower = account.lower()

                if any(kw in account_lower for kw in _OUTPUT_TAX_KEYWORDS):
                    output_tax += Decimal(str(item.get("credit", 0)))

                if any(kw in account_lower for kw in _INPUT_TAX_KEYWORDS):
                    input_tax += Decimal(str(item.get("debit", 0)))

        # BR-KTAX-005: 원 단위 절사 (부가세법 시행령)
        net_tax = (output_tax - input_tax).quantize(_KRW_QUANT, rounding=ROUND_DOWN)

        return {
            "output_tax": output_tax.quantize(_KRW_QUANT, rounding=ROUND_DOWN),
            "input_tax": input_tax.quantize(_KRW_QUANT, rounding=ROUND_DOWN),
            "net_tax": net_tax,
            "journal_count": len(journals),
        }

    def create_vat_return(self, period_start: date, period_end: date) -> str:
        """부가세 신고서를 자동 생성한다.

        BR-KTAX-004: 기간 분류 자동 적용.
        중복 신고서 검증 (ERR-KTAX-020).
        """
        period_label = f"{period_start.isoformat()}~{period_end.isoformat()}"

        # 중복 검증
        existing = self._vat_repo.find_many({"period": period_label}, limit=1)
        if existing:
            raise_unprocessable(
                "ERR-KTAX-020",
                f"해당 기간의 부가세 신고서가 이미 존재합니다: {period_label}",
            )

        result = self.calculate_vat(period_start, period_end)
        vat_period = classify_vat_period(period_start)

        vat_return = VATReturn(
            period=period_label,
            tax_amount=result["net_tax"],
            output_tax=result["output_tax"],
            input_tax=result["input_tax"],
            net_tax=result["net_tax"],
            status="draft",
        )

        doc_id = self._vat_repo.insert(vat_return)
        logger.info("부가세 신고서 생성: %s (기간: %s, 분류: %s)", doc_id, period_label, vat_period)
        return doc_id

    def get_tax_summary(self, period: str) -> dict[str, Any]:
        """기간별 세액 요약을 조회한다."""
        docs = self._vat_repo.find_many({"period": period}, limit=1)

        if not docs:
            return {
                "period": period,
                "output_tax": Decimal(0),
                "input_tax": Decimal(0),
                "net_tax": Decimal(0),
                "status": "not_found",
                "doc_id": None,
            }

        doc = docs[0]
        return {
            "period": doc.get("period", ""),
            "output_tax": Decimal(str(doc.get("output_tax", 0))),
            "input_tax": Decimal(str(doc.get("input_tax", 0))),
            "net_tax": Decimal(str(doc.get("net_tax", 0))),
            "status": doc.get("status", "draft"),
            "doc_id": str(doc.get("_id", "")),
        }
