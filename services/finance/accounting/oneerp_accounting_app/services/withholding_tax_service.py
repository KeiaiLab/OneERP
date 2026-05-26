"""원천징수 서비스 — 한국 세법 기반 사업/기타/이자/배당 소득 원천징수.

근거 법령 (2026년 4월 기준):
- 소득세법 제127조 (원천징수의무)
- 소득세법 제129조 (사업소득 원천징수 3%)
- 소득세법 제145조 (기타소득 원천징수 20%)
- 소득세법 제155조의2 (이자·배당소득 14%)
- 지방세법 제103조의13 (지방소득세 = 소득세의 10%)
- 국세기본법 제47조의2 (10원 미만 절사)

L2 비즈니스 룰 신규 등록 후보:
- BR-WHT-001: 사업소득 원천세 = 지급액 x 3.3% (소득세 3% + 지방세 0.3%)
- BR-WHT-002: 기타소득 원천세 = (지급액 - 필요경비) x 22% (소득세 20% + 지방세 2%)
  - 필요경비 기본 60% (강연료, 사례금 등)
- BR-WHT-003: 이자/배당소득 원천세 = 지급액 x 15.4% (소득세 14% + 지방세 1.4%)
- BR-WHT-004: 기타소득 과세표준 5만원 이하는 비과세 (소득세법 시행령 제200조)
- BR-WHT-005: 모든 원천세는 10원 미만 절사 (국세기본법 제47조의2)

설계 메모:
- 모든 금액 계산은 Decimal 사용 (float 절대 금지).
- 10원 미만 절사는 round_down(amount, -1).
- 분개 자동 생성 시 차변 = 비용 계정, 대변 = 예수금-소득세, 예수금-지방세, 현금/예금.
- 원천징수영수증 발급 (지급명세서) 연동은 후속 작업 예정.
"""

from __future__ import annotations

import logging
from decimal import ROUND_DOWN, Decimal
from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_accounting_app.models.journal_entry import JournalEntry, JournalEntryItem

logger = logging.getLogger(__name__)

# 소득세 세율 (소득세법 제129·145·155조)
INCOME_TAX_RATES: dict[str, Decimal] = {
    "business": Decimal("0.03"),  # 사업소득 3%
    "other": Decimal("0.20"),  # 기타소득 20% (과세표준 기준)
    "interest": Decimal("0.14"),  # 이자소득 14%
    "dividend": Decimal("0.14"),  # 배당소득 14%
}

# 지방소득세 = 소득세 x 10% (지방세법 제103조의13)
LOCAL_TAX_MULTIPLIER = Decimal("0.1")

# 기타소득 기본 필요경비율 (강연료·사례금·원고료 등)
DEFAULT_NECESSARY_EXPENSE_RATE = Decimal("0.60")

# 기타소득 비과세 한도 (과세표준 기준, 소득세법 시행령 제200조)
OTHER_INCOME_TAX_FREE_THRESHOLD = Decimal(50000)

# 절사 단위 (10원)
_ROUND_UNIT = Decimal(10)


def _round_down_10won(value: Decimal) -> Decimal:
    """10원 미만을 버린다 (국세기본법 제47조의2)."""
    return (value / _ROUND_UNIT).quantize(Decimal(1), rounding=ROUND_DOWN) * _ROUND_UNIT


def _to_decimal(value: Any) -> Decimal:
    """다양한 입력을 Decimal로 안전하게 변환한다."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _calculate_local_tax(income_tax: Decimal) -> Decimal:
    """지방소득세를 계산한다 (소득세 x 10%, 10원 미만 절사)."""
    return _round_down_10won(income_tax * LOCAL_TAX_MULTIPLIER)


def _validate_payment_amount(payment_amount: Decimal) -> None:
    """지급액 사전 검증."""
    if payment_amount < 0:
        msg = "지급액은 0 이상이어야 합니다"
        raise ValueError(msg)


class WithholdingTaxService:
    """원천징수 비즈니스 로직.

    한국 소득세법에 따라 사업/기타/이자/배당 소득 지급 시 원천징수 세액을 계산하고,
    선택적으로 자동 분개전표를 생성한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._je_repo = Repository("journal_entries", tenant_id=tenant_id)

    def calculate_business_income(self, payment_amount: Decimal) -> dict[str, Any]:
        """BR-WHT-001: 사업소득 원천세 계산 (3.3%).

        Args:
            payment_amount: 총 지급액 (소득세 + 지방세 + 실수령액의 합)

        Returns:
            {"income_tax": Decimal, "local_income_tax": Decimal,
             "total_withholding": Decimal, "net_payment": Decimal, "income_type": "business"}
        """
        amount = _to_decimal(payment_amount)
        _validate_payment_amount(amount)

        # 소득세 = 지급액 x 3% (10원 미만 절사)
        income_tax = _round_down_10won(amount * INCOME_TAX_RATES["business"])
        local_income_tax = _calculate_local_tax(income_tax)
        total_withholding = income_tax + local_income_tax
        net_payment = amount - total_withholding

        return {
            "income_type": "business",
            "payment_amount": amount,
            "income_tax": income_tax,
            "local_income_tax": local_income_tax,
            "total_withholding": total_withholding,
            "net_payment": net_payment,
        }

    def calculate_other_income(
        self,
        payment_amount: Decimal,
        necessary_expense_rate: Decimal | None = None,
    ) -> dict[str, Any]:
        """BR-WHT-002: 기타소득 원천세 계산.

        과세표준 = 지급액 - (지급액 x 필요경비율).
        과세표준이 50,000원 이하이면 비과세 (BR-WHT-004).

        Args:
            payment_amount: 총 지급액
            necessary_expense_rate: 필요경비율 (기본 60%)
        """
        amount = _to_decimal(payment_amount)
        _validate_payment_amount(amount)

        rate = (
            necessary_expense_rate
            if necessary_expense_rate is not None
            else DEFAULT_NECESSARY_EXPENSE_RATE
        )
        necessary_expense = amount * rate
        taxable_amount = amount - necessary_expense

        # BR-WHT-004: 과세표준 5만원 이하 비과세
        if taxable_amount <= OTHER_INCOME_TAX_FREE_THRESHOLD:
            return {
                "income_type": "other",
                "payment_amount": amount,
                "necessary_expense": necessary_expense,
                "taxable_amount": taxable_amount,
                "income_tax": Decimal(0),
                "local_income_tax": Decimal(0),
                "total_withholding": Decimal(0),
                "net_payment": amount,
                "is_tax_exempt": True,
                "exempt_reason": "기타소득 과세표준 5만원 이하 (소득세법 시행령 제200조)",
            }

        income_tax = _round_down_10won(taxable_amount * INCOME_TAX_RATES["other"])
        local_income_tax = _calculate_local_tax(income_tax)
        total_withholding = income_tax + local_income_tax

        return {
            "income_type": "other",
            "payment_amount": amount,
            "necessary_expense": necessary_expense,
            "taxable_amount": taxable_amount,
            "income_tax": income_tax,
            "local_income_tax": local_income_tax,
            "total_withholding": total_withholding,
            "net_payment": amount - total_withholding,
            "is_tax_exempt": False,
        }

    def calculate_interest_income(self, payment_amount: Decimal) -> dict[str, Any]:
        """BR-WHT-003: 이자소득 원천세 계산 (15.4%)."""
        return self._calculate_flat_rate_income(payment_amount, "interest")

    def calculate_dividend_income(self, payment_amount: Decimal) -> dict[str, Any]:
        """BR-WHT-003: 배당소득 원천세 계산 (15.4%)."""
        return self._calculate_flat_rate_income(payment_amount, "dividend")

    def calculate_withholding(
        self,
        payment_amount: Decimal,
        income_type: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """소득 유형별 원천세 계산 디스패처.

        Args:
            payment_amount: 총 지급액
            income_type: business/other/interest/dividend
            **kwargs: 유형별 추가 파라미터 (예: other의 necessary_expense_rate)

        Returns:
            계산 결과 딕셔너리
        """
        if income_type == "business":
            return self.calculate_business_income(payment_amount)
        if income_type == "other":
            return self.calculate_other_income(payment_amount, **kwargs)
        if income_type == "interest":
            return self.calculate_interest_income(payment_amount)
        if income_type == "dividend":
            return self.calculate_dividend_income(payment_amount)
        msg = f"지원하지 않는 소득 유형입니다: {income_type}"
        raise ValueError(msg)

    def create_withholding_journal(
        self,
        payment_amount: Decimal,
        income_type: str,
        expense_account: str,
        cash_account: str,
        party: str,
        posting_date: Any,
        **kwargs: Any,
    ) -> str:
        """원천징수 분개전표를 자동 생성한다.

        분개 형식 (사업소득 100만원 예시):
        - 차변: 지급수수료 1,000,000
        - 대변: 예수금-소득세 30,000
        - 대변: 예수금-지방소득세 3,000
        - 대변: 현금 967,000

        Returns:
            생성된 분개전표 ID
        """
        amount = _to_decimal(payment_amount)
        if amount <= 0:
            msg = "원천징수 분개의 지급액은 0보다 커야 합니다"
            raise ValueError(msg)

        calc = self.calculate_withholding(
            payment_amount=amount,
            income_type=income_type,
            **kwargs,
        )

        items: list[JournalEntryItem] = [
            JournalEntryItem(
                account=expense_account,
                account_type="expense",
                debit=amount,
                credit=Decimal(0),
            ),
        ]

        income_tax = calc["income_tax"]
        local_tax = calc["local_income_tax"]
        net_payment = calc["net_payment"]

        if income_tax > 0:
            items.append(
                JournalEntryItem(
                    account="예수금-소득세",
                    account_type="liability",
                    debit=Decimal(0),
                    credit=income_tax,
                )
            )
        if local_tax > 0:
            items.append(
                JournalEntryItem(
                    account="예수금-지방소득세",
                    account_type="liability",
                    debit=Decimal(0),
                    credit=local_tax,
                )
            )
        items.append(
            JournalEntryItem(
                account=cash_account,
                account_type="asset",
                debit=Decimal(0),
                credit=net_payment,
            )
        )

        je_id = generate_name("JE", tenant_id=self._tenant_id)
        je = JournalEntry(
            _id=je_id,
            posting_date=posting_date,
            voucher_type="withholding_tax",
            voucher_no=f"WHT-{party}",
            total_debit=amount,
            total_credit=amount,
            items=items,
            remark=f"{income_type} 소득 원천징수 ({party}, 총 {amount:,}원)",
            docstatus=DocStatus.SUBMITTED,
            tenant_id=self._tenant_id,
        )

        self._je_repo.insert(je)

        logger.info(
            "원천징수 분개 생성: %s (%s, 지급=%s, 원천세=%s)",
            je_id,
            income_type,
            amount,
            calc["total_withholding"],
        )

        return je_id

    # -- 내부 헬퍼 --

    def _calculate_flat_rate_income(
        self,
        payment_amount: Decimal,
        income_type: str,
    ) -> dict[str, Any]:
        """이자·배당 등 단일 세율 소득 계산 공통 로직."""
        amount = _to_decimal(payment_amount)
        _validate_payment_amount(amount)

        rate = INCOME_TAX_RATES[income_type]
        income_tax = _round_down_10won(amount * rate)
        local_income_tax = _calculate_local_tax(income_tax)
        total_withholding = income_tax + local_income_tax

        return {
            "income_type": income_type,
            "payment_amount": amount,
            "income_tax": income_tax,
            "local_income_tax": local_income_tax,
            "total_withholding": total_withholding,
            "net_payment": amount - total_withholding,
        }
