"""연말정산 계산 서비스.

근로소득공제, 6단계 누진세율, 세액공제를 적용하여
연말정산 결과(환급 또는 추가납부)를 산출한다.

세율 테이블은 상수로 정의하되, 향후 환경변수로 오버라이드 가능하다.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 세율 테이블 — 2026년 기준 (향후 환경변수 오버라이드 예정)
# ---------------------------------------------------------------------------

# 근로소득공제 구간 [(상한, 공제율)]
EARNED_INCOME_DEDUCTION_BRACKETS: list[tuple[float, float]] = [
    (5_000_000, 0.70),
    (15_000_000, 0.40),
    (45_000_000, 0.15),
    (100_000_000, 0.05),
    (float("inf"), 0.02),
]

# 과세표준 구간 [(상한, 세율)]
TAX_BRACKETS: list[tuple[float, float]] = [
    (14_000_000, 0.06),
    (50_000_000, 0.15),
    (88_000_000, 0.24),
    (150_000_000, 0.35),
    (300_000_000, 0.38),
    (500_000_000, 0.40),
    (1_000_000_000, 0.42),
    (float("inf"), 0.45),
]

# 근로소득 세액공제 한도 — 총급여 기준 [(상한, 한도)]
EARNED_INCOME_CREDIT_LIMITS: list[tuple[float, float]] = [
    (55_000_000, 740_000),
    (70_000_000, 660_000),
    (120_000_000, 500_000),
    (float("inf"), 200_000),
]


# ---------------------------------------------------------------------------
# 계산 결과 데이터 클래스
# ---------------------------------------------------------------------------


@dataclass
class YearEndSettlementResult:
    """연말정산 계산 결과."""

    total_income: float  # 총 급여
    earned_income_deduction: float  # 근로소득공제
    taxable_income: float  # 과세표준
    calculated_tax: float  # 산출세액
    earned_income_credit: float  # 근로소득 세액공제
    determined_tax: float  # 결정세액
    tax_paid: float  # 기납부세액
    settlement_amount: float  # 정산금액 (음수=환급, 양수=추가납부)


# ---------------------------------------------------------------------------
# 서비스 클래스
# ---------------------------------------------------------------------------


class YearEndSettlementService:
    """연말정산 계산 서비스.

    직원의 연간 급여명세(SalarySlip)를 집계하고,
    근로소득공제 → 과세표준 → 누진세율 → 세액공제를 적용하여
    최종 정산금액을 산출한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id

    # -----------------------------------------------------------------------
    # 근로소득공제
    # -----------------------------------------------------------------------

    def calculate_earned_income_deduction(self, total_income: float) -> float:
        """BR-PAY-009: 연말정산 근로소득공제 (5단계 누진).

        - 500만원 이하: 70%
        - 500~1500만원: 350만 + 초과분의 40%
        - 1500~4500만원: 750만 + 초과분의 15%
        - 4500~1억: 1200만 + 초과분의 5%
        - 1억 초과: 1475만 + 초과분의 2%
        """
        if total_income <= 0:
            return 0.0

        deduction = 0.0
        prev_upper = 0.0

        for upper, rate in EARNED_INCOME_DEDUCTION_BRACKETS:
            bracket_base = min(total_income, upper) - prev_upper
            if bracket_base <= 0:
                break
            deduction += bracket_base * rate
            prev_upper = upper

        return round(deduction)

    # -----------------------------------------------------------------------
    # 6단계 누진세율
    # -----------------------------------------------------------------------

    def calculate_tax_by_bracket(self, taxable_income: float) -> float:
        """BR-PAY-010: 연말정산 8단계 누진세율 적용.

        - 1400만 이하: 6%
        - 1400~5000만: 15%
        - 5000~8800만: 24%
        - 8800만~1.5억: 35%
        - 1.5억~3억: 38%
        - 3억~5억: 40%
        - 5억~10억: 42%
        - 10억 초과: 45%
        """
        if taxable_income <= 0:
            return 0.0

        tax = 0.0
        prev_upper = 0.0

        for upper, rate in TAX_BRACKETS:
            bracket_base = min(taxable_income, upper) - prev_upper
            if bracket_base <= 0:
                break
            tax += bracket_base * rate
            prev_upper = upper

        return round(tax)

    # -----------------------------------------------------------------------
    # 근로소득 세액공제
    # -----------------------------------------------------------------------

    def calculate_earned_income_credit(
        self,
        calculated_tax: float,
        total_income: float = 0.0,
    ) -> float:
        """BR-PAY-011: 연말정산 근로소득 세액공제.

        - 산출세액 130만원 이하: 산출세액 x 55%
        - 130만원 초과: 71.5만 + (초과분 x 30%)
        - 한도: 총급여 5500만 이하 74만, 7000만 이하 66만, 1.2억 이하 50만, 초과 20만
        """
        if calculated_tax <= 0:
            return 0.0

        # 세액공제 계산
        if calculated_tax <= 1_300_000:
            credit = calculated_tax * 0.55
        else:
            credit = 715_000 + (calculated_tax - 1_300_000) * 0.30

        # 한도 적용
        limit = 200_000  # 기본값
        for upper, cap in EARNED_INCOME_CREDIT_LIMITS:
            if total_income <= upper:
                limit = cap
                break

        return round(min(credit, limit))

    # -----------------------------------------------------------------------
    # 전체 계산
    # -----------------------------------------------------------------------

    def calculate(
        self,
        total_income: float,
        tax_paid: float = 0.0,
    ) -> YearEndSettlementResult:
        """BR-PAY-012: 연말정산 정산금액 산출.

        정산 = 결정세액 - 기납부세액 (음수=환급, 양수=추가납부)

        Args:
            total_income: 연간 총 급여
            tax_paid: 기납부세액 (원천징수 등)

        Returns:
            YearEndSettlementResult: 연말정산 계산 결과

        프로세스 (BR-PAY-009 → 010 → 011 → 012):
            1. 근로소득공제(BR-PAY-009) → 과세표준
            2. 8단계 누진세율(BR-PAY-010) → 산출세액
            3. 세액공제(BR-PAY-011) → 결정세액
            4. 기납부세액 차감(BR-PAY-012) → 정산금액
        """
        if total_income <= 0:
            logger.info(
                "연말정산: tenant=%s, 소득 0원 → 정산 0원",
                self.tenant_id,
            )
            return YearEndSettlementResult(
                total_income=0.0,
                earned_income_deduction=0.0,
                taxable_income=0.0,
                calculated_tax=0.0,
                earned_income_credit=0.0,
                determined_tax=0.0,
                tax_paid=tax_paid,
                settlement_amount=-tax_paid,
            )

        # 1. 근로소득공제 → 과세표준
        earned_income_deduction = self.calculate_earned_income_deduction(total_income)
        taxable_income = max(total_income - earned_income_deduction, 0.0)

        # 2. 6단계 누진세율 → 산출세액
        calculated_tax = self.calculate_tax_by_bracket(taxable_income)

        # 3. 세액공제 적용 → 결정세액
        earned_income_credit = self.calculate_earned_income_credit(calculated_tax, total_income)
        determined_tax = max(calculated_tax - earned_income_credit, 0.0)

        # 4. 기납부세액 차감 → 정산금액
        settlement_amount = round(determined_tax - tax_paid)

        logger.info(
            "연말정산 완료: tenant=%s, total_income=%s, "
            "taxable_income=%s, calculated_tax=%s, "
            "determined_tax=%s, settlement=%s",
            self.tenant_id,
            total_income,
            taxable_income,
            calculated_tax,
            determined_tax,
            settlement_amount,
        )

        return YearEndSettlementResult(
            total_income=total_income,
            earned_income_deduction=earned_income_deduction,
            taxable_income=taxable_income,
            calculated_tax=calculated_tax,
            earned_income_credit=earned_income_credit,
            determined_tax=determined_tax,
            tax_paid=tax_paid,
            settlement_amount=settlement_amount,
        )
